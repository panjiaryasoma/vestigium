#!/usr/bin/env python3
"""OPTIONAL: Stream SQLite records to year/sensor Parquet files (requires pyarrow).

Install in your own environment: pip install pyarrow
Run after build_pipeline.py: python export_parquet_optional.py --db outputs/vestigium_hotspots.sqlite --out outputs/parquet
"""
import argparse
import sqlite3
from pathlib import Path

def export(db, out, chunk=100000):
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:
        raise SystemExit('Parquet is optional. Install pyarrow in your own environment: pip install pyarrow') from e
    out = Path(out);out.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(f'file:{Path(db).resolve()}?mode=ro',uri=True) as conn:
        groups=conn.execute('SELECT sensor,year FROM hotspots GROUP BY sensor,year ORDER BY sensor,year').fetchall()
        for sensor,year in groups:
            dest=out/f'sensor={sensor}'/f'year={year}'
            dest.mkdir(parents=True,exist_ok=True)
            writer=None
            cur=conn.execute('SELECT * FROM hotspots WHERE sensor=? AND year=? ORDER BY id',(sensor,year))
            keys=[x[0] for x in cur.description]
            try:
                while True:
                    rows=cur.fetchmany(chunk)
                    if not rows:break
                    ascols={k:[r[j] for r in rows] for j,k in enumerate(keys)}
                    t=pa.table(ascols)
                    if writer is None:writer=pq.ParquetWriter(dest/'part-0000.parquet', t.schema, compression='zstd')
                    writer.write_table(t)
            finally:
                if writer:writer.close()
            print(sensor,year,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--db',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--chunk',type=int,default=100000)
    a=p.parse_args()
    export(a.db,a.out,a.chunk)
