#!/usr/bin/env python3
"""Render VESTIGIUM FIRMS EDA plots from processed aggregations; no heavy raw reload."""
from pathlib import Path
import json, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import FuncFormatter, MaxNLocator

ROOT=Path(__file__).resolve().parent
T=ROOT/'tables'; F=ROOT/'figures';F.mkdir(exist_ok=True)
M=pd.read_csv(T/'monthly_type0.csv');A=pd.read_csv(T/'annual_type0.csv');DA=pd.read_csv(T/'daily_type0.csv');TY=pd.read_csv(T/'type_distribution.csv');FR=pd.read_csv(T/'frp_type0_stats.csv');DN=pd.read_csv(T/'daynight_distribution.csv');CONF=pd.read_csv(T/'confidence_distribution.csv');G=pd.read_csv(T/'spatial_grid_0p5deg_type0_by_year.csv');VER=pd.read_csv(T/'modis_version_by_year.csv')
BG='#0e1012'; AX='#181b1f'; FG='#eae5dc'; MUT='#aaa49a';GRID='#3b4046'
CO={'MODIS':'#f46b57','VIIRS S-NPP':'#a1b6c4','VIIRS NOAA-20':'#d6ac73'}
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':AX,'axes.labelcolor':FG,'axes.edgecolor':'#656b72','xtick.color':MUT,'ytick.color':MUT,'text.color':FG,'font.size':10,'axes.titlesize':15,'axes.titleweight':'bold','grid.alpha':.15,'savefig.facecolor':BG,'figure.dpi':110})
def finish(fig,ax,fname,subtitle=None):
    if subtitle:fig.text(.08,.04,subtitle,fontsize=9,color=MUT)
    for a in (ax if isinstance(ax,(list,np.ndarray)) else [ax]):
      if hasattr(a,'spines'):
        a.spines[['top','right']].set_visible(False)
    fig.savefig(F/fname,bbox_inches='tight',dpi=130)
    plt.close(fig)
def fmt(x,pos):return f'{x/1e6:.1f}M' if abs(x)>=1e6 else f'{x/1e3:.0f}K' if abs(x)>=1000 else f'{x:g}'

for src,label,idx in [('MODIS','MODIS',1),('VIIRS S-NPP','VIIRS S-NPP',2),('VIIRS NOAA-20','VIIRS NOAA-20',3)]:
  d=A[A.source==src].sort_values('year');fig,ax=plt.subplots(figsize=(10.5,4.6))
  ax.bar(d.year,d.type0_count,color=CO[src],width=.78,alpha=.90)
  ax.set_title(f'{label}: presumed vegetation fire detections by year',loc='left',pad=17)
  ax.set_xlabel('Year (UTC)');ax.set_ylabel('Pixel detections (type = 0)')
  ax.yaxis.set_major_formatter(FuncFormatter(fmt));ax.grid(axis='y');ax.set_axisbelow(True)
  ax.set_xticks(d.year[::(2 if src=='MODIS' else 1)]);ax.tick_params(axis='x',rotation=30)
  peak=d.loc[d.type0_count.idxmax()];ax.annotate(f"Peak {int(peak.year)}: {int(peak.type0_count):,}",xy=(peak.year,peak.type0_count),xytext=(peak.year-1,peak.type0_count*1.13),arrowprops={'arrowstyle':'-','color':MUT},color=FG)
  ax.set_ylim(0,d.type0_count.max()*1.28)
  finish(fig,ax,f'{idx:02d}_annual_{src.replace(" ","_").replace("-","_")}.png',('Only Nov–Dec 2000 available; product changes may affect long-term comparisons.' if src=='MODIS' else 'Detection counts are not burned area and are not directly comparable across sensors.'))

for src,idx in [('MODIS',4),('VIIRS S-NPP',5)]:
  d=M[M.source==src];pivot=d.pivot(index='year',columns='month',values='type0_count').reindex(columns=range(1,13))
  from matplotlib.colors import LogNorm
  fig,ax=plt.subplots(figsize=(10.5,6.4)); vv=pivot.to_numpy(dtype=float);masked=np.ma.masked_invalid(vv)
  im=ax.imshow(masked,aspect='auto',cmap='inferno',norm=LogNorm(vmin=1,vmax=max(10,int(np.nanmax(vv)))))
  ax.set_yticks(range(len(pivot)),labels=pivot.index);ax.set_xticks(range(12),labels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
  ax.set_title(f'Monthly hotspot calendar: {src}',loc='left',pad=18)
  cb=fig.colorbar(im,ax=ax,pad=.02,shrink=.88);cb.set_label('Detections per month (log scale)',color=FG);cb.ax.tick_params(colors=MUT)
  fig.text(.08,.03,'Blank cells indicate missing records, not proof of zero fires.',color=MUT,fontsize=9)
  finish(fig,ax,f'{idx:02d}_calendar_{src.replace(" ","_")}.png')

# Seasonality: each complete year contributes monthly shares, then average, not sensor-count comparisons.
fig,ax=plt.subplots(figsize=(10.5,4.8))
for src,start in [('MODIS',2001),('VIIRS S-NPP',2013),('VIIRS NOAA-20',2019)]:
  d=M[(M.source==src)&(M.year>=start)].copy();d['year_sum']=d.groupby('year')['type0_count'].transform('sum');d['share']=100*d.type0_count/d.year_sum
  s=d.groupby('month').share.mean().reindex(range(1,13))
  ax.plot(s.index,s.values,'-o',label=src,color=CO[src],linewidth=2,markersize=4)
ax.set_title('Seasonality: average monthly share of annual detections',loc='left',pad=17)
ax.set_ylabel('Mean monthly share of annual detections (%)');ax.set_xlabel('Month');ax.set_xticks(range(1,13),['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']);ax.grid(axis='y');ax.legend(facecolor=AX,labelcolor=FG)
finish(fig,ax,'06_seasonality_share.png','Each year is normalized to 100%. These shares do not measure fire intensity.')

fig,ax=plt.subplots(figsize=(10.5,4.9));ty=TY.pivot(index='source',columns='type',values='count').fillna(0).reindex(['MODIS','VIIRS S-NPP','VIIRS NOAA-20']); tot=ty.sum(axis=1)
left=np.zeros(len(ty));colors=['#f46b57','#c6a46c','#879a9a','#746a79'];lab=['0: presumed vegetation fire','1: volcanic','2: static heat source','3: offshore']
for c,color,l in zip([0,1,2,3],colors,lab):
  vals=100*ty[c]/tot;ax.barh(np.arange(len(ty)),vals,left=left,color=color,label=l,height=.58);left+=vals.to_numpy()
ax.set_yticks(np.arange(len(ty)),ty.index);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Share of all records (%)');ax.set_title('Thermal anomaly categories (type)',loc='left',pad=18)
ax.legend(loc='lower center',bbox_to_anchor=(.5,-.42),ncol=2,facecolor=AX,labelcolor=FG)
finish(fig,ax,'07_type_mix_by_sensor.png','Type 0 is a presumed vegetation fire detection, not a confirmed forest fire.')

fig,ax=plt.subplots(figsize=(10.5,4.6));dn=DN.pivot(index='source',columns='daynight',values='count').fillna(0).reindex(['MODIS','VIIRS S-NPP','VIIRS NOAA-20']);w=np.arange(len(dn));dshare=100*dn['D']/(dn['D']+dn['N'])
ax.barh(w,dshare,color='#d6ac73',height=.58,label='Day (D)');ax.barh(w,100-dshare,left=dshare,color='#8196ac',height=.58,label='Night (N)');ax.set_yticks(w,dn.index);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('Share of sensor records (%)');ax.set_title('Daytime versus nighttime detections',loc='left',pad=17);ax.legend(facecolor=AX,labelcolor=FG)
finish(fig,ax,'08_day_night_mix.png','Day/night reflects satellite acquisition time, not fire duration.')

fig,ax=plt.subplots(figsize=(10.5,5.2));f=FR.set_index('source').reindex(['MODIS','VIIRS S-NPP','VIIRS NOAA-20'])
xs=np.arange(3);p25=f['frp_p25_mw'].values;med=f['frp_p50_mw'].values;p75=f['frp_p75_mw'].values;p95=f['frp_p95_mw'].values
for j,src in enumerate(f.index):
 ax.plot([xs[j],xs[j]],[p25[j],p75[j]],color=CO[src],linewidth=14,solid_capstyle='butt')
 ax.plot([xs[j],xs[j]],[p75[j],p95[j]],color=CO[src],linewidth=2,alpha=.8)
 ax.scatter([xs[j]],[med[j]],s=75,marker='o',c=FG,zorder=5)
ax.set_yscale('log');ax.set_ylabel('FRP (MW, logarithmic scale)');ax.set_xticks(xs,f.index);ax.set_title('Type-0 FRP: median, IQR, and 95th percentile',loc='left',pad=18);ax.grid(axis='y')
finish(fig,ax,'09_frp_quantiles.png','White dot: median; thick line: P25–P75; thin line: up to P95. Sensors are not equivalent.')

conf=CONF[CONF.source.str.startswith('VIIRS')].copy(); p=conf.pivot(index='source',columns='confidence',values='count').fillna(0).reindex(['VIIRS S-NPP','VIIRS NOAA-20']); fig,ax=plt.subplots(figsize=(9.8,4.6)); pos=np.arange(len(p));bottom=np.zeros(len(p))
for k,c,label in [('l','#d6ac73','Low'),('n','#91a8ba','Nominal'),('h','#f46b57','High')]:
 vals=100*p[k].to_numpy()/p.sum(axis=1).to_numpy();ax.bar(pos,vals,bottom=bottom,color=c,width=.48,label=label);bottom+=vals
ax.set_xticks(pos,p.index);ax.set_ylabel('Share of VIIRS records (%)');ax.set_ylim(0,100);ax.set_title('VIIRS confidence classes',loc='left',pad=16);ax.legend(facecolor=AX,labelcolor=FG)
finish(fig,ax,'10_viirs_confidence.png','MODIS uses numeric 0–100 confidence; it is not equivalent to VIIRS l/n/h.')

for src,year,idx in [('VIIRS S-NPP',2015,11),('VIIRS S-NPP',2019,12)]:
 d=G[(G.source==src)&(G.year==year)].copy(); fig,ax=plt.subplots(figsize=(12,5.2))
 im=ax.scatter(d.lon_grid+.25,d.lat_grid+.25,c=d['count'],s=np.clip(np.sqrt(d['count'].to_numpy())*1.15,2,55),cmap='inferno',norm=LogNorm(vmin=1,vmax=d['count'].max()),marker='s',linewidths=0)
 ax.set_xlim(94,142);ax.set_ylim(-12,7);ax.set_xlabel('Longitude (°E)');ax.set_ylabel('Latitude (°)');ax.set_aspect('equal',adjustable='box');ax.set_title(f'Detection density on a 0.5° × 0.5° grid: {src}, {year}',loc='left',pad=18)
 cb=fig.colorbar(im,ax=ax,pad=.02,shrink=.78);cb.set_label('Detections per grid cell (log)',color=FG);cb.ax.tick_params(colors=MUT)
 ax.grid(alpha=.1)
 finish(fig,ax,f'{idx:02d}_spatial_density_{year}.png','No administrative boundaries or coastline; grid counts do not measure burned area.')

# Normalized 2015 within-sensor shape. Do not imply true fire counts comparable.
d=M[M.year==2015];fig,ax=plt.subplots(figsize=(10.5,4.8))
for src in ['MODIS','VIIRS S-NPP']:
 g=d[d.source==src].sort_values('month');pct=100*g.type0_count/g.type0_count.sum();ax.plot(g.month,pct,'-o',linewidth=2,markersize=4,color=CO[src],label=src)
ax.set_title('Comparison of normalized 2015 monthly profiles',loc='left',pad=17);ax.set_ylabel('Within-sensor share of annual detections (%)');ax.set_xticks(range(1,13),['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']);ax.grid(axis='y');ax.legend(facecolor=AX,labelcolor=FG)
finish(fig,ax,'13_normalized_2015_sensor_comparison.png','Similar monthly profiles do not establish equal coverage, locations, or fire incidents.')

fig,ax=plt.subplots(figsize=(10.5,4.8));vv=VER.pivot(index='year',columns='version',values='count').fillna(0);bottom=np.zeros(len(vv));color={'6.2':'#c2ad88','6.03':'#8196ac','61.03':'#f46b57'}
for ver in vv.columns:
 vals=vv[ver].values;ax.bar(vv.index,vals,bottom=bottom,color=color.get(str(ver),'#bbbbbb'),label=str(ver));bottom+=vals
ax.set_title('MODIS version-field values in the supplied archive',loc='left',pad=17);ax.set_ylabel('All detections');ax.yaxis.set_major_formatter(FuncFormatter(fmt));ax.legend(title='Input version',facecolor=AX,labelcolor=FG)
finish(fig,ax,'14_modis_versions.png','Version changes must be checked against source metadata and processing history.')

# Month-by-month 2019 raw counts: lines distinct, not merged.
fig,ax=plt.subplots(figsize=(10.5,4.8)); d=M[M.year==2019]
for src in ['MODIS','VIIRS S-NPP','VIIRS NOAA-20']:
 s=d[d.source==src];ax.plot(s.month,s.type0_count,'-o',color=CO[src],label=src,markersize=4,linewidth=2)
ax.set_title('Three sensors in 2019: raw monthly detection counts',loc='left',pad=17);ax.set_ylabel('Number of type-0 pixel detections');ax.set_xlabel('Month (UTC)');ax.set_xticks(range(1,13));ax.yaxis.set_major_formatter(FuncFormatter(fmt));ax.grid(axis='y');ax.legend(facecolor=AX,labelcolor=FG)
finish(fig,ax,'15_raw_2019_comparison.png','Cross-sensor count differences are the harmonization problem, not unique-fire counts.')

# Peak days by source
fig,ax=plt.subplots(figsize=(10.5,5.3));d=DA[DA.source=='VIIRS S-NPP'].nlargest(12,'type0_count').sort_values('type0_count');ax.barh(d.date_utc,d.type0_count,color=CO['VIIRS S-NPP']);ax.xaxis.set_major_formatter(FuncFormatter(fmt));ax.set_title('Twelve highest-count VIIRS S-NPP dates',loc='left',pad=18);ax.set_xlabel('Type-0 detections by UTC date')
finish(fig,ax,'16_peak_dates_snpp.png','The highest detection-count days are not the 12 largest fire incidents.')

# Spatial intersection monthly 2019 coarse grid (presence).
GG=pd.read_csv(T/'spatial_grid_2019_monthly_MODIS_SNPP.csv');rows=[]
for mo in range(1,13):
  a=set(zip(GG.loc[(GG.source=='MODIS')&(GG.month==mo),'lat_grid'],GG.loc[(GG.source=='MODIS')&(GG.month==mo),'lon_grid']))
  b=set(zip(GG.loc[(GG.source=='VIIRS S-NPP')&(GG.month==mo),'lat_grid'],GG.loc[(GG.source=='VIIRS S-NPP')&(GG.month==mo),'lon_grid']))
  union=a|b; intr=a&b
  rows.append({'month':mo,'modis_nonempty_grid_count':len(a),'snpp_nonempty_grid_count':len(b),'overlap_grid_count':len(intr),'union_grid_count':len(union),'jaccard_presence':len(intr)/len(union) if union else np.nan})
J=pd.DataFrame(rows);J.to_csv(T/'2019_monthly_spatial_grid_overlap.csv',index=False)
fig,ax=plt.subplots(figsize=(10.5,4.5));ax.plot(J.month,J.jaccard_presence,'-o',color='#f46b57',linewidth=2)
ax.set_title('2019: overlap of occupied 0.5° grid cells (MODIS vs S-NPP)',loc='left',pad=17);ax.set_xlabel('Month UTC');ax.set_ylabel('Occupied-grid Jaccard index (0–1)');ax.set_ylim(0,1);ax.set_xticks(range(1,13));ax.grid(axis='y')
finish(fig,ax,'17_spatial_overlap_grid2019.png','Coarse-grid co-occurrence is not same-time detection matching or model validation.')

# Peak month summary in table to let reader question chronology.
M.nlargest(25,'type0_count').to_csv(T/'top_25_months_by_source.csv',index=False)
DA.nlargest(25,'type0_count').to_csv(T/'top_25_days_by_source.csv',index=False)
print('Created',len(list(F.glob('*.png'))),'figures')
