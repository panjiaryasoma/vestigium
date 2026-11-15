#!/usr/bin/env python3
"""Reproducible maps and charts from the *observed* VESTIGIUM grids."""
import json
from pathlib import Path
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'
FIG=ROOT/'figures';FIG.mkdir(exist_ok=True)
coast=gpd.read_file(ROOT/'reference/indonesia_coarse_naturalearth_110m.geojson')
m=pd.read_csv(OUT/'monthly_grid_025deg.csv')

# 1) Dynamic spatial observation map (2015 September, S-NPP); not individual fires
s=m[(m.year==2015)&(m.month==9)&(m.sensor=='VIIRS_SNPP')]
fig,ax=plt.subplots(figsize=(15,7),dpi=160)
coast.plot(ax=ax,facecolor='#181B20',edgecolor='#68717B',linewidth=.55,zorder=0)
p=ax.scatter(s.grid_center_lon,s.grid_center_lat,c=np.log1p(s.detection_count),
             s=5+np.sqrt(s.detection_count)*1.6,cmap='inferno',alpha=.86,linewidths=0,zorder=1)
ax.set(xlim=(94,142),ylim=(-12,8),xlabel='Longitude (°E)',ylabel='Latitude (°N)')
ax.set_title('Indonesia | VIIRS S-NPP hotspot detections | September 2015',fontsize=15)
cbar=fig.colorbar(p,ax=ax,shrink=.68,pad=.012)
cbar.set_label('log(1 + vegetation-type detections per 0.25° cell)')
ax.text(.01,.02,'NASA FIRMS • pixel detections, not distinct fire events or burned area',
        transform=ax.transAxes,fontsize=9)
fig.tight_layout()
fig.savefig(FIG/'01_spatial_hotspots_2015_09.png',bbox_inches='tight')
plt.close(fig)

# 2) Side-by-side counts, no false claim that VIIRS vs MODIS directly comparable
s=m[(m.year==2015)&(m.month==9)]
t=s.groupby('sensor',as_index=False)['detection_count'].sum().sort_values('sensor')
fig,ax=plt.subplots(figsize=(10,4.5),dpi=160)
ax.barh(t.sensor,t.detection_count)
for i,n in enumerate(t.detection_count):ax.text(n+1000,i,f'{int(n):,}',va='center',fontsize=9)
ax.set_xlim(0,max(t.detection_count)*1.24)
ax.set_xlabel('Raw satellite detections (NOT calibrated across sensors)')
ax.set_title('September 2015: sensor-specific counts')
ax.grid(axis='x',alpha=.2)
fig.tight_layout();fig.savefig(FIG/'02_raw_sensor_counts_2015_09.png',bbox_inches='tight');plt.close(fig)

# 3) Spatial overlap indicators; count shared grid-month observations not shared fires
p=pd.read_csv(OUT/'sensor_comparison_025deg_raw.csv')
p=p[p.year>=2012]
summary=pd.DataFrame({'sensors':['MODIS','VIIRS_SNPP','VIIRS_NOAA20'],
                      'positive_cells':[(p[col]>0).sum() for col in ['MODIS','VIIRS_SNPP','VIIRS_NOAA20']]})
fig,ax=plt.subplots(figsize=(9,4.5),dpi=160)
ax.bar(summary.sensors,summary.positive_cells)
ax.set_ylabel('Sensor-month-grid cells with >= 1 detection')
ax.set_title('Observation coverage in monthly 0.25° cells (2012–2025)')
ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(FIG/'03_month_grid_observation_coverage.png',bbox_inches='tight');plt.close(fig)

# 4) recurrence: years of detection (not repeated individual fire events)
r=pd.read_csv(OUT/'recurrence_025deg_by_sensor.csv')
fig,ax=plt.subplots(figsize=(10,4.5),dpi=160)
for name in ['MODIS','VIIRS_SNPP','VIIRS_NOAA20']:
    x=r[r.sensor.eq(name)].distinct_years_with_detections
    vals=x.value_counts().sort_index()
    ax.plot(vals.index,vals.values,marker='o',markersize=2.3,linewidth=1.4,label=name)
ax.set(xlabel='Years with >= 1 detection in cell',ylabel='Number of 0.25° cells',title='Spatial recurrence of satellite observations')
ax.legend();ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(FIG/'04_years_with_detections.png',bbox_inches='tight');plt.close(fig)

# 5) high-level grid-zoom hierarchy (monthly 2015 Sep SNPP)
fig,ax=plt.subplots(figsize=(10,5),dpi=160)
labels=[];values=[]
for res,pth in [('1.0°','monthly_grid_1deg.csv'),('0.5°','monthly_grid_05deg.csv'),('0.25°','monthly_grid_025deg.csv'),('0.1°','monthly_grid_01deg.csv')]:
    x=pd.read_csv(OUT/pth,usecols=['year','month','sensor','detection_count'])
    y=x[(x.year==2015)&(x.month==9)&(x.sensor=='VIIRS_SNPP')]
    labels.append(res);values.append(len(y))
ax.bar(labels,values)
ax.set(xlabel='Geographic cell size',ylabel='Occupied grid cells',title='Multi-resolution map index: September 2015 VIIRS S-NPP')
ax.grid(axis='y',alpha=.2)
fig.tight_layout();fig.savefig(FIG/'05_map_grid_resolution.png',bbox_inches='tight');plt.close(fig)

# 6) interactive proof of concept with tooltips, top 1,250 grids by count, not all records
try:
 import folium
 x=m[(m.year==2015)&(m.month==9)&(m.sensor=='VIIRS_SNPP')].nlargest(1250,'detection_count')
 f=folium.Map(location=[-2.0,117.0],zoom_start=5,tiles='CartoDB dark_matter',control_scale=True)
 for _,row in x.iterrows():
    folium.CircleMarker(
        [float(row.grid_center_lat),float(row.grid_center_lon)],
        radius=max(2,min(8,float(np.sqrt(row.detection_count)*.45))),
        color='#C53D34',fill=True,fill_color='#E94B3C',fill_opacity=.75,weight=.6,
        tooltip=f"2015-09 · VIIRS S-NPP<br>0.25° cell ({int(row.grid_x)}, {int(row.grid_y)})<br>{int(row.detection_count):,} satellite detections"
    ).add_to(f)
 f.get_root().html.add_child(folium.Element('<!-- TOP 1,250 OCCUPIED GRIDS ONLY; NOT ALL DETECTIONS; map tiles require internet -->'))
 f.save(str(FIG/'06_interactive_map_preview_2015_09.html'))
except ImportError:pass
print('created',len(list(FIG.iterdir())),'spatial figure files')
