"""Publish sampled authentic NASA FIRMS points and exact monthly totals, without SQLite."""
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app/api/data"
CAP = 360
SOURCES = [("MODIS", "data/MODIS"), ("VIIRS_SNPP", "data/viirs-snpp"), ("VIIRS_NOAA20", "data/viirs-jpss1")]

def run():
    sample = defaultdict(list)
    count = defaultdict(int)
    rngs = {}
    source_files = 0
    for sensor, folder in SOURCES:
        paths = sorted((ROOT / folder).glob("*.csv"))
        if not paths:
            raise FileNotFoundError(folder)
        for path in paths:
            source_files += 1
            with path.open(encoding="utf-8-sig", newline="") as stream:
                for line, row in enumerate(csv.DictReader(stream), start=2):
                    if str(row.get("type", "")).strip() != "0":
                        continue
                    lat, lon, frp = float(row["latitude"]), float(row["longitude"]), float(row["frp"])
                    if not (math.isfinite(lat) and math.isfinite(lon) and math.isfinite(frp) and
                            -90 <= lat <= 90 and -180 <= lon <= 180 and frp >= 0):
                        raise ValueError(f"Invalid coordinates/FRP: {path}:{line}")
                    date = row["acq_date"].strip()
                    year, month = (int(v) for v in date.split("-")[:2])
                    if not (2000 <= year <= 2025 and 1 <= month <= 12):
                        raise ValueError("Invalid source date")
                    key = (year, month, sensor)
                    count[key] += 1
                    n = count[key]
                    if key not in rngs:
                        seed = int.from_bytes(hashlib.sha256(str(key).encode()).digest()[:8], "big")
                        rngs[key] = random.Random(seed)
                    idx = n - 1 if n <= CAP else rngs[key].randrange(n)
                    if idx >= CAP:
                        continue
                    utc = row.get("acq_time", "0000").strip().zfill(4)
                    if len(utc) != 4 or not utc.isdigit():
                        raise ValueError(f"Invalid UTC time: {path}:{line}")
                    confidence = row.get("confidence", "").strip()
                    record = {
                        "id": f"{sensor}-{path.stem}-{line}", "latitude": round(lat, 5),
                        "longitude": round(lon, 5), "timestamp_utc": f"{date}T{utc[:2]}:{utc[2:]}:00Z",
                        "date_utc": date, "sensor": sensor, "satellite": row.get("satellite", ""),
                        "frp_mw": frp,
                        "confidence_modis_pct": float(confidence) if confidence and sensor == "MODIS" else None,
                        "confidence_viirs_label": confidence.lower() if confidence and sensor != "MODIS" else None,
                        "synthetic": False,
                    }
                    group = sample[key]
                    if idx == len(group):
                        group.append(record)
                    else:
                        group[idx] = record
            print("Read", path.name, flush=True)
    baseline = json.loads((ROOT / "data/validation_result.json").read_text())
    total = sum(count.values())
    if total != baseline["rows"] or source_files != 48:
        raise ValueError(f"Integrity mismatch: {total}, {source_files}")
    for sensor, expected in baseline["by_sensor"].items():
        if sum(n for (year, month, s), n in count.items() if s == sensor) != expected:
            raise ValueError("Sensor validation failed: " + sensor)
    (OUT / "samples").mkdir(parents=True, exist_ok=True)
    for year in range(2000, 2026):
        records = {}
        for month in range(1, 13):
            records[str(month)] = [record for s in ("MODIS", "VIIRS_SNPP", "VIIRS_NOAA20") for record in sample.get((year, month, s), [])]
        (OUT / "samples" / f"{year}.json").write_text(json.dumps(records, separators=(",", ":")))
    summary = {
        "source": "NASA FIRMS Indonesia type=0",
        "source_total": total, "source_files": source_files, "cap_per_sensor_month": CAP,
        "map_points_sampled": sum(len(v) for v in sample.values()),
        "months": [{"year":y, "month":m, "sensor":s, "detection_count":n} for (y,m,s),n in sorted(count.items())]
    }
    (OUT / "monthly_index.json").write_text(json.dumps(summary, separators=(",", ":")))
    (OUT / "quality_report.json").write_text((ROOT / "data/quality_report.json").read_text())
    print("COMPLETE", total, "source pixels,", summary["map_points_sampled"], "real map coordinates", flush=True)

if __name__ == "__main__":
    run()
