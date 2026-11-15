"""Rebuild the three main VESTIGIUM data stages from the original FIRMS ZIP.

Run from any working directory:
 python scripts/run_all.py --input data/raw/data.zip

Requires sufficient local disk space (multi-GB for a ~6M-record source) and time.
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PYTHON=sys.executable

def run(*args):
    cmd=[PYTHON,*map(str,args)]
    print("\n$", " ".join(cmd), flush=True)
    subprocess.run(cmd,cwd=ROOT,check=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=ROOT/"data/raw/data.zip")
    p.add_argument("--output",type=Path,default=ROOT/"data/processed")
    a=p.parse_args()
    src=a.input if a.input.is_absolute() else ROOT/a.input
    out=a.output if a.output.is_absolute() else ROOT/a.output
    if not src.is_file():
        p.error(f"NASA FIRMS source archive not found: {src}")
    out.mkdir(parents=True,exist_ok=True)
    run(ROOT/"src/pipelines/build_pipeline.py",
        "--input",src,"--output",out/"data-engineering")
    run(ROOT/"src/pipelines/run_advanced.py",
        "--database",out/"data-engineering/vestigium_hotspots.sqlite",
        "--output",out/"geospatial")
    run(ROOT/"src/pipelines/harmonize.py",
        "--input",out/"geospatial/monthly_equal_area_25km.csv",
        "--output",out/"harmonization")
    if out.resolve()==(ROOT/"data/processed").resolve():
        run(ROOT/"src/pipelines/validate_outputs.py","--root",ROOT)
    else:
        print("Custom output location: run validate_outputs against standard paths separately.")
    print("All requested stages completed; review QA reports before publishing results.")

if __name__=="__main__":
    main()
