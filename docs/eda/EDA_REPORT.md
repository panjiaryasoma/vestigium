# VESTIGIUM
## Comprehensive Exploratory Data Analysis (EDA) of Satellite Hotspot Detections in Indonesia, 2000–2025
**NASA Space Apps Challenge 2026 | Team Ga Tidur**

*Source: the user-supplied `data.zip`, analyzed from the original CSV files on 14 November 2026. Observation dates and times use UTC.*

> **Analysis status:** This is a descriptive EDA and data-quality assessment. **Sensor harmonization, fire-cause labels, burned-area estimates, and machine-learning models are NOT included.** Each record is a satellite-pixel thermal-anomaly detection, not a unique fire incident. `type=0` denotes a *presumed vegetation fire*, not a confirmed forest fire or evidence of deliberate ignition.

## 1. Objectives and research questions

This EDA supports the VESTIGIUM MVP: an interactive hotspot map with coordinate/date/FRP inspection, date filtering, monthly and annual summaries, and a foundation for MODIS–VIIRS harmonization. It examines: (i) whether input files satisfy the expected data contract; (ii) when detections concentrate; (iii) how their geographical distribution and pixel-level intensity vary; (iv) how far the sensors can be compared; and (v) which data-quality risks and additional datasets matter for responsible interpretation.

## 2. Dataset inventory and observational grain

One CSV row represents **one thermal-anomaly pixel detection on a satellite overpass**. Observations have not been deduplicated across satellites or overpasses. They are neither incident-level records nor burned-area measurements. There are **49 CSV files**, but `MODIS/modis_2003_Angola.csv` was excluded; the analysis covers **48 Indonesia CSV files**.

| Source | All detections | `type=0` | Share `type=0` | Observed UTC dates |
|---|---:|---:|---:|---|
| MODIS | 1,533,411 | 1,443,591 | 94.14% | 2000-11-01 to 2025-12-31 |
| VIIRS S-NPP | 3,514,520 | 3,350,961 | 95.35% | 2012-01-20 to 2025-12-31 |
| VIIRS NOAA-20 | 1,307,603 | 1,203,124 | 92.01% | 2018-04-01 to 2025-12-31 |

**Total:** 6,355,534 Indonesia detections, including **5,997,676 (94.37%)** records with `type=0` and **357,858 (5.63%)** of other types.

**Unequal temporal coverage:** MODIS starts 1 November 2000; VIIRS S-NPP starts 20 January 2012; and VIIRS NOAA-20 starts 1 April 2018. These initial years are **partial**. The uploaded archive has no NOAA-21 data. All included series end on 31 December 2025.

## 3. Data dictionary and attribute semantics

| Field | Meaning | Interpretation risk |
|---|---|---|
| `latitude`, `longitude` | Detection-pixel centroid, WGS 84 decimal degrees | Not an exact ignition coordinate or fire perimeter |
| `acq_date`, `acq_time` | Acquisition date and UTC hour/minute | Do not assume local Indonesian time; normalize HHMM first |
| `satellite`, `instrument` | Observing platform and instrument | Platform codes and product versions differ; retain provenance |
| `type` | 0 presumed vegetation; 1 volcanic; 2 static heat source; 3 offshore | `type=0` is not confirmed forest fire |
| `frp` | Pixel Fire Radiative Power, in MW | Not total energy, fire duration, or area in hectares |
| `confidence` | MODIS numeric 0–100; VIIRS `l/n/h` | Scales cannot be equated directly |
| `brightness`, `bright_t31` | MODIS brightness temperatures, K | Different channels from VIIRS |
| `bright_ti4`, `bright_ti5` | VIIRS brightness temperatures, K | Different channels/resolution from MODIS |
| `scan`, `track` | Observation pixel dimensions | May vary between observations |
| `daynight` | Day/night classification at acquisition | Does not measure how long a fire burned |
| `version` | Product/processing identifier | Product changes may introduce artificial discontinuities |

## 4. Preprocessing and validation approach

1. Read raw CSV files incrementally from the ZIP in chunks of 150,000 rows; retain source-file and sensor provenance.
2. Exclude the Angola file from the Indonesia analysis.
3. Separate all thermal-anomaly types from the primary `type=0` analysis.
4. Validate UTC date/time syntax, global coordinates, an approximate Indonesia bounding box, nonnegative FRP, accepted `type` codes, and filename-versus-record year agreement.
5. Check exact duplicates within each annual CSV using row hashes. This **does not** resolve physical duplicates across sensors or passes.
6. Build sensor-separated daily, monthly, yearly, and 0.5° spatial-grid aggregates.
7. Compute `type=0` FRP descriptive statistics from the full set of values, not a sampled subset.

**Not performed:** clipping to Indonesia administrative polygons, province attribution, human-versus-natural ignition labeling, conversion of FRP to burned area, or automatic filling of missing days with zero fire activity.

## 5. Data-quality assessment

- **Null values across inspected CSV fields:** 0 detected among the 6,355,534 records within the file/column checks.
- **Exact duplicates within individual files:** 0 detected.
- **Invalid dates, coordinate bounds, time fields, and FRP under implemented checks:** 0 detected.
- **Within-sensor schema drift:** 0 files flagged.
- **Geographical extent:** all checked coordinates lie inside the approximate box from latitude −12 to 6.5 and longitude 94 to 142. This is **not** a check against Indonesia's land territory.

**Methodological limitation:** Zero violations of these mechanical checks does not mean the satellite observations lack cloud/smoke bias, sensor errors, or repeated detections of the same physical fire. Polygon-based geospatial checks, satellite-product QA, and independent cross-validation remain necessary.

## 6. Annual detection history: MODIS

Variation in hotspot counts does **not** directly measure change in burned area. Within-sensor trends nevertheless reveal temporal variation worth investigating. The MODIS series spans 26 calendar years, with only November–December in 2000.

![Annual MODIS presumed vegetation fire detections.](figures/01_annual_MODIS.png)

*Annual number of MODIS `type=0` detections.*

**Five highest-count years in the supplied MODIS series:**

| Year | `type=0` detections |
|---:|---:|
| 2015 | 161,757 |
| 2006 | 147,458 |
| 2002 | 120,781 |
| 2014 | 108,038 |
| 2004 | 103,390 |

## 7. Annual detection history: VIIRS S-NPP and NOAA-20

VIIRS has a nominal 375 m fire-detection resolution, in contrast to approximately 1 km for MODIS. Higher VIIRS counts do not necessarily indicate more distinct fires. The first available years for S-NPP (2012) and NOAA-20 (2018) are incomplete.

![Annual VIIRS S-NPP presumed vegetation fire detections.](figures/02_annual_VIIRS_S_NPP.png)

*Annual number of VIIRS S-NPP `type=0` detections.*

![Annual VIIRS NOAA-20 presumed vegetation fire detections.](figures/03_annual_VIIRS_NOAA_20.png)

*Annual number of VIIRS NOAA-20 `type=0` detections.*

**Peak years by source:** MODIS **2015 (161,757)**; VIIRS NOAA-20 **2019 (420,220)**; VIIRS S-NPP **2015 (859,411)**.

## 8. Year-by-month hotspot calendars

The heatmaps highlight periods of concentrated detections for each sensor using logarithmic color scaling. A blank calendar cell should **not** automatically be interpreted as zero fires.

![Monthly MODIS heatmap, 2000–2025.](figures/04_calendar_MODIS.png)

*MODIS monthly detection calendar, 2000–2025.*

![Monthly VIIRS S-NPP heatmap, 2012–2025.](figures/05_calendar_VIIRS_S-NPP.png)

*VIIRS S-NPP monthly detection calendar, 2012–2025.*

**Ten highest-count sensor–month combinations:**

| Sensor | UTC month | Detections |
|---|---|---:|
| VIIRS S-NPP | 2015-10 | 318,931 |
| VIIRS S-NPP | 2015-09 | 292,886 |
| VIIRS S-NPP | 2019-09 | 195,047 |
| VIIRS NOAA-20 | 2019-09 | 194,004 |
| VIIRS S-NPP | 2014-10 | 125,800 |
| VIIRS S-NPP | 2014-09 | 125,056 |
| VIIRS S-NPP | 2015-08 | 118,886 |
| VIIRS S-NPP | 2012-09 | 98,870 |
| VIIRS S-NPP | 2019-10 | 82,555 |
| VIIRS NOAA-20 | 2019-10 | 81,459 |

## 9. Seasonality across calendar years

To reduce raw-count scale effects, each fully covered calendar year is normalized to 100% of that sensor's detections, and monthly shares are averaged across years. This characterizes seasonality; it is **not a correction for sensor detection bias**.

![Mean within-year monthly detection shares by source.](figures/06_seasonality_share.png)

*Mean monthly proportion of annual detections, using full years only.*

**August–October concentration in complete years:**

| Source | Full years | Median annual Aug–Oct share | Mean annual Aug–Oct share |
|---|---|---:|---:|
| MODIS | 2001–2025 | 65.1% | 64.5% |
| VIIRS S-NPP | 2013–2025 | 62.4% | 65.4% |
| VIIRS NOAA-20 | 2019–2025 | 63.4% | 65.7% |

## 10. Thermal-anomaly type composition

The default fire-focused exploration uses `type=0`. Other type codes remain relevant for QA and for recognizing non-vegetation thermal detections. Type definitions must follow the appropriate NASA FIRMS product documentation.

![Thermal-anomaly type shares by sensor.](figures/07_type_mix_by_sensor.png)

*Relative composition of types 0, 1, 2, and 3 by sensor.*

## 11. Daytime versus nighttime detections

The `daynight` flag reflects acquisition conditions and satellite overpass times rather than the duration of a burning event. Observation opportunities differ across satellites and should be considered during harmonization.

![Day and night detection composition by sensor.](figures/08_day_night_mix.png)

*Daytime and nighttime detection counts by sensor.*

| Sensor | Day (D) | Night (N) | Night share |
|---|---:|---:|---:|
| MODIS | 1,192,570 | 340,841 | 22.23% |
| VIIRS NOAA-20 | 921,180 | 386,423 | 29.55% |
| VIIRS S-NPP | 2,351,519 | 1,163,001 | 33.09% |

## 12. FRP distribution: robust statistics and outliers

Pixel-level FRP has a heavily right-skewed distribution. Medians, interquartile ranges (IQR), P95, and P99 are therefore more informative than means alone. FRP is **radiative power in MW**, not fire duration, total energy, or burned area. Comparisons across sensors must account for measurement algorithms and pixel size.

![FRP median, IQR, and 95th percentile for type-0 records.](figures/09_frp_quantiles.png)

*FRP median, quartiles, and P95 for `type=0`.*

| Sensor | P25 FRP (MW) | Median FRP (MW) | P75 FRP (MW) | P95 FRP (MW) | Mean FRP (MW) |
|---|---:|---:|---:|---:|---:|
| MODIS | 10.10 | 17.40 | 33.90 | 104.20 | 33.10 |
| VIIRS NOAA-20 | 2.64 | 4.76 | 8.48 | 24.23 | 8.00 |
| VIIRS S-NPP | 2.45 | 4.72 | 8.65 | 26.92 | 8.41 |

Maximum FRP is far above the 99th percentile, so means tend to exceed medians. The dashboard should show median and P95 rather than allowing rare extreme values to appear typical. **Do not sum FRP over different passes or sensors to estimate a fire's total energy.**

## 13. Confidence is not equivalent across sensors

MODIS reports numerical confidence (0–100), while VIIRS reports `l`, `n`, and `h` categories. Within the supplied MODIS `type=0` records, median numerical confidence is **67**; this is not a calibrated 67% probability of a real fire. VIIRS `high` cannot be assumed equivalent to a particular MODIS threshold.

![VIIRS confidence-category distributions.](figures/10_viirs_confidence.png)

*VIIRS S-NPP and NOAA-20 confidence class distribution.*

| Source | Low | Nominal | High |
|---|---:|---:|---:|
| VIIRS NOAA-20 | 6.86% | 90.31% | 2.83% |
| VIIRS S-NPP | 6.14% | 90.44% | 3.43% |

## 14. Spatial distribution on a coarse 0.5° grid

For descriptive spatial EDA, detections were grouped into 0.5° × 0.5° latitude/longitude cells. This coarse grid does **not** identify provinces or districts precisely and does not measure hectares burned. The plots do not contain Indonesia's authoritative coastline or administrative polygons.

![VIIRS S-NPP spatial-grid density, 2015.](figures/11_spatial_density_2015.png)

*VIIRS S-NPP hotspot-detection density, 2015.*

![VIIRS S-NPP spatial-grid density, 2019.](figures/12_spatial_density_2019.png)

*VIIRS S-NPP hotspot-detection density, 2019.*

**Selected highest-count VIIRS S-NPP grids in 2015:**

| Grid lower latitude (°) | Grid western longitude (°) | `type=0` detections |
|---:|---:|---:|
| −3.0 | 105.5 | 28,158 |
| −3.0 | 114.0 | 19,639 |
| −3.0 | 105.0 | 16,842 |
| −2.5 | 114.0 | 16,578 |
| −2.0 | 103.5 | 15,678 |
| −2.0 | 104.0 | 15,398 |
| −3.5 | 105.5 | 15,249 |
| −3.5 | 105.0 | 14,279 |

## 15. MODIS–VIIRS comparison during overlapping years

MODIS overlaps with S-NPP from 2012, and NOAA-20 joins from 2018. Different instruments may observe the same area at different times and resolutions. A defensible baseline keeps sensors separate, aggregates them to matching time windows and spatial cells, and compares results **without treating the summed counts as unique fires**.

![Normalized 2015 monthly detection shares by sensor.](figures/13_normalized_2015_sensor_comparison.png)

*2015 monthly profile, normalized within each sensor.*

![Raw monthly detection count comparison in 2019.](figures/15_raw_2019_comparison.png)

*Raw detection counts for three sensors in 2019.*

## 16. Spatial co-occurrence in 2019 (not fire-event matching)

A simple descriptive check asks whether the same 0.5° grid cell has at least one MODIS and S-NPP detection within a given month. Grid-set overlap is summarized by the **Jaccard index** (intersection divided by union). A high Jaccard value indicates similar coverage of active grid cells, **not** detection-level agreement, overpass-time matching, true fire perimeters, or verified model accuracy.

![Monthly 2019 MODIS–S-NPP coarse-grid Jaccard overlap.](figures/17_spatial_overlap_grid2019.png)

*Jaccard overlap of occupied monthly grids, MODIS versus S-NPP, 2019.*

**Monthly 2019 Jaccard summary:** minimum **0.226**, median **0.397**, maximum **0.757**. These values depend on cell size and temporal aggregation and must not be interpreted as classification performance.

## 17. Highest-count days and extreme detection periods

The highest-count days represent dates when many satellite pixels were classified as `type=0`. They do not rank unique fire incidents by extent or human impact. Event-level conclusions require explicit spatiotemporal event grouping and external validation.

![Twelve highest-count VIIRS S-NPP dates.](figures/16_peak_dates_snpp.png)

*Twelve UTC dates with the most VIIRS S-NPP `type=0` detections.*

## 18. Changes in MODIS product version fields

The supplied MODIS files contain `version` values `6.2`, `6.03`, and `61.03`. Their archive and processing provenance should be examined before interpreting the complete long-term series. These values **must not be silently rewritten as one version**; they may indicate different processing or collection contexts.

![MODIS version-label composition by year.](figures/14_modis_versions.png)

*Yearly counts grouped by the raw MODIS `version` field.*

## 19. Main findings and VESTIGIUM product implications

| Finding | Careful interpretation | Product implication |
|---|---|---|
| 2015 stands out in MODIS and S-NPP | Highest `type=0` counts within these sensor series | Offer a 2015 exploration preset |
| 2019 stands out in S-NPP and NOAA-20 | Many satellite detections; not evidence of ignition cause | Offer a 2019 sensor-comparison view |
| August–October dominates many annual distributions | Sensor-specific seasonal concentration | Prioritize month filtering and an annual timeline |
| MODIS/VIIRS confidence scales differ | No direct valid mapping | Show native scales and definitions |
| Some thermal anomalies are not vegetation-related | Filtering affects interpretation | Default to `type=0`, optionally expose other types |
| A 0.5° density map is coarse | Precise point data still matter | Use map clustering plus bbox/zoom queries |
| Multiple MODIS version values occur | Possible methodological discontinuities | Retain product `version` and per-file provenance |

## 20. Responsible machine-learning development plan

**Stage A — Non-ML baseline:** Aggregate MODIS and VIIRS separately into agreed UTC windows and common cells (for example, 0.1° or 0.25°, after testing). Measure source-specific counts, coverage and ratios, and robust seasonal anomalies.

**Stage B — Evaluated harmonization:** Define the prediction target explicitly. One possibility is a sensor-robust activity index per spatial cell, **not** an estimate of the absolute number of real fires. Evaluate regression or gradient boosting using source identity, calendar features, FRP, brightness, scan/track, location and spatiotemporal context. Do not treat a label engineered from the satellites themselves as independent physical ground truth. Compare every model to a straightforward baseline.

**Stage C — Validation:** Split by **both time and geography** to avoid leakage from nearby observations. Report MAE/RMSE or rank agreement against the explicitly defined target, assess calibration where appropriate, and compare performance across regions. Independent validation, such as burned-area products or higher-resolution observations, is required for claims of physical correspondence.

**Unsupported from these data alone:** the probability of deliberate versus natural ignition, the number of hectares burned, or whether a former fire location subsequently became a plantation or factory. Such claims require verified ignition-cause labels, lightning and weather data, burned-area layers, and multi-year land-cover information. Spatial correlation alone does not establish intent.

## 21. Data-quality actions before dashboard deployment

1. **Geographic clipping:** Use a vetted Indonesia boundary geometry and appropriate coordinate system; add province/district spatial joins and reference metadata.
2. **Record contract:** Retain `latitude`, `longitude`, `acq_datetime_utc`, `source`, `satellite`, `version`, `type`, `frp`, `confidence`, and `daynight`.
3. **Observation versus zero:** Do not fill a day with no recorded detection as proof of zero fire activity; account for cloud cover, overpass schedules, and availability.
4. **Cross-sensor duplication:** Design a documented spatiotemporal matching protocol with explicit thresholds. Do not drop records arbitrarily.
5. **API serving:** Precompute aggregations for national/low-zoom maps; page and filter individual detections by viewport (bbox), date, and sensor for click/hover.
6. **Public transparency:** Show source file, product version, field definitions, UTC/local-time conversion and the meaning of `type=0`.
7. **Product metadata:** Verify archive origin, product quality status, and reuse/licensing conditions.
8. **Humanitarian analysis:** Keep hotspot, burned-area, land-cover, concession/legal-rights and other evidence layers separate.
9. **Automated EDA checks:** Fail on absent required fields, malformed dates, out-of-range coordinates, negative FRP, unknown type codes, or mismatched annual filenames.

## 22. Limitations and unsupported causal claims

- Cloud/smoke obscuration, satellite overpass frequency, day/night sampling, sensor sensitivity and product revisions cannot be resolved from these CSV records alone.
- `type=0` does **not** mean a confirmed *forest* fire. Vegetation fires can include non-forest land covers.
- MODIS 2000, S-NPP 2012 and NOAA-20 2018 are partial initial years, so raw totals cannot be compared mechanically with full years.
- Detections on agricultural or plantation land do not prove deliberate burning. There are no verified `human-caused` or `natural` labels in these files.
- Administrative attribution is not completed. Falling inside an approximate coordinate box does not prove a point lies on Indonesian land.
- Pixel FRP is power (MW), not hectares burned, fire duration or a carbon-emissions estimate.
- The provided ZIP does not contain burned-area data, land-cover change maps, concession permits, ownership records or cloud-cover measures.
- The 2015/2019 peaks and seasonal distributions are descriptive patterns, **not causal evidence**.

## 23. Reproducibility artifacts

- `vestigium_eda.py`: reads `data.zip`, computes original aggregates and raw-data checks.
- `render_eda.py`: generates 17 English-labeled figures and the 2019 grid-overlap table.
- `VESTIGIUM_EDA_EN.ipynb`: sequentially annotated, executed notebook using the included tables and figures.
- `tables/`: 20 source-derived CSV/JSON tables for independent audit and backend prototyping.
- `figures/`: 17 PNG charts.
- `summary.json`: machine-readable original data-quality summary.
- `provenance.json`: input archive fingerprint.

To reproduce from the supplied raw archive, put `data.zip` next to the project directory and run `python vestigium_eda.py data.zip .`, followed by `python render_eda.py`. The final English-language report can be regenerated using `python build_english_report.py`. Keep large raw archives outside the public GitHub repository.

### Primary product references
- NASA FIRMS MODIS: https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_MODIS_Firehotspots.html
- NASA FIRMS VIIRS: https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_VIIRS_Firehotspots.html
- NASA FIRMS Archive: https://firms.modaps.eosdis.nasa.gov/download/

**Conclusion:** These datasets support exploratory analysis and historical hotspot mapping but do not establish ignition motives or land-use outcomes after a fire. The NASA challenge remains focused on MODIS–VIIRS harmonization and transparent fire-activity calendars.