"""Read-only viewport-scoped query helpers for VESTIGIUM map hover."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SENSORS={"MODIS","VIIRS_SNPP","VIIRS_NOAA20"}

def fetch_hotspots(db_path:str,year:int,month:int,
                   min_lon:float,min_lat:float,max_lon:float,max_lat:float,
                   limit:int=500,sensor:str|None=None):
    """Returns individual pixel detections; never claims these are unique fires."""
    if sensor is not None and sensor not in SENSORS:
        raise ValueError("Unknown sensor")
    if not(2000<=int(year)<=2025 and 1<=int(month)<=12):
        raise ValueError("Invalid UTC year or month")
    if min_lon>max_lon or min_lat>max_lat:
        raise ValueError("Invalid bounding box")
    if not (1<=int(limit)<=2000):
        raise ValueError("limit must be in [1, 2000]")
    sql="""SELECT latitude,longitude,date_utc,time_utc,timestamp_utc,sensor,
                  satellite,frp_mw,confidence_modis_pct,confidence_viirs_label
           FROM hotspots WHERE year=? AND month=?
           AND longitude BETWEEN ? AND ? AND latitude BETWEEN ? AND ?"""
    params=[int(year),int(month),min_lon,max_lon,min_lat,max_lat]
    if sensor is not None:
        sql+=" AND sensor=?"
        params.append(sensor)
    sql+=" ORDER BY date_utc,time_utc,id LIMIT ?"
    params.append(int(limit))
    con=sqlite3.connect(f"file:{Path(db_path).resolve()}?mode=ro",uri=True)
    con.row_factory=sqlite3.Row
    try:
        return [dict(row) for row in con.execute(sql,params)]
    finally:
        con.close()
