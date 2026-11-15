"""Advanced equal-area and multi-resolution spatial aggregation of FIRMS detections.

Input: SQLite produced by build_pipeline.py.
Output: data/processed/geospatial/monthly_equal_area_25km.csv plus QA summary.
Observation unit remains satellite thermal-pixel detections, never fire events.

Usage:
  python src/pipelines/run_advanced.py --database data/processed/data-engineering/vestigium_hotspots.sqlite --output data/processed/geospatial
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np
from pyproj import Transformer

CELL_M = 25_000
SCALES = (1.0, 0.5, 0.25, 0.1)

def cell_indices(lon, lat, width):
    return (math.floor((lon + 180.0) / width),
            math.floor((lat + 90.0) / width))

def equal_area_cell(longitude, latitude):
    to_equal = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    x,y = to_equal.transform(longitude,latitude)
    return math.floor(x / CELL_M), math.floor(y / CELL_M)

def rows_to_csv(con, path, query, fields):
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(fields)
        writer.writerows(con.execute(query))

def aggregate(database: Path, output: Path):
    if not database.is_file():
        raise FileNotFoundError(database)
    output.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    tmp_path = output / "_spatial_work.sqlite"
    if tmp_path.exists():
        tmp_path.unlink()
    tmp = sqlite3.connect(tmp_path)
    tmp.execute("PRAGMA journal_mode=OFF")
    tmp.execute("PRAGMA synchronous=OFF")
    tmp.execute("""CREATE TABLE grid_records(
        sensor TEXT,year INTEGER,month INTEGER,
        cell_x INTEGER,cell_y INTEGER,
        x1 INTEGER,y1 INTEGER,x05 INTEGER,y05 INTEGER,
        x025 INTEGER,y025 INTEGER,x01 INTEGER,y01 INTEGER,
        frp_mw REAL, day INTEGER,night INTEGER)""")
    forward = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    reverse = Transformer.from_crs("EPSG:6933", "EPSG:4326", always_xy=True)
    cursor = src.execute("SELECT sensor,year,month,longitude,latitude,frp_mw,daynight FROM hotspots ORDER BY id")
    count = 0
    while True:
        batch = cursor.fetchmany(20_000)
        if not batch:
            break
        lon = np.array([x[3] for x in batch], dtype="float64")
        lat = np.array([x[4] for x in batch], dtype="float64")
        ex, ey = forward.transform(lon, lat)
        rows = []
        for i,r in enumerate(batch):
            def geo(step):
                return cell_indices(r[3],r[4],step)
            x1,y1=geo(1.0)
            x05,y05=geo(0.5)
            x025,y025=geo(0.25)
            x01,y01=geo(0.1)
            rows.append((r[0],r[1],r[2],math.floor(ex[i]/CELL_M),math.floor(ey[i]/CELL_M),
                         x1,y1,x05,y05,x025,y025,x01,y01,r[5],int(r[6]=='D'),int(r[6]=='N')))
        tmp.executemany("INSERT INTO grid_records VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",rows)
        count+=len(rows)
        if count % 200_000 == 0:
            tmp.commit()
            print(f"Projected {count:,} source pixels",flush=True)
    tmp.commit()
    expected = src.execute("SELECT COUNT(*) FROM hotspots").fetchone()[0]
    assert count == expected
    # Grid-month records are sensor-specific. Source detections are never
    # deduplicated across satellite overpasses.
    sql = """SELECT year,month,sensor,cell_x,cell_y,
                 COUNT(*) AS detection_count, ROUND(SUM(frp_mw),5) AS frp_sum_mw,
                 ROUND(MAX(frp_mw),5) AS max_frp_mw,
                 SUM(day) AS daytime_detections, SUM(night) AS nighttime_detections
             FROM grid_records
             GROUP BY year,month,sensor,cell_x,cell_y
             ORDER BY year,month,sensor,cell_x,cell_y"""
    path=output/"monthly_equal_area_25km.csv"
    grouped = 0
    conserved = 0
    with path.open("w",newline="",encoding="utf8") as f:
        w=csv.writer(f)
        w.writerow(["year","month","sensor","cell_x","cell_y","detection_count",
                    "frp_sum_mw","max_frp_mw","daytime_detections","nighttime_detections",
                    "center_longitude","center_latitude"])
        for year,month,sensor,cx,cy,n,frp,max_frp,dn,nn in tmp.execute(sql):
            center_x=(cx+0.5)*CELL_M
            center_y=(cy+0.5)*CELL_M
            lon,lat=reverse.transform(center_x,center_y)
            w.writerow([year,month,sensor,cx,cy,n,frp,max_frp,dn,nn,round(lon,6),round(lat,6)])
            grouped+=1
            conserved+=n
    assert conserved==expected
    result={"input_sqlite":str(database),"accepted_type0":expected,
            "equal_area_crs":"EPSG:6933","cell_size_meters":CELL_M,
            "equal_area_rows":grouped,"all_detectors_reconciled":True,
            "pixel_caveat":"Pixel-center aggregation, not wildfire incidents or burned-area estimates"}
    for res,colx,coly in [(1.0,"x1","y1"),(0.5,"x05","y05"),
                           (0.25,"x025","y025"),(0.1,"x01","y01")]:
        label=str(res).replace(".","p")
        query=f"""SELECT year,month,sensor,{colx} AS grid_x,{coly} AS grid_y,
                   COUNT(*) AS detection_count,ROUND(SUM(frp_mw),5) AS frp_sum_mw
                FROM grid_records GROUP BY year,month,sensor,{colx},{coly}
                ORDER BY year,month,sensor,{colx},{coly}"""
        name=f"monthly_geographic_{label}deg.csv"
        rows_to_csv(tmp,output/name,query,
                    ["year","month","sensor","grid_x","grid_y","detection_count","frp_sum_mw"])
        total=tmp.execute(f"SELECT COUNT(*) FROM grid_records").fetchone()[0]
        assert total==expected
    (output/"geospatial_quality_report.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    src.close()
    tmp.close()
    tmp_path.unlink(missing_ok=True)  # Remove disposable multi-GB intermediate after QA.
    print(json.dumps(result,indent=2))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--database",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    aggregate(a.database,a.output)
