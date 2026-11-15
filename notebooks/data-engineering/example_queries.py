#!/usr/bin/env python3
"""Read-only examples for querying a Vestigium SQLite detection store."""
import argparse
import json
import sqlite3
from pathlib import Path


def fetch_hotspots(db: str, year: int, month: int, west: float, south: float,
                   east: float, north: float, limit: int = 50, sensor: str | None = None):
    if not (1 <= month <= 12 and 2000 <= year <= 2100):
        raise ValueError('Invalid year or month')
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError('Invalid bounding box')
    if not (1 <= limit <= 1000):
        raise ValueError('Limit must be between 1 and 1000')
    with sqlite3.connect(f'file:{Path(db).resolve()}?mode=ro', uri=True) as con:
        con.row_factory = sqlite3.Row
        sql = '''SELECT latitude, longitude, date_utc, time_utc, timestamp_utc,
           sensor, satellite, frp_mw, confidence_modis_pct, confidence_viirs_label,
           daynight FROM hotspots WHERE year=? AND month=?
           AND longitude BETWEEN ? AND ? AND latitude BETWEEN ? AND ?'''
        params = [year, month, west, east, south, north]
        if sensor is not None:
            if sensor not in {'MODIS', 'VIIRS_SNPP', 'VIIRS_NOAA20'}:
                raise ValueError('Unrecognized sensor')
            sql += ' AND sensor=?'; params.append(sensor)
        sql += ' ORDER BY date_utc, time_utc, id LIMIT ?'; params.append(limit)
        return [dict(row) for row in con.execute(sql, params)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',required=True)
    p.add_argument('--year',type=int,default=2015)
    p.add_argument('--month',type=int,default=9)
    p.add_argument('--west',type=float,default=108)
    p.add_argument('--south',type=float,default=-4)
    p.add_argument('--east',type=float,default=119)
    p.add_argument('--north',type=float,default=4)
    p.add_argument('--sensor',choices=['MODIS','VIIRS_SNPP','VIIRS_NOAA20'])
    p.add_argument('--limit',type=int,default=10)
    a=p.parse_args()
    print(json.dumps(fetch_hotspots(a.db,a.year,a.month,a.west,a.south,a.east,a.north,a.limit,a.sensor),indent=2))

if __name__=='__main__': main()
