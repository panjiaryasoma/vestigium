#!/usr/bin/env python3
"""Optional and explicit ADM1/province point-in-polygon enrichment for VESTIGIUM.

This operation is NOT executed unless a sourced province boundary file is supplied.
Prefer a dated/sourced boundary set and record its release year.
A modern administrative label is not a reconstruction of historical province borders.
"""
from __future__ import annotations
import argparse
import sqlite3
from pathlib import Path
import pandas as pd
import geopandas as gpd


def match_province(points: pd.DataFrame, boundaries: gpd.GeoDataFrame, name_field: str):
    """Return one row per id; ambiguous overlaps are never silently resolved."""
    required={'id','latitude','longitude'}
    if not required.issubset(points.columns):raise ValueError('Missing point fields: '+str(required-points.columns))
    if name_field not in boundaries.columns:raise ValueError('Missing polygon name field '+name_field)
    crs=boundaries.crs
    if crs is None:raise ValueError('Boundary CRS missing; do not infer EPSG:4326 without evidence')
    p=gpd.GeoDataFrame(points.copy(),geometry=gpd.points_from_xy(points.longitude,points.latitude),crs='EPSG:4326')
    b=boundaries[[name_field,'geometry']].to_crs('EPSG:4326')
    matches=gpd.sjoin(p,b,how='left',predicate='within')
    grouped=matches.groupby('id',sort=False)[name_field].agg(lambda v:sorted(set(map(str,v.dropna())))).reset_index()
    grouped['match_count']=grouped[name_field].str.len()
    grouped['province_name']=grouped.apply(lambda r:r[name_field][0] if r.match_count==1 else None,axis=1)
    grouped['spatial_join_status']=grouped.match_count.map(lambda n:'matched' if n==1 else ('unmatched' if n==0 else 'ambiguous_overlap'))
    return grouped[['id','province_name','spatial_join_status','match_count']]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db',required=True,help='Basic VESTIGIUM Data Engineering SQLite hotspots database')
    ap.add_argument('--boundaries',required=True,help='Sourced ADM1 GeoJSON/GPKG/Shapefile')
    ap.add_argument('--name-column',default='shapeName')
    ap.add_argument('--out',required=True)
    ap.add_argument('--limit',type=int,default=None,help='Optional reproducible test subset; omit for entire DB')
    args=ap.parse_args()
    b=gpd.read_file(args.boundaries)
    dst=Path(args.out);dst.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(args.db) as con:
        n=0
        query='SELECT id, latitude, longitude FROM hotspots ORDER BY id'+(' LIMIT '+str(args.limit) if args.limit else '')
        for chunk in pd.read_sql_query(query,con,chunksize=100000):
            matched=match_province(chunk,b,args.name_column)
            matched.to_csv(dst,mode='a',header=not dst.exists(),index=False)
            n+=len(matched)
            print(f'joined {n:,} hotspot detections',flush=True)
    print('Province enrichment completed. Historical boundary interpretation is NOT implied.')

if __name__=='__main__':main()
