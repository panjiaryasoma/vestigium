#!/usr/bin/env python3
"""Independent output QA: totals, schema, sensor confidences, timestamps, and grid bounds."""
import argparse,csv,json,sqlite3
from pathlib import Path

def validate(folder):
    p=Path(folder)
    qa=json.loads((p/'quality_report.json').read_text())
    with sqlite3.connect(f'file:{(p/"vestigium_hotspots.sqlite").resolve()}?mode=ro',uri=True) as db:
        c=db.execute('SELECT COUNT(*) FROM hotspots').fetchone()[0]
        assert c==qa['accepted_presumed_vegetation_detections']
        assert db.execute('SELECT COUNT(*) FROM hotspots WHERE year<2000 OR year>2025').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM hotspots WHERE frp_mw<0 OR frp_mw IS NULL').fetchone()[0]==0
        assert db.execute('SELECT COUNT(*) FROM hotspots WHERE latitude NOT BETWEEN -12 AND 8 OR longitude NOT BETWEEN 94 AND 142').fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM hotspots WHERE sensor='MODIS' AND (confidence_viirs_label IS NOT NULL OR confidence_modis_pct IS NULL)").fetchone()[0]==0
        assert db.execute("SELECT COUNT(*) FROM hotspots WHERE sensor LIKE 'VIIRS%' AND (confidence_modis_pct IS NOT NULL OR confidence_viirs_label NOT IN ('l','n','h'))").fetchone()[0]==0
        counts=db.execute('SELECT sensor,COUNT(*) FROM hotspots GROUP BY sensor').fetchall()
    aggs={}
    for name in ['daily_sensor','monthly_sensor','annual_sensor','monthly_grid','annual_grid']:
        f=p/f'{name}.csv'
        if not f.exists():continue
        with f.open() as h:
            aggs[name]=sum(int(r['detection_count']) for r in csv.DictReader(h))
        assert aggs[name]==c, f'Count reconciliation failed: {name} {aggs[name]} vs {c}'
    result={'status':'PASS','rows':c,'by_sensor':dict(counts),'aggregate_checks':aggs}
    (p/'validation_result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True)
    validate(p.parse_args().output)
