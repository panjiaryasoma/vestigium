#!/usr/bin/env python3
"""VESTIGIUM | Reproducible geospatial ETL for NASA FIRMS CSV archives.

Standard-library-only ETL, intentionally sensor-aware and audit-friendly.
Designed for the 2000–2025 Indonesian MODIS / VIIRS source archive.

Input: data.zip (original CSVs, read without extracting)
Output: SQLite geospatial detections + aggregated CSV summaries + QA JSON

IMPORTANT: This transforms detection records, not verified wildfire events.
No sensor harmonization or inference about ignition causes occurs here.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
import sqlite3
import sys
import time
import zipfile

GRID_DEG = 0.25
LAT_ORIGIN, LON_ORIGIN = -12.0, 94.0
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -12.0, 8.0, 94.0, 142.0
CSV_FIELDS = ["latitude", "longitude", "scan", "track", "acq_date", "acq_time",
              "satellite", "instrument", "confidence", "version", "frp", "daynight", "type"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS source_files (
 id INTEGER PRIMARY KEY, filename TEXT UNIQUE NOT NULL, sensor TEXT NOT NULL,
 nominal_year INTEGER NOT NULL, archive_bytes INTEGER NOT NULL,
 source_rows INTEGER DEFAULT 0, accepted_type0 INTEGER DEFAULT 0,
 excluded_non_vegetation INTEGER DEFAULT 0, rejected_invalid INTEGER DEFAULT 0,
 first_date_utc TEXT, last_date_utc TEXT, file_sha256 TEXT,
 error_counts_json TEXT
);
CREATE TABLE IF NOT EXISTS hotspots (
 id INTEGER PRIMARY KEY,
 sensor TEXT NOT NULL, satellite TEXT NOT NULL,
 date_utc TEXT NOT NULL, time_utc TEXT NOT NULL,
 timestamp_utc TEXT NOT NULL, year INTEGER NOT NULL, month INTEGER NOT NULL,
 latitude REAL NOT NULL, longitude REAL NOT NULL,
 grid_x INTEGER NOT NULL, grid_y INTEGER NOT NULL,
 frp_mw REAL NOT NULL, confidence_modis_pct INTEGER,
 confidence_viirs_label TEXT,
 scan_km REAL, track_km REAL,
 brightness_primary_k REAL, brightness_secondary_k REAL,
 daynight TEXT, version TEXT, source_file_id INTEGER NOT NULL,
 FOREIGN KEY (source_file_id) REFERENCES source_files(id)
);
CREATE TABLE IF NOT EXISTS pipeline_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def sensor_from_path(filename: str):
    lo = filename.lower()
    if not lo.endswith('.csv') or not lo.endswith('_indonesia.csv'):
        return None
    if 'viirs-snpp/' in lo:
        return 'VIIRS_SNPP'
    if 'viirs-jpss1/' in lo:
        return 'VIIRS_NOAA20'
    if 'modis/' in lo:
        return 'MODIS'
    return None


def nominal_year_from_name(filename):
    import re
    m = re.search(r'_(20\d{2})_Indonesia\.csv$', filename, re.I)
    if not m:
        raise ValueError(f'Cannot parse year: {filename}')
    return int(m.group(1))


def finite_float(value: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise ValueError('nonfinite')
    return x


def optional_float(value: str):
    try:
        return finite_float(value)
    except (TypeError, ValueError):
        return None


def parse_detection(row, sensor, file_year, source_file_id):
    """Return (tuple, reason); type!=0 rows are explicitly excluded, not rejected."""
    try:
        fire_type = int(row['type'])
    except (KeyError, TypeError, ValueError):
        return None, 'invalid_type'
    if fire_type != 0:
        return None, 'non_vegetation_type'
    try:
        lat, lon = finite_float(row['latitude']), finite_float(row['longitude'])
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            return None, 'outside_coarse_indonesia_bbox'
        date_str = row['acq_date'].strip()
        d = dt.date.fromisoformat(date_str)
        if d.year != file_year:
            return None, 'date_year_mismatch'
        tm = row['acq_time'].strip().zfill(4)
        if len(tm) != 4 or not tm.isdigit():
            return None, 'bad_time'
        hh, mm = int(tm[:2]), int(tm[2:])
        if hh > 23 or mm > 59:
            return None, 'bad_time'
        frp = finite_float(row['frp'])
        if frp < 0:
            return None, 'invalid_frp'
        conf_modis, conf_viirs = None, None
        c = str(row['confidence']).strip()
        if sensor == 'MODIS':
            score = finite_float(c)
            if score < 0 or score > 100:
                return None, 'invalid_modis_confidence'
            conf_modis = round(score, 2)
        else:
            if c.lower() not in ('l', 'n', 'h'):
                return None, 'invalid_viirs_confidence'
            conf_viirs = c.lower()
        sx = int(math.floor((lon - LON_ORIGIN) / GRID_DEG))
        sy = int(math.floor((lat - LAT_ORIGIN) / GRID_DEG))
        dn = str(row.get('daynight', '')).strip().upper()
        if dn not in ('D','N'):
            return None, 'invalid_daynight'
        sat = row['satellite'].strip()
        if not sat:
            return None, 'missing_satellite'
        v = row['version'].strip()
        bright_primary = optional_float(row.get('brightness') or row.get('bright_ti4'))
        bright_secondary = optional_float(row.get('bright_t31') or row.get('bright_ti5'))
        data = (sensor, sat, date_str, tm, f'{date_str}T{tm[:2]}:{tm[2:]}:00Z',
                d.year, d.month, lat, lon, sx, sy, frp, conf_modis, conf_viirs,
                optional_float(row.get('scan')), optional_float(row.get('track')),
                bright_primary, bright_secondary, dn, v, source_file_id)
        return data, None
    except (ValueError, TypeError, KeyError, OverflowError):
        return None, 'malformed_required_field'


def add_metadata(conn, key, value):
    conn.execute('INSERT OR REPLACE INTO pipeline_metadata(key,value) VALUES (?,?)', (key, str(value)))


def write_sql_csv(conn, sql, params, dest, extra_columns=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    cur = conn.execute(sql, params)
    hdr = [c[0] for c in cur.description]
    with dest.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(hdr + (extra_columns or []))
        count = 0
        while True:
            rows = cur.fetchmany(10000)
            if not rows:
                break
            for row in rows:
                if extra_columns:
                    gx, gy = row[-5:-3]
                    writer.writerow(list(row) + [round(LON_ORIGIN+(gx+0.5)*GRID_DEG,5),
                                                   round(LAT_ORIGIN+(gy+0.5)*GRID_DEG,5)])
                else:
                    writer.writerow(row)
                count += 1
    return count


def build(src_zip: Path, out_dir: Path, max_files=None, max_rows_per_file=None, skip_spatial=False):
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    dbpath = out_dir / 'vestigium_hotspots.sqlite'
    if dbpath.exists():
        dbpath.unlink()
    sha = hashlib.sha256()
    with src_zip.open('rb') as h:
        for part in iter(lambda: h.read(1024*1024), b''):
            sha.update(part)
    archive_sha = sha.hexdigest()
    conn = sqlite3.connect(dbpath)
    conn.execute('PRAGMA journal_mode=OFF')
    conn.execute('PRAGMA synchronous=OFF')
    conn.execute('PRAGMA temp_store=MEMORY')
    conn.execute('PRAGMA cache_size=-128000')
    conn.executescript(SCHEMA)
    insert_sql = """INSERT INTO hotspots (
     sensor,satellite,date_utc,time_utc,timestamp_utc,year,month,latitude,longitude,
     grid_x,grid_y,frp_mw,confidence_modis_pct,confidence_viirs_label,
     scan_km,track_km,brightness_primary_k,brightness_secondary_k,daynight,version,source_file_id)
     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
    total_source = total_accepted = total_nonveg = total_rejected = 0
    reports = []
    with zipfile.ZipFile(src_zip) as zip_obj:
        members = [(a, sensor_from_path(a.filename)) for a in zip_obj.infolist()]
        members = [(a, sensor) for a, sensor in members if sensor is not None]
        members.sort(key=lambda a: (a[1], a[0].filename))
        if max_files is not None:
            members = members[:max_files]
        for idx,(file, sensor) in enumerate(members, 1):
            file_year = nominal_year_from_name(file.filename)
            cur = conn.execute('INSERT INTO source_files(filename,sensor,nominal_year,archive_bytes) VALUES (?,?,?,?)',
                               (file.filename,sensor,file_year,file.file_size))
            source_id = cur.lastrowid
            rejected = Counter(); count=accepted=nonveg=bad=0; buf=[]; first=None; last=None
            hash_csv = hashlib.sha256()
            # zipfile read bytes for CSV fingerprinting, then rewind by reopening stream.
            with zip_obj.open(file) as raw:
                for part in iter(lambda: raw.read(1024*1024), b''):
                    hash_csv.update(part)
            with zip_obj.open(file) as raw:
                import io
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding='utf-8-sig', newline=''))
                missing = set(CSV_FIELDS) - set(reader.fieldnames or [])
                if missing:
                    raise ValueError(f'{file.filename}: missing columns {sorted(missing)}')
                for row in reader:
                    count += 1
                    parsed, reason = parse_detection(row, sensor, file_year, source_id)
                    if reason == 'non_vegetation_type':
                        nonveg += 1
                    elif reason:
                        bad += 1; rejected[reason] += 1
                    else:
                        buf.append(parsed); accepted += 1
                        d = parsed[2]
                        first = min(first, d) if first else d
                        last = max(last, d) if last else d
                        if len(buf) == 15000:
                            conn.executemany(insert_sql, buf); buf=[]
                    if max_rows_per_file and count >= max_rows_per_file:
                        break
                if buf:
                    conn.executemany(insert_sql, buf)
            conn.execute('''UPDATE source_files SET source_rows=?,accepted_type0=?,excluded_non_vegetation=?,
                 rejected_invalid=?,first_date_utc=?,last_date_utc=?,file_sha256=?,error_counts_json=? WHERE id=?''',
                 (count,accepted,nonveg,bad,first,last,hash_csv.hexdigest(),json.dumps(dict(rejected)),source_id))
            conn.commit()
            reports.append({'filename':file.filename,'sensor':sensor,'nominal_year':file_year,
                            'rows_read':count,'accepted_type0':accepted,'excluded_non_vegetation':nonveg,
                            'rejected_invalid':bad,'min_date':first,'max_date':last,
                            'errors':dict(rejected),'source_sha256':hash_csv.hexdigest()})
            total_source += count; total_accepted += accepted; total_nonveg += nonveg; total_rejected += bad
            print(f'[{idx}/{len(members)}] {file.filename}: read={count:,}, vegetation={accepted:,}, rejected={bad:,}',flush=True)
    print('Creating indexes...',flush=True)
    conn.executescript('''
       CREATE INDEX idx_hotspot_date_sensor ON hotspots(date_utc,sensor);
       CREATE INDEX idx_hotspot_year_month_lon_lat ON hotspots(year,month,longitude,latitude);
       CREATE INDEX idx_hotspot_grid_date ON hotspots(grid_x,grid_y,date_utc);
       CREATE INDEX idx_hotspot_sensor_year_month ON hotspots(sensor,year,month);
    ''')
    conn.commit()
    print('Exporting aggregate tables...',flush=True)
    q = lambda group_cols: f'''SELECT {group_cols},COUNT(*) AS detection_count,
      ROUND(SUM(frp_mw),3) AS sum_detected_pixel_frp_mw,
      ROUND(AVG(frp_mw),3) AS mean_detected_pixel_frp_mw
      FROM hotspots GROUP BY {group_cols} ORDER BY {group_cols}'''
    table_counts={}
    # Keep sensor grain and UTC dates. Do not fill gaps as zeros.
    for name,group in [('daily_sensor','sensor,date_utc'),
                       ('monthly_sensor','sensor,year,month'),
                       ('annual_sensor','sensor,year')]:
        table_counts[name] = write_sql_csv(conn,q(group),(),out_dir / f'{name}.csv')
    if not skip_spatial:
        for name, group in [('monthly_grid','sensor,year,month,grid_x,grid_y'),
                            ('annual_grid','sensor,year,grid_x,grid_y')]:
            table_counts[name] = write_sql_csv(conn,q(group),(),out_dir / f'{name}.csv',
                extra_columns=['grid_center_lon','grid_center_lat'])
    add_metadata(conn,'pipeline_version','1.0.0')
    add_metadata(conn,'zip_sha256',archive_sha)
    add_metadata(conn,'date_timezone','UTC')
    add_metadata(conn,'grid_resolution_degrees',GRID_DEG)
    add_metadata(conn,'grid_lat_origin',LAT_ORIGIN)
    add_metadata(conn,'grid_lon_origin',LON_ORIGIN)
    add_metadata(conn,'record_definition','One active-fire pixel detection (NOT a distinct wildfire event)')
    add_metadata(conn,'filter','type = 0 presumed vegetation fire')
    add_metadata(conn,'geographic_qualification','Filename _Indonesia and coarse lon/lat bbox, NOT Indonesian boundary polygon')
    add_metadata(conn,'sensor_harmonized','FALSE')
    add_metadata(conn,'partial_input',bool(max_files or max_rows_per_file))
    conn.commit()
    sql_count=conn.execute('SELECT COUNT(*) FROM hotspots').fetchone()[0]
    group_count=conn.execute('SELECT SUM(accepted_type0) FROM source_files').fetchone()[0]
    assert sql_count==group_count==total_accepted, (sql_count,group_count,total_accepted)
    assert total_source==total_accepted+total_nonveg+total_rejected
    aggregated = {}
    for name in ('daily_sensor','monthly_sensor','annual_sensor'):
        with (out_dir/f'{name}.csv').open() as f:
            aggregated[name]=sum(int(row['detection_count']) for row in csv.DictReader(f))
        assert aggregated[name] == total_accepted, (name, aggregated[name],total_accepted)
    qa={'pipeline_version':'1.0.0','input_archive_name':src_zip.name,'input_sha256':archive_sha,
        'total_csv_in_archive':sum(m.filename.endswith('.csv') for m in zipfile.ZipFile(src_zip).infolist()),
        'processed_indonesia_files':len(reports),'total_indonesia_source_rows':total_source,
        'accepted_presumed_vegetation_detections':total_accepted,
        'excluded_non_vegetation_detections':total_nonveg,'rejected_invalid_rows':total_rejected,
        'spatial_validation':'coarse bounding box only; no administrative polygon validation',
        'duplicate_check':'not performed across sensors; distinct detections may observe same event',
        'timezone':'UTC', 'grid_degrees':GRID_DEG,
        'summary_reconciliation':aggregated,'aggregate_rows':table_counts,
        'build_seconds':round(time.time()-t0,1),
        'data_limitations':['Detections are not unique wildfire events.','type=0 is presumed vegetation fire, not verified forest fire.',
          'MODIS and VIIRS confidence scales are not equivalent.','No harmonization, ignitions, or cause labels are computed.',
          'Missing aggregate dates are unobserved/zero detections, not necessarily zero burning.',
          'Geographic bounding box does not guarantee land in Indonesia.',
          'Grid center is a visualization aggregation, not a fire coordinate.'],
        'source_files':reports}
    (out_dir/'quality_report.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
    conn.execute('PRAGMA optimize')
    conn.close()
    print('VALIDATED:',json.dumps({k:qa[k] for k in ('total_indonesia_source_rows','accepted_presumed_vegetation_detections','excluded_non_vegetation_detections','rejected_invalid_rows','aggregate_rows','build_seconds')},indent=2),flush=True)
    return qa


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Original FIRMS ZIP')
    p.add_argument('--output',type=Path,required=True,help='Output directory')
    p.add_argument('--max-files',type=int,help='Smoke-test only')
    p.add_argument('--max-rows-per-file',type=int,help='Smoke-test only')
    p.add_argument('--skip-spatial',action='store_true')
    a=p.parse_args()
    build(a.input,a.output,a.max_files,a.max_rows_per_file,a.skip_spatial)

if __name__=='__main__':
    main()
