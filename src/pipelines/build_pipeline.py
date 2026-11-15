"""Build the individual-hotspot SQLite store and sensor-wise aggregates from NASA FIRMS ZIP.

Usage:
  python src/pipelines/build_pipeline.py --input data/raw/data.zip --output data/processed/data-engineering

A row is one satellite-detected thermal pixel, NOT one wildfire or ignition.
Only FIRMS type=0 (presumed vegetation fire) is retained in the product tables.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sqlite3
import zipfile
from datetime import date
from pathlib import Path

COLUMNS = """
id INTEGER PRIMARY KEY,
sensor TEXT NOT NULL, satellite TEXT,
date_utc TEXT NOT NULL, time_utc TEXT, timestamp_utc TEXT,
year INTEGER NOT NULL, month INTEGER NOT NULL,
latitude REAL NOT NULL, longitude REAL NOT NULL,
frp_mw REAL NOT NULL, daynight TEXT, confidence_modis_pct REAL,
confidence_viirs_label TEXT,
grid_x INTEGER NOT NULL, grid_y INTEGER NOT NULL
"""

def sensor_from_name(name: str) -> str:
    name = name.upper().replace("-", "_").replace(" ", "_")
    if "MODIS" in name:
        return "MODIS"
    if "NOAA" in name or "J1" in name or "JPS" in name:
        return "VIIRS_NOAA20"
    if "SNPP" in name or "S_NPP" in name or "SUOMI" in name:
        return "VIIRS_SNPP"
    raise ValueError(f"Unknown sensor family in source filename: {name}")

def source_members(z: zipfile.ZipFile):
    return sorted(x for x in z.namelist()
                  if not x.endswith("/")
                  and x.lower().endswith(".csv")
                  and "indonesia" in x.lower()
                  and "angola" not in x.lower())

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def normalize(row: dict, sensor: str):
    if str(row.get("type", "")).strip() != "0":
        return None
    lat = float(row["latitude"])
    lon = float(row["longitude"])
    frp = float(row["frp"])
    if not (math.isfinite(lat) and math.isfinite(lon) and math.isfinite(frp)):
        raise ValueError("Nonfinite latitude/longitude/FRP")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180 and frp >= 0):
        raise ValueError("Invalid coordinate or negative FRP")
    observed = date.fromisoformat(row["acq_date"].strip())
    if not 2000 <= observed.year <= 2025:
        raise ValueError("Unexpected observation year")
    time = re.sub(r"[^0-9]", "", str(row.get("acq_time", ""))).zfill(4)
    if len(time) != 4 or int(time[:2]) > 23 or int(time[2:]) > 59:
        raise ValueError("Invalid acquisition time")
    dt = f"{observed.isoformat()}T{time[:2]}:{time[2:]}:00Z"
    c = str(row.get("confidence", "")).strip()
    modis_conf, viirs_conf = None, None
    if sensor == "MODIS":
        if c:
            modis_conf = float(c)
            if not 0 <= modis_conf <= 100:
                raise ValueError("Invalid MODIS confidence percent")
    elif c:
        viirs_conf = c.lower()
        if viirs_conf not in ("l", "n", "h"):
            raise ValueError("Invalid VIIRS confidence class")
    return (sensor, row.get("satellite", ""), observed.isoformat(),
            time, dt, observed.year, observed.month, lat, lon, frp,
            row.get("daynight", "").strip().upper() or None,
            modis_conf, viirs_conf,
            math.floor((lon + 180) / 0.25), math.floor((lat + 90) / 0.25))

def write_aggregate(conn, dest: Path, filename: str, dimensions: list[str]):
    dim = ", ".join(dimensions)
    sql = (f"SELECT {dim}, COUNT(*) AS detection_count, "
           f"ROUND(SUM(frp_mw), 4) AS frp_sum_mw "
           f"FROM hotspots GROUP BY {dim} ORDER BY {dim}")
    names = dimensions + ["detection_count", "frp_sum_mw"]
    with (dest / filename).open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(names)
        w.writerows(conn.execute(sql))

def build(input_zip: Path, output: Path):
    if not input_zip.is_file():
        raise FileNotFoundError(input_zip)
    output.mkdir(parents=True, exist_ok=True)
    db = output / "vestigium_hotspots.sqlite"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.execute("PRAGMA journal_mode=DELETE")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute(f"CREATE TABLE hotspots ({COLUMNS})")
    con.execute("""CREATE TABLE source_files(
        filename TEXT, sensor TEXT, nominal_year INTEGER,
        source_rows INTEGER, accepted_type0 INTEGER,
        excluded_non_vegetation INTEGER, rejected_invalid INTEGER,
        first_date_utc TEXT, last_date_utc TEXT)""")
    sql = """INSERT INTO hotspots (
        sensor,satellite,date_utc,time_utc,timestamp_utc,year,month,
        latitude,longitude,frp_mw,daynight,confidence_modis_pct,confidence_viirs_label,
        grid_x,grid_y) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    accepted = excluded = invalid = source_count = 0
    by_sensor: dict[str,int] = {}
    with zipfile.ZipFile(input_zip) as z:
        names = source_members(z)
        if not names:
            raise ValueError("No Indonesia FIRMS CSV files found in ZIP")
        for name in names:
            family = sensor_from_name(name)
            file_rows = file_ok = file_excluded = file_invalid = 0
            min_date = max_date = None
            buffer = []
            with z.open(name) as stream:
                reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))
                for row in reader:
                    file_rows += 1
                    if str(row.get("type", "")).strip() != "0":
                        file_excluded += 1
                        continue
                    try:
                        value = normalize(row, family)
                    except (ValueError, TypeError, KeyError, OverflowError):
                        file_invalid += 1
                        continue
                    if value is None:
                        file_excluded += 1
                        continue
                    buffer.append(value)
                    file_ok += 1
                    d = value[2]
                    min_date = d if min_date is None else min(min_date, d)
                    max_date = d if max_date is None else max(max_date, d)
                    if len(buffer) == 20_000:
                        con.executemany(sql, buffer)
                        buffer.clear()
                if buffer:
                    con.executemany(sql, buffer)
            m = re.search(r"(20\d{2})", Path(name).name)
            nominal_year = int(m.group(1)) if m else None
            con.execute("INSERT INTO source_files VALUES (?,?,?,?,?,?,?,?,?)",
                (name, family, nominal_year, file_rows, file_ok, file_excluded,
                 file_invalid, min_date, max_date))
            con.commit()
            accepted += file_ok
            excluded += file_excluded
            invalid += file_invalid
            source_count += file_rows
            by_sensor[family] = by_sensor.get(family, 0) + file_ok
            print(f"{name}: accepted={file_ok:,} excluded={file_excluded:,} invalid={file_invalid:,}", flush=True)
    con.executescript("""
    CREATE INDEX idx_hotspot_time ON hotspots(year,month,date_utc);
    CREATE INDEX idx_hotspot_bbox ON hotspots(longitude,latitude);
    CREATE INDEX idx_hotspot_sensor_time ON hotspots(sensor,year,month);
    CREATE INDEX idx_hotspot_grid ON hotspots(grid_x,grid_y,year,month);
    """)
    con.commit()
    summary = [
        ("daily_sensor.csv", ["date_utc","sensor"]),
        ("monthly_sensor.csv", ["year","month","sensor"]),
        ("annual_sensor.csv", ["year","sensor"]),
        ("monthly_grid.csv", ["year","month","sensor","grid_x","grid_y"]),
        ("annual_grid.csv", ["year","sensor","grid_x","grid_y"]),
    ]
    # Grid center is added to CSV in a separate streaming pass for map convenience.
    for filename, dims in summary:
        write_aggregate(con, output, filename, dims)
    for filename in ("monthly_grid.csv", "annual_grid.csv"):
        file = output / filename
        tmp = output / (filename + ".tmp")
        with file.open(newline="", encoding="utf-8") as inp, tmp.open("w", newline="", encoding="utf-8") as out:
            rd = csv.DictReader(inp)
            w = csv.DictWriter(out, fieldnames=rd.fieldnames + ["grid_center_lon","grid_center_lat"])
            w.writeheader()
            for r in rd:
                r["grid_center_lon"] = round(-180 + (int(r["grid_x"]) + 0.5) * 0.25, 5)
                r["grid_center_lat"] = round(-90 + (int(r["grid_y"]) + 0.5) * 0.25, 5)
                w.writerow(r)
        tmp.replace(file)
    found = con.execute("SELECT COUNT(*) FROM hotspots").fetchone()[0]
    assert found == accepted, (found, accepted)
    for filename, _ in summary:
        with (output / filename).open(newline="", encoding="utf-8") as f:
            actual = sum(int(r["detection_count"]) for r in csv.DictReader(f))
        assert actual == accepted, (filename, actual, accepted)
    qa = dict(input_archive=str(input_zip), input_sha256=sha256(input_zip),
              source_rows=source_count, accepted_presumed_vegetation_detections=accepted,
              excluded_non_vegetation_detections=excluded, rejected_invalid_rows=invalid,
              source_files=len(names), by_sensor=by_sensor,
              integrity=con.execute("PRAGMA integrity_check").fetchone()[0],
              observation_unit="satellite_thermal_pixel_detection_not_fire_event",
              all_timestamps_utc=True, grid_resolution_degrees=0.25)
    assert qa["integrity"] == "ok"
    (output / "quality_report.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    con.close()
    print(json.dumps({k:qa[k] for k in ("source_files","accepted_presumed_vegetation_detections","integrity")}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.input, args.output)
