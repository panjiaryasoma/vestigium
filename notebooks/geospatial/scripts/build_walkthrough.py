#!/usr/bin/env python3
"""Create and execute an English scientific walkthrough from archived outputs."""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

root=Path(__file__).resolve().parents[1]
nb_dir=root/'notebooks';nb_dir.mkdir(exist_ok=True)
nb=nbf.v4.new_notebook()
nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
nb.metadata.language_info={'name':'python','version':'3'}
C=[]
def M(s):C.append(nbf.v4.new_markdown_cell(s))
def P(s):C.append(nbf.v4.new_code_cell(s))

M('''# VESTIGIUM | Advanced Geospatial Preprocessing Walkthrough

**NASA Space Apps Challenge 2026 · Team Ga Tidur**  
**Indonesia, 2000–2025 | MODIS + VIIRS S-NPP + VIIRS NOAA-20**

This reproducible notebook reviews the **executed** geospatial engineering outputs. It does not train a machine learning model and does not establish wildfire ignition causes. All observations are source pixel detections. Complete pipeline source is in `scripts/run_advanced.py`.''')
M('''## 1. Objective and research limits

- Make Indonesia-wide hotspots viewable at multiple map zoom levels without loading millions of points at once.
- Retain individual pixel observations in the prior Data Engineering SQLite store; the present workflow adds grid-level outputs.
- Build a consistent **sensor × UTC period × cell** data contract.
- Create equal-area projected cells for later spatial analyses.
- Check detection conservation before modeling.
- **Do not** interpret sensor counts as distinct wildfires, burned area, or arson evidence.''')
P('''from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from IPython.display import display

ROOT = Path.cwd().parent
OUT = ROOT / 'outputs'
FIG = ROOT / 'figures'
assert OUT.exists(), 'Run from the notebooks/ folder with outputs/ present'
qa = json.loads((OUT / 'geospatial_quality_report.json').read_text())
print('Archive:', Path(qa['source_zip']).name)
print('Files:', qa['raw_sensor_files'])
print('Accepted type=0:', f"{qa['accepted_type0']:,}")
print('QA:', qa['data_quality'])''')
M('''## 2. Data lineage and source granularity

The archived `data.zip` contains 48 Indonesia CSVs plus an unrelated 2003 Angola CSV. Only source paths ending `_Indonesia.csv` within the recognized MODIS and VIIRS folders are processed. Following source validation, only `type=0` presumed-vegetation detections are aggregated. The earlier Data Engineering stage provides the original 0.25° and individual-detection SQLite outputs.''')
P('''display(pd.DataFrame([{'sensor':k, 'retained_pixel_detections':v} for k,v in qa['by_sensor'].items()]).sort_values('sensor'))
assert sum(qa['by_sensor'].values()) == qa['accepted_type0']''')
M('''## 3. Projection, spatial support, and units

The 0.1° geographic grid is anchored globally at (-180°, -90°). The 0.25°, 0.5°, and 1.0° layers are aligned to the earlier 0.25° stage's origin (94°E, 12°S). **Cell indexes from different origins cannot be joined directly.** The 25-km analytical grid uses `EPSG:6933`, with 25,000-meter projected squares. These are areas of observation bins, **not** burned-area estimates.''')
P('''rows=[]
for name,a in qa['grid_outputs'].items():
    rows.append({'output':name,'occupied_rows':a['rows'],'total_detections':a.get('detections',pd.NA)})
display(pd.DataFrame(rows))''')
M('''## 4. Conservation across spatial resolutions

The strongest quantitative integrity test is that every grid conserves the accepted **source pixel count**, even when cell size changes. The table below compares actual output totals and marks violations.''')
P('''expected=qa['accepted_type0']
checks=[]
for name in ['monthly_grid_01deg','monthly_grid_025deg','monthly_grid_05deg','monthly_grid_1deg','monthly_equal_area_25km']:
    x=qa['grid_outputs'][name]['detections']
    checks.append({'output':name,'observations':x,'matches_source':x==expected})
display(pd.DataFrame(checks))
assert all(x['matches_source'] for x in checks)''')
M('''## 5. Example geographical observation map

The map below shows **September 2015 VIIRS S-NPP observations aggregated into 0.25° cells**. It is not a map of burned hectares or separate wildfires. Coastline outlines are low-resolution and cannot validate individual Indonesian islands.''')
P('''from IPython.display import Image
Image(filename=str(FIG/'01_spatial_hotspots_2015_09.png'), width=900)''')
M('''## 6. Sensor availability and resolution are not equal

MODIS and VIIRS have different detection sensitivities and spatial resolutions. A raw sensor comparison, even when using the same month and grid, is not harmonization. Sensor availability changes over time and a zero does not indicate verified no fire.''')
P('''comparison=pd.read_csv(OUT/'sensor_comparison_025deg_raw.csv')
assert {'MODIS','VIIRS_SNPP','VIIRS_NOAA20'}.issubset(comparison.columns)
comparison_2015=comparison[(comparison.year==2015)&(comparison.month==9)]
display(pd.DataFrame({'sensor':['MODIS','VIIRS_SNPP','VIIRS_NOAA20'],
                     'raw_detections':[comparison_2015[x].sum() for x in ['MODIS','VIIRS_SNPP','VIIRS_NOAA20']]}))
print('Rows with > 1 sensor recording a detection:', int(((comparison_2015[['MODIS','VIIRS_SNPP','VIIRS_NOAA20']]>0).sum(axis=1)>1).sum()))''')
M('''## 7. How coarser and finer grids alter map density

A finer grid produces more occupied cells without changing the underlying sum of detections. Thus changing map zoom must not change the total represented detection count.''')
P('''Image(filename=str(FIG/'05_map_grid_resolution.png'), width=800)''')
M('''## 8. Equal-area 25-km projected cells

The equal-area product is calculated **from individual points** in WGS84, projected to `EPSG:6933`, and assigned to 25-km squares. Inverse projection is used only for their map label centers. This avoids claiming that angular 0.1° bins have equal surface area.''')
P('''ea=pd.read_csv(OUT/'monthly_equal_area_25km.csv', nrows=5)
display(ea[['sensor','year','month','cell_x','cell_y','detection_count','center_longitude','center_latitude']])''')
M('''## 9. Repeated detection locations, not repeated fire events

For every 0.25° cell and sensor, a recurrence feature counts the number of different years containing ≥1 accepted pixel detection. This **does not prove** the same physical fire recurred, the land burned in each year, or any ignition cause.''')
P('''recurrence=pd.read_csv(OUT/'recurrence_025deg_by_sensor.csv')
display(recurrence.sort_values(['distinct_years_with_detections','total_detection_count'],ascending=False).head(10))
Image(filename=str(FIG/'04_years_with_detections.png'),width=750)''')
M('''## 10. National boundary sanity diagnostic is intentionally non-destructive

A Natural Earth 1:110m country polygon is **too coarse** to verify an individual Indonesian hotspot centroid near small islands and coastlines. Only a diagnostic sample is tested. Points outside that outline are neither dropped nor labeled as non-Indonesian.''')
P('''display(pd.DataFrame([qa['national_boundary_diagnostic']]))
print('Province spatial join status:',qa['spatial_join_adm1'])''')
M('''## 11. Hover prototype records (true pixel samples)

At an individual zoom level, users should hover/click *pixel-center observations* containing coordinates, UTC acquisition date/time, sensor, satellite and raw confidence. **A month-grid centroid does not represent an exact active-fire pixel.** The sample below is a deterministic interface test subset of September 2015, not a sampling frame for inference.''')
P('''hover=pd.read_csv(OUT/'example_hover_points_2015_09.csv')
print('Demo points:',f"{len(hover):,}")
display(hover.head(8))''')
M('''## 12. Source-specific confidence and observation effort

MODIS confidence values are percentages. VIIRS confidence classes are ordinal labels (`l/n/h`) and must not be mapped directly to the same numeric 0–100 scale. Model training must also account for satellite availability, orbital overpasses, cloud visibility, algorithm version changes, and source observation bias.''')
M('''## 13. QA verdict and limitations

**Passed:** 48 expected Indonesia source files, exclusion of the Angola filename, agreement with earlier accepted counts, pixel-count conservation in five spatial grid products, and spatial indexing unit tests.

**Not completed:** accurate province-by-province point-in-polygon assignments (no suitable authoritative boundary input), proven harmonization of MODIS and VIIRS, validated classification of natural vs intentional fire, or post-fire land-cover interpretation. The optional script `assign_provinces_optional.py` must be run with sourced ADM1 polygons and independently checked.''')
P('''assert qa['data_quality']['agrees_with_baseline'] and qa['data_quality']['agrees_with_all_grids']
print('FINAL QA: PASS (geospatial aggregation conservation)')
print('HARMONIZATION: NOT TRAINED')
print('PROVINCE ASSIGNMENT: NOT RUN')''')
M('''## 14. Next stage

Start a **MODIS–VIIRS harmonization benchmark** on aligned grid-months and overlapping sensor years. Evaluate against simple statistical baselines with held-out time windows/regions; include uncertainty and explicit observation-coverage limitations. In parallel, connect zoom-dependent grid outputs and the earlier SQLite point store to the MapLibre/React interface. Maintain clear attribution and provenance for all data sources.''')
nb.cells=C
src=nb_dir/'VESTIGIUM_ADVANCED_GEOSPATIAL.ipynb'
out=nb_dir/'VESTIGIUM_ADVANCED_GEOSPATIAL_EXECUTED.ipynb'
nbf.write(nb,src)
client=NotebookClient(nb,timeout=90,kernel_name='python3',resources={'metadata':{'path':str(nb_dir)}})
executed=client.execute()
nbf.write(executed,out)
print('Notebook cells',len(nb.cells),'source',src,'executed',out)
