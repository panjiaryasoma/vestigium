#!/usr/bin/env python3
"""VESTIGIUM - reproducible raw FIRMS EDA, chunk streamed from the user's ZIP.
Usage: python vestigium_eda.py /path/to/data.zip /path/to/output_dir
Outputs audit JSON, aggregation tables, and sampled/non-spatially verified hotspot grids.
No machine-learning or causal fire origin classifications are performed.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import csv, io, json, re, sys, zipfile
import numpy as np
import pandas as pd

SRC = {'MODIS':'MODIS','viirs-snpp':'VIIRS S-NPP','viirs-jpss1':'VIIRS NOAA-20'}
BBOX = {'lat_min':-12,'lat_max':6.5,'lon_min':94,'lon_max':142}  # coarse envelope, not land polygon
FIELDS_CORE = ['latitude','longitude','acq_date','acq_time','frp','type','confidence','daynight','satellite','version']
CHUNKSIZE = 150_000

def analyze(zip_path: Path, out: Path):
    out.mkdir(parents=True,exist_ok=True)
    tables=out/'tables'; tables.mkdir(exist_ok=True)
    file_stats=[]; schemas={}; source_n=Counter(); source_type=Counter(); source_dn=Counter()
    source_conf=Counter(); source_version=Counter(); satellite_count=Counter(); source_year_all=Counter()
    by_month=Counter(); by_day=Counter(); by_hour=Counter(); grid_year=Counter(); grid_2019_month=Counter()
    nulls=Counter(); counts_per_field=Counter(); invalid=Counter(); sample_spots=[]
    frp_values=defaultdict(list); modis_conf=[]; dates_by_source=defaultdict(set)
    source_frp_sum=Counter(); source_frp_n=Counter(); version_by_year=Counter()
    all_records=0; excluded=[]; schema_drift=[]
    with zipfile.ZipFile(zip_path) as z:
      members=[n for n in z.namelist() if n.lower().endswith('.csv')]
      for fi, name in enumerate(members,1):
        if not name.lower().endswith('_indonesia.csv'):
            excluded.append(name); continue
        pathsrc=name.split('/')[0]; src=SRC.get(pathsrc)
        if not src:
            excluded.append(name); continue
        m=re.search(r'_(20\d\d)_Indonesia\.csv$',name,re.I)
        file_year=int(m.group(1)) if m else -1
        dup_hashes=set(); file_dups=0; nfile=0; ntype0=0; file_min=None; file_max=None
        with z.open(name) as handle:
          rd=pd.read_csv(handle,chunksize=CHUNKSIZE,low_memory=False,dtype={'confidence':'string','version':'string','satellite':'string','instrument':'string','daynight':'string','acq_date':'string','acq_time':'string'},on_bad_lines='error')
          for ch in rd:
            n=len(ch); nfile+=n; all_records+=n; source_n[src]+=n
            cols=tuple(ch.columns)
            if src not in schemas:schemas[src]=list(cols)
            elif tuple(schemas[src])!=cols:schema_drift.append({'file':name,'columns':list(cols)})
            nulls.update({(src,c):int(x) for c,x in ch.isna().sum().items()})
            counts_per_field.update({(src,c):n for c in ch.columns})
            # Count identical full-row hashes within each yearly file (not same event across sensors).
            row_h=pd.util.hash_pandas_object(ch,index=False).to_numpy(dtype=np.uint64)
            # Most duplicates are in-chunk; set also captures across chunk boundaries.
            if len(np.unique(row_h))!=len(row_h) or len(dup_hashes):
                uniques,counts=np.unique(row_h,return_counts=True)
                file_dups+=int(np.maximum(counts-1,0).sum())
                file_dups+=sum(int(h in dup_hashes) for h in uniques)
                dup_hashes.update(map(int,uniques))
            else:
                dup_hashes.update(map(int,row_h))
            dt=pd.to_datetime(ch['acq_date'],errors='coerce')
            yr=dt.dt.year
            month=dt.dt.month
            valid_date=dt.notna()
            invalid[(src,'date_parse')]+=int((~valid_date).sum())
            invalid[(src,'file_year_mismatch')]+=int((valid_date & (yr!=file_year)).sum())
            if valid_date.any():
              mn=str(dt.min().date()); mx=str(dt.max().date());file_min=mn if file_min is None else min(mn,file_min);file_max=mx if file_max is None else max(mx,file_max)
              dates_by_source[src].update(dt.loc[valid_date].dt.strftime('%Y-%m-%d').unique().tolist())
            lat=pd.to_numeric(ch['latitude'],errors='coerce'); lon=pd.to_numeric(ch['longitude'],errors='coerce')
            frp=pd.to_numeric(ch['frp'],errors='coerce'); typ=pd.to_numeric(ch['type'],errors='coerce')
            validgeo=lat.between(-90,90)&lon.between(-180,180)
            envelope=lat.between(BBOX['lat_min'],BBOX['lat_max'])&lon.between(BBOX['lon_min'],BBOX['lon_max'])
            invalid[(src,'invalid_geo_world')]+=int((~validgeo).sum())
            invalid[(src,'out_of_rough_ID_bbox')]+=int((~envelope).sum())
            invalid[(src,'invalid_frp')]+=int((frp.isna()|(frp<0)).sum())
            invalid[(src,'invalid_type')]+=int((~typ.isin([0,1,2,3])).sum())
            hhmm=pd.to_numeric(ch['acq_time'].str.zfill(4),errors='coerce')
            hh=np.floor(hhmm/100)
            mm=hhmm%100
            valid_time=hh.between(0,23)&mm.between(0,59)
            invalid[(src,'invalid_utc_time')]+=int((~valid_time).sum())
            # Distinct evidence variables include all detected thermal anomaly categories.
            for t,c in typ.value_counts(dropna=False).items():source_type[(src,str(int(t)) if pd.notna(t) else 'missing')]+=int(c)
            for val,c in ch['daynight'].fillna('missing').value_counts().items():source_dn[(src,str(val))]+=int(c)
            for val,c in ch['confidence'].fillna('missing').value_counts().items():source_conf[(src,str(val))]+=int(c)
            for val,c in ch['version'].fillna('missing').value_counts().items():source_version[(src,str(val))]+=int(c)
            for val,c in ch['satellite'].fillna('missing').value_counts().items():satellite_count[(src,str(val))]+=int(c)
            for y,c in yr.value_counts().items():
              if pd.notna(y):source_year_all[(src,int(y))]+=int(c)
            if src=='MODIS':
              for (y,v),c in ch.groupby([yr,ch['version']],dropna=False).size().items():
                if pd.notna(y):version_by_year[(int(y),str(v))]+=int(c)
            # Type 0: presumed vegetation fire. No claim about forest location or cause.
            mask=typ.eq(0)&valid_date&validgeo&frp.notna()&frp.ge(0)
            tc=ch.loc[mask].copy()
            k=len(tc);ntype0+=k
            if not k:continue
            frp_t=frp.loc[mask].to_numpy(dtype=np.float32)
            frp_values[src].append(frp_t)
            source_frp_sum[src]+=float(np.sum(frp_t,dtype=np.float64)); source_frp_n[src]+=k
            if src=='MODIS':
              modis_conf.append(pd.to_numeric(tc['confidence'],errors='coerce').to_numpy(np.float32))
            # Slice and group raw records into UTC calendar aggregates.
            tc['utcdate']=dt.loc[mask].dt.strftime('%Y-%m-%d').to_numpy()
            tc['yr']=yr.loc[mask].astype(int).to_numpy()
            tc['mon']=month.loc[mask].astype(int).to_numpy()
            tc['frpnum']=frp_t
            monthly=tc.groupby(['yr','mon']).agg(count=('frpnum','size'),frp_sum=('frpnum','sum'))
            for (y,mo),r in monthly.iterrows():
              by_month[(src,int(y),int(mo),'count')]+=int(r['count'])
              by_month[(src,int(y),int(mo),'frp_sum')]+=float(r['frp_sum'])
            daily=tc.groupby('utcdate').agg(count=('frpnum','size'),frp_sum=('frpnum','sum'))
            for d,r in daily.iterrows():
              by_day[(src,str(d),'count')]+=int(r['count'])
              by_day[(src,str(d),'frp_sum')]+=float(r['frp_sum'])
            for hr,c in pd.Series(hh.loc[mask].loc[valid_time.loc[mask]].astype(int)).value_counts().items():
              by_hour[(src,int(hr))]+=int(c)
            # 0.5 degree bins are for EDA and not a valid administrative map.
            tc['latbin']=(np.floor(lat.loc[mask].to_numpy()*2)/2).astype('float32')
            tc['lonbin']=(np.floor(lon.loc[mask].to_numpy()*2)/2).astype('float32')
            cell=tc.groupby(['yr','latbin','lonbin']).size()
            for (y,la,lo),count in cell.items():grid_year[(src,int(y),float(la),float(lo))]+=int(count)
            if src in ('MODIS','VIIRS S-NPP'):
              sub=tc.loc[tc['yr']==2019]
              if not sub.empty:
                for (mo,la,lo),count in sub.groupby(['mon','latbin','lonbin']).size().items():
                  grid_2019_month[(src,int(mo),float(la),float(lo))]+=int(count)
            if len(sample_spots)<36:
              for _,row in tc.head(min(36-len(sample_spots),4)).iterrows():
                sample_spots.append({'source':src,'date_utc':str(row['utcdate']),'latitude':float(row['latitude']),'longitude':float(row['longitude']),'frp_mw':float(row['frpnum']),'type':0})
        file_stats.append({'filename':name,'sensor':src,'filename_year':file_year,'rows_all':nfile,'rows_type0':ntype0,'duplicate_full_rows_within_file':file_dups,'first_date_utc':file_min,'last_date_utc':file_max,'size_bytes':z.getinfo(name).file_size})
        print(f'[{fi}/{len(members)}] {src:15s} {file_year}: {nfile:,} total; {ntype0:,} vegetation; dup {file_dups}',flush=True)

    def ctr_df(counter,names):
      return pd.DataFrame([list(k)+[v] for k,v in counter.items()],columns=names+['count']) if counter else pd.DataFrame(columns=names+['count'])
    fdf=pd.DataFrame(file_stats).sort_values(['sensor','filename_year'])
    fdf.to_csv(tables/'file_inventory.csv',index=False)
    ctr_df(source_type,['source','type']).to_csv(tables/'type_distribution.csv',index=False)
    ctr_df(source_conf,['source','confidence']).to_csv(tables/'confidence_distribution.csv',index=False)
    ctr_df(source_dn,['source','daynight']).to_csv(tables/'daynight_distribution.csv',index=False)
    ctr_df(source_version,['source','version']).to_csv(tables/'versions.csv',index=False)
    ctr_df(version_by_year,['year','version']).to_csv(tables/'modis_version_by_year.csv',index=False)
    ctr_df(satellite_count,['source','satellite']).to_csv(tables/'satellite_values.csv',index=False)
    ctr_df(source_year_all,['source','year']).to_csv(tables/'annual_all_types.csv',index=False)
    ctr_df(by_hour,['source','hour_utc']).to_csv(tables/'hourly_type0.csv',index=False)
    mkeys={(s,y,m) for s,y,m,field in by_month}
    monthly_df=pd.DataFrame([{'source':s,'year':y,'month':m,'date_month':f'{y}-{m:02d}',
                              'type0_count':by_month[(s,y,m,'count')], 'frp_sum_mw':round(by_month[(s,y,m,'frp_sum')],2)} for s,y,m in sorted(mkeys)])
    monthly_df.to_csv(tables/'monthly_type0.csv',index=False)
    daily_keys={(s,d) for s,d,field in by_day}
    daily_df=pd.DataFrame([{'source':s,'date_utc':d,'type0_count':by_day[(s,d,'count')], 'frp_sum_mw':round(by_day[(s,d,'frp_sum')],2)} for s,d in sorted(daily_keys)])
    daily_df.to_csv(tables/'daily_type0.csv',index=False)
    annual_df=monthly_df.groupby(['source','year'],as_index=False).agg(type0_count=('type0_count','sum'),frp_sum_mw=('frp_sum_mw','sum'),active_months=('month','nunique'))
    annual_df.to_csv(tables/'annual_type0.csv',index=False)
    grid_df=ctr_df(grid_year,['source','year','lat_grid','lon_grid'])
    grid_df.to_csv(tables/'spatial_grid_0p5deg_type0_by_year.csv',index=False)
    by_month_grid=ctr_df(grid_2019_month,['source','month','lat_grid','lon_grid'])
    by_month_grid.to_csv(tables/'spatial_grid_2019_monthly_MODIS_SNPP.csv',index=False)
    null_df=ctr_df(nulls,['source','column']).rename(columns={'count':'null_count'})
    null_df['total_records']=null_df.apply(lambda r:counts_per_field[(r['source'],r['column'])],axis=1)
    null_df['null_pct']=100*null_df['null_count']/null_df['total_records']
    null_df.to_csv(tables/'missingness_by_source_column.csv',index=False)
    inv_df=ctr_df(invalid,['source','check'])
    inv_df.to_csv(tables/'validity_checks.csv',index=False)
    frp_stats=[]
    for source,blocks in frp_values.items():
      v=np.concatenate(blocks)
      pts=np.quantile(v,[0,.01,.05,.25,.5,.75,.9,.95,.99,1.0])
      frp_stats.append({'source':source,'n_type0':len(v),'frp_mean_mw':float(np.mean(v,dtype=np.float64)),'frp_sum_mw':float(np.sum(v,dtype=np.float64)),
        **{f'frp_p{p:02d}_mw':float(val) for p,val in zip([0,1,5,25,50,75,90,95,99,100],pts)},'zero_frp_n':int(np.count_nonzero(v==0))})
    pd.DataFrame(frp_stats).sort_values('source').to_csv(tables/'frp_type0_stats.csv',index=False)
    modis_c=np.concatenate(modis_conf) if modis_conf else np.array([])
    conf_summary={'modis_type0_confidence_n_numeric':int(np.isfinite(modis_c).sum()),'modis_type0_confidence_quantiles':{str(p):float(np.nanpercentile(modis_c,p)) for p in [0,10,25,50,75,90,100]} if len(modis_c) else {},'invalid_confidence_numeric':int(np.isnan(modis_c).sum())}
    json.dump(sample_spots,open(tables/'sample_spots.json','w'),indent=2)
    summary={
      'data_zip':zip_path.name, 'total_csv_files_in_zip':len(members),'indonesia_csv_files':len(file_stats),'excluded_files':excluded,
      'all_indonesia_records':all_records,'records_by_source':dict(source_n),'type0_total':int(sum(source_type[(s,'0')] for s in SRC.values())),
      'type_counts_overall':{str(t):int(sum(source_type[(s,str(t))] for s in SRC.values())) for t in (0,1,2,3)},
      'schemas':schemas,'schema_drift':schema_drift,'bounding_box_for_screening_only':BBOX,
      'duplicate_full_rows_within_each_file':int(fdf['duplicate_full_rows_within_file'].sum()),
      'first_last_date_by_source':{s:{'first':min(d),'last':max(d),'days_with_at_least_one_detection_all_types':len(d)} for s,d in dates_by_source.items()},
      'invalid_counts':{f'{s} | {check}':int(c) for (s,check),c in invalid.items()},
      'confidence_notes':conf_summary,
      'cautions':['Source records are pixel-level thermal detections, not unique fires nor confirmed forest fires.',
                  'type=0 means presumed vegetation fire, not confirmed fire origin.',
                  'Sensor counts and FRP values are not intrinsically comparable across MODIS and VIIRS.',
                  'Dates and acquisition times are UTC. Empty day means no records, not proof of no fires.',
                  'Bounding-box check does not verify Indonesia land polygons or province membership.',
                  'Dataset does not label deliberate ignition or natural ignition, no arson model labels.',
                  'Exact full-row hashes within-file checked, no cross-sensor event deduplication attempted.']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf8')
    print('DONE:',json.dumps({k:summary[k] for k in ('all_indonesia_records','records_by_source','type0_total','duplicate_full_rows_within_each_file')},ensure_ascii=False))
    return summary

if __name__=='__main__':
    zpath=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/data.zip')
    out=Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/vestigium_eda')
    analyze(zpath,out)
