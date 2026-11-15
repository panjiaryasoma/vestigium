"""Reconcile expected pixel-count conservation across VESTIGIUM stages.

Usage:
 python src/pipelines/validate_outputs.py --root .
"""
from __future__ import annotations
import argparse
import csv
import json
import sqlite3
from pathlib import Path

def sum_csv(path:Path,column:str="detection_count"):
    with path.open(newline="",encoding="utf8") as fp:
        return sum(int(row[column]) for row in csv.DictReader(fp))

def validate(root:Path):
    root=root.resolve()
    de=root/"data/processed/data-engineering"
    geo=root/"data/processed/geospatial"
    harm=root/"data/processed/harmonization"
    q1=json.loads((de/"quality_report.json").read_text())
    q2=json.loads((geo/"geospatial_quality_report.json").read_text())
    evaluation=json.loads((harm/"evaluation.json").read_text())
    src_count=int(q1["accepted_presumed_vegetation_detections"])
    con=sqlite3.connect(f"file:{(de/'vestigium_hotspots.sqlite').resolve()}?mode=ro",uri=True)
    try:
        actual=con.execute("SELECT COUNT(*) FROM hotspots").fetchone()[0]
        assert actual==src_count,(actual,src_count)
        assert con.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        source_totals=dict(con.execute(
           "SELECT sensor,COUNT(*) FROM hotspots GROUP BY sensor"))
    finally:
        con.close()
    for name in ("daily_sensor.csv","monthly_sensor.csv","annual_sensor.csv",
                 "monthly_grid.csv","annual_grid.csv"):
        count=sum_csv(de/name)
        assert count==src_count,(name,count,src_count)
    assert int(q2["accepted_type0"])==src_count
    assert int(q2["cell_size_meters"])==25_000
    assert sum_csv(geo/"monthly_equal_area_25km.csv")==src_count
    for value in (1.0,0.5,0.25,0.1):
        label=str(value).replace(".","p")
        name=f"monthly_geographic_{label}deg.csv"
        assert sum_csv(geo/name)==src_count,(name)
    fit_totals={k:int(v) for k,v in evaluation["source_by_sensor"].items()}
    assert fit_totals==source_totals,(fit_totals,source_totals)
    checks={"db_integrity":"ok","source_pixels":src_count,
            "by_sensor":source_totals,"data_engineering_grid_count":"PASS",
            "equal_area_count":"PASS","harmonization_source_count":"PASS",
            "scientific_scope":"pixel-level detection reconciliation, not model accuracy",
            "model_validation_method":evaluation.get("preferred_method")}
    print(json.dumps(checks,indent=2))
    return checks

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    validate(a.root)
