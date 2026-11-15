#!/usr/bin/env python3
"""VESTIGIUM | Advanced geospatial preprocessing of NASA FIRMS detections.

Source of truth: data.zip with MODIS / VIIRS Indonesia CSVs (2000--2025).
This script creates geographic display grids and equal-area analytical grids.
All detections are sensor-specific pixel observations, NOT verified wildfire events.

Raw individual detections remain in the earlier Data Engineering SQLite database.
This stage is additive and does not modify or discard that database.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

SENSORS = {'viirs-snpp/': 'VIIRS_SNPP', 'viirs-jpss1/':'VIIRS_NOAA20', 'modis/':'MODIS'}
RAW_COLS = ['latitude','longitude','acq_date','acq_time','frp','type','daynight','satellite','confidence']
INDO_BBOX = (94., -12., 142., 8.)
FINE_DEGREES = .1
EA_CELL_METERS = 25000
NODATA_NOTE = 'A zero detection count does not imply zero fires; observation coverage differs by sensor and period.'


def sensor_for(path: str):
    p = path.lower()
    if not p.endswith('_indonesia.csv'): return None
    for prefix,s in SENSORS.items():
        if p.startswith(prefix): return s
    return None


def coord_grid(lon, lat, resolution):
    """Stable global grid indices; centers reconstructed exactly from indices."""
    lon = np.asarray(lon,dtype='float64'); lat = np.asarray(lat,dtype='float64')
    x = np.floor((lon + 180.) / resolution).astype('int32')
    y = np.floor((lat + 90.) / resolution).astype('int32')
    return x,y


def grid_centers(x,y,resolution):
    return np.round(-180.+(np.asarray(x)+.5)*resolution,6),np.round(-90.+(np.asarray(y)+.5)*resolution,6)


def prepare(raw, year):
    """Same type=0, bbox, timestamp and FRP acceptance criteria as basic ETL."""
    v = raw.loc[pd.to_numeric(raw['type'],errors='coerce').eq(0)].copy()
    for c in ['latitude','longitude','frp']:
        v[c] = pd.to_numeric(v[c],errors='coerce')
    v = v.loc[(v.latitude.between(INDO_BBOX[0+1],INDO_BBOX[3]) &
              v.longitude.between(INDO_BBOX[0],INDO_BBOX[2])) &
              np.isfinite(v.latitude) & np.isfinite(v.longitude) &
              np.isfinite(v.frp) & (v.frp >= 0)].copy()
    dates=pd.to_datetime(v.acq_date,errors='coerce',utc=True)
    times=v.acq_time.astype(str).str.replace('.0','',regex=False).str.zfill(4)
    hh=pd.to_numeric(times.str[:2],errors='coerce'); mm=pd.to_numeric(times.str[2:],errors='coerce')
    valid=(dates.dt.year.eq(year) & times.str.fullmatch(r'\d{4}') &
           hh.between(0,23) & mm.between(0,59) & v.daynight.isin(['D','N']) &
           v.satellite.notna())
    v=v.loc[valid].copy()
    v['year']=year
    v['month']=dates.loc[valid].dt.month.astype('int8')
    v['time_utc']=times.loc[valid]
    return v


def agg_per_file(frame, kind, sensor, transformer):
    frame=frame.copy()
    if kind=='geographic_01':
        frame['cell_x'],frame['cell_y']=coord_grid(frame.longitude,frame.latitude,FINE_DEGREES)
    elif kind=='equal_area_25km':
        e,n=transformer.transform(frame.longitude.to_numpy(dtype='float64'),frame.latitude.to_numpy(dtype='float64'))
        frame['cell_x']=np.floor(e/EA_CELL_METERS).astype('int32')
        frame['cell_y']=np.floor(n/EA_CELL_METERS).astype('int32')
    else:raise ValueError(kind)
    frame['is_daytime']=frame.daynight.eq('D').astype('int8')
    grp=frame.groupby(['year','month','cell_x','cell_y'],observed=True,sort=True).agg(
        detection_count=('frp','size'),
        sum_detected_pixel_frp_mw=('frp','sum'),
        max_detected_pixel_frp_mw=('frp','max'),
        daytime_detections=('is_daytime','sum')
    ).reset_index()
    grp.insert(0,'sensor',sensor)
    grp['nighttime_detections']=grp.detection_count-grp.daytime_detections
    if kind=='geographic_01':
        grp['center_longitude'],grp['center_latitude']=grid_centers(grp.cell_x,grp.cell_y,FINE_DEGREES)
    else:
        e=(grp.cell_x.to_numpy()+.5)*EA_CELL_METERS
        n=(grp.cell_y.to_numpy()+.5)*EA_CELL_METERS
        lon,lat=transformer.transform(e,n,direction='INVERSE')
        grp['center_longitude']=np.round(lon,6)
        grp['center_latitude']=np.round(lat,6)
    # keep fraction precision in FRP (this is a SUM of detected pixel FRP, not a fire-energy estimate)
    for name in ['sum_detected_pixel_frp_mw','max_detected_pixel_frp_mw']:
        grp[name]=grp[name].round(4)
    return grp


def postaggregate_base_025(base, resolution):
    """Coarsen exact 0.25-degree base grid. All counts conserved; FRP may differ by rounding <= 0.1 MW."""
    assert resolution in (.5,1.)
    fac=int(round(resolution/.25))
    x=base.copy()
    x['cell_x']=(x.grid_x.astype('int32')//fac).astype('int32')
    x['cell_y']=(x.grid_y.astype('int32')//fac).astype('int32')
    g=x.groupby(['sensor','year','month','cell_x','cell_y'],sort=True,as_index=False).agg(
        detection_count=('detection_count','sum'),
        sum_detected_pixel_frp_mw=('sum_detected_pixel_frp_mw','sum'))
    g['center_longitude']=np.round(94+(g.cell_x.to_numpy()+.5)*resolution,5)
    g['center_latitude']=np.round(-12+(g.cell_y.to_numpy()+.5)*resolution,5)
    g['sum_detected_pixel_frp_mw']=g.sum_detected_pixel_frp_mw.round(4)
    return g


def monthly_sensor_pair(base):
    # Raw sensor counts on same UTC month and 0.25deg tile; no calibration.
    keys=['year','month','grid_x','grid_y']
    p=base.pivot_table(index=keys,columns='sensor',values='detection_count',fill_value=0,aggfunc='sum').reset_index()
    p.columns.name=None
    for s in ('MODIS','VIIRS_SNPP','VIIRS_NOAA20'):
        if s not in p:p[s]=0
    p['raw_modis_minus_snpp']=p.MODIS-p.VIIRS_SNPP
    p['sensor_overlap_period']=p.year>=2012
    return p


def file_sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as src:
        for block in iter(lambda:src.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def write_csv(out,path,append=False):
    path.parent.mkdir(exist_ok=True,parents=True)
    out.to_csv(path,mode='a' if append else 'w',index=False,header=not append,float_format='%.6f')


def validate_boundaries(sample,coarse_geojson):
    """Diagnostic ONLY. Coarse national polygon under-represents small Indonesian islands."""
    if coarse_geojson is None or not Path(coarse_geojson).exists():
        return {'status':'not_run','reason':'No reference national boundary supplied'}
    import geopandas as gpd
    import shapely
    from shapely import contains_xy
    gdf=gpd.read_file(coarse_geojson)
    mask=contains_xy(gdf.geometry.union_all(),sample.longitude.to_numpy(),sample.latitude.to_numpy())
    return {'status':'diagnostic_only','sample_count':int(len(sample)),
            'inside_low_resolution_country_polygon':int(np.sum(mask)),
            'outside_low_resolution_country_polygon':int(len(sample)-np.sum(mask)),
            'boundary_precision':'Natural Earth 1:110m; NOT suitable for rejecting islands/coastal pixel centroids'}


def build(zip_path,base_csv,out,reference_boundary=None,max_files=None):
    start=time.time();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    base=pd.read_csv(base_csv)
    base['sensor']=base.sensor.astype(str)
    baseline_count=int(base.detection_count.sum())
    for resolution,name in [(.5,'monthly_grid_05deg.csv'),(1.,'monthly_grid_1deg.csv')]:
        result=postaggregate_base_025(base,resolution)
        write_csv(result,out/name)
        assert int(result.detection_count.sum())==baseline_count
    pairs=monthly_sensor_pair(base)
    write_csv(pairs,out/'sensor_comparison_025deg_raw.csv')
    # retain previous stage's 0.25-degree grids with metadata naming
    base.to_csv(out/'monthly_grid_025deg.csv',index=False)

    fine_path=out/'monthly_grid_01deg.csv';ea_path=out/'monthly_equal_area_25km.csv'
    for p in [fine_path,ea_path]:
        if p.exists():p.unlink()
    transformer=Transformer.from_crs('EPSG:4326','EPSG:6933',always_xy=True)
    stats={'source_zip':str(zip_path),'source_zip_sha256':file_sha256(zip_path),'base_grid_sha256':file_sha256(base_csv),'start_year':2000,'end_year':2025,'raw_sensor_files':0,
           'total_source_rows':0,'accepted_type0':0,'by_sensor':{},'per_file':[],
           'baseline_025_degree_total_type0':baseline_count,'bbox':INDO_BBOX,
           'fine_grid_degrees':FINE_DEGREES,'equal_area_crs':'EPSG:6933',
           'equal_area_cell_size_m':EA_CELL_METERS,
           'spatial_join_adm1':'not_performed_missing_adm1_geojson',
           'country_polygon_source':'Natural Earth 1:110m diagnostic-only',
           'is_sensor_harmonized':False,'is_ground_truth_fire_events':False}
    sample_total=0
    # year 2015 September stratified deterministic per source for a frontend demo
    sample_file=out/'example_hover_points_2015_09.csv'
    if sample_file.exists():sample_file.unlink()
    sampled=[]
    boundary_sample=[]
    with zipfile.ZipFile(zip_path) as zin:
        files=[f for f in zin.namelist() if sensor_for(f)]
        files.sort()
        if max_files is not None:files=files[:max_files]
        for ix,f in enumerate(files,1):
            sensor=sensor_for(f)
            year=int(re.search(r'_(20\d{2})_Indonesia.csv$',f).group(1))
            with zin.open(f) as stream:
                raw=pd.read_csv(stream,usecols=RAW_COLS,low_memory=False)
            v=prepare(raw,year)
            stats['raw_sensor_files']+=1;stats['total_source_rows']+=len(raw)
            stats['accepted_type0']+=len(v)
            stats['by_sensor'][sensor]=stats['by_sensor'].get(sensor,0)+len(v)
            stats['per_file'].append({'file':f,'sensor':sensor,'year':year,'raw_rows':len(raw),'accepted_type0':len(v)})
            for kind,p in [('geographic_01',fine_path),('equal_area_25km',ea_path)]:
                a=agg_per_file(v,kind,sensor,transformer)
                write_csv(a,p,append=p.exists())
            if year==2015:
                subset=v.loc[v.month.eq(9)]
                if len(subset):
                    # deterministic subsample; display demo ONLY, not a valid statistical sample
                    sample=subset.iloc[np.linspace(0,len(subset)-1,min(8000,len(subset)),dtype=int)].copy()
                    sample.insert(0,'sensor',sensor)
                    cols=['sensor','satellite','acq_date','time_utc','latitude','longitude','frp','confidence']
                    sampled.append(sample[cols].rename(columns={'frp':'frp_mw'}))
            # diagnostic sample stratified across source files; no filtering by polygon
            if len(v):
                boundary_sample.append(v[['latitude','longitude']].iloc[np.linspace(0,len(v)-1,min(120,len(v)),dtype=int)].copy())
            print(f'[{ix:02d}/{len(files)}] {sensor:13s} {year}: accepted {len(v):,}',flush=True)
    if sampled:
        sample=pd.concat(sampled,ignore_index=True)
        sample.to_csv(sample_file,index=False)
        sample_total=len(sample)
    # Cross-output integrity, roundoff tolerant for FRP; no data dropped across sensor-month file grids
    fine=pd.read_csv(fine_path,usecols=['sensor','detection_count'])
    ea=pd.read_csv(ea_path,usecols=['sensor','detection_count'])
    stats['grid_outputs']={
        'monthly_grid_01deg':{'rows':len(fine),'detections':int(fine.detection_count.sum())},
        'monthly_equal_area_25km':{'rows':len(ea),'detections':int(ea.detection_count.sum())},
        'monthly_grid_025deg':{'rows':len(base),'detections':baseline_count},
        'monthly_grid_05deg':{'rows':int(pd.read_csv(out/'monthly_grid_05deg.csv',usecols=['sensor']).shape[0]),'detections':baseline_count},
        'monthly_grid_1deg':{'rows':int(pd.read_csv(out/'monthly_grid_1deg.csv',usecols=['sensor']).shape[0]),'detections':baseline_count},
        'raw_sensor_comparison_grid':{'rows':len(pairs)}
    }
    stats['hover_demo_rows']=sample_total
    # annual recurrence: number of years with >=1 detection per grid and sensor (NOT fire recurrence)
    grouped=base.groupby(['sensor','grid_x','grid_y']).agg(
        distinct_years_with_detections=('year','nunique'),
        total_detection_count=('detection_count','sum'),
        first_year=('year','min'),last_year=('year','max')).reset_index()
    write_csv(grouped.sort_values('distinct_years_with_detections',ascending=False),out/'recurrence_025deg_by_sensor.csv')
    stats['grid_outputs']['recurrence_025deg_by_sensor']={'rows':len(grouped)}
    if boundary_sample:
        s=pd.concat(boundary_sample,ignore_index=True)
        stats['national_boundary_diagnostic']=validate_boundaries(s,reference_boundary)
    # No implicit inference of provinces or fire ignition causes.
    stats['data_quality']={
        'expected_type0':5997676 if max_files is None else None,
        'agrees_with_baseline':int(stats['accepted_type0'])==baseline_count if max_files is None else None,
        'agrees_with_all_grids':all(int(stats['grid_outputs'][k]['detections'])==int(stats['accepted_type0'])
            for k in ('monthly_grid_01deg','monthly_equal_area_25km','monthly_grid_025deg')) if max_files is None else None}
    stats['elapsed_seconds']=round(time.time()-start,2)
    with (out/'geospatial_quality_report.json').open('w') as h:json.dump(stats,h,indent=2)
    assert max_files is not None or (stats['data_quality']['agrees_with_baseline'] and stats['data_quality']['agrees_with_all_grids']),stats['data_quality']
    return stats


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',required=True,help='Original NASA FIRMS data.zip archive')
    ap.add_argument('--base-grid',required=True,help='monthly_grid.csv generated by basic data engineering stage')
    ap.add_argument('--out',required=True)
    ap.add_argument('--country-boundary',default=None,help='Optional coarse national GeoJSON for diagnostic only')
    ap.add_argument('--max-files',type=int,default=None,help='Development-only partial run; never report as national total')
    args=ap.parse_args()
    s=build(Path(args.source),Path(args.base_grid),Path(args.out),args.country_boundary,args.max_files)
    print(json.dumps({'status':'PASS','elapsed_s':s['elapsed_seconds'],'type0':s['accepted_type0'],'grids':s['grid_outputs']},indent=2))

if __name__=='__main__':main()
