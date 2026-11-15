# VESTIGIUM — Data Engineering Execution Report

**Status:** PASS, complete 48-file Indonesia archive build.  
**Team:** Ga Tidur · NASA Space Apps Challenge 2026  
**Period:** 2000–2025 (partial sensor years noted below).  
**Input:** user-supplied `data.zip`; input SHA-256: `8af7ff723b8d5c0916b382b1a2f9088b9028b75fecc1c2cfb927831c1127bcba`.  
**Pipeline:** `build_pipeline.py` v1.0.0.  
**Run result:** Complete ingestion and reconciliation of every accepted record.

## 1. Dataset ingestion

| Source | Input rows | Presumed vegetation detections (`type=0`) | Excluded other types |
|---|---:|---:|---:|
| MODIS | 1,533,411 | 1,443,591 | 89,820 |
| VIIRS_NOAA20 | 1,307,603 | 1,203,124 | 104,479 |
| VIIRS_SNPP | 3,514,520 | 3,350,961 | 163,559 |
| **TOTAL** | **6,355,534** | **5,997,676** | **357,858** |

- 49 CSVs present; 48 Indonesia CSVs accepted by source-file whitelist; 1 Angola file excluded.
- Invalid rows rejected: **0**.
- Record-level dimension preserved: sensor, raw satellite, timestamp UTC, reported latitude and longitude, FRP, quality fields, day/night, version and source provenance.
- Values are pixel **detections**, not distinct incidents. Do not add satellite counts to infer total fires.

## 2. Produced analytical layers

| Deliverable | Groups |
|---|---:|
| `daily_sensor.csv` | 16,880 |
| `monthly_sensor.csv` | 563 |
| `annual_sensor.csv` | 48 |
| `monthly_grid.csv` | 432,387 |
| `annual_grid.csv` | 104,359 |

All five aggregate `detection_count` columns reconcile to **5,997,676**. For the grid outputs, cells are 0.25° × 0.25°, beginning at 94°E, 12°S. Their centers represent aggregation bins only.

## 3. Source inclusion and coverage

- MODIS: 26 annual CSVs, 2000–2025. MODIS 2000 begins in November.
- VIIRS S-NPP: 14 annual CSVs, 2012–2025. 2012 begins in January, but no full-year coverage is guaranteed.
- VIIRS NOAA-20: 8 annual CSVs, 2018–2025. 2018 begins in April.
- VIIRS NOAA-21 is absent from this source archive.
- Dates and acquisition times are preserved as **UTC**, not naively converted to Western Indonesia Time.

## 4. Implemented safeguards

1. Sensor-aware confidence: MODIS numeric percent and VIIRS categorical labels remain separate.
2. Required-column checks, finite coordinates, coarse geo bounding box, date-year match, HHMM range, and nonnegative FRP.
3. File-based provenance and cryptographic fingerprints (SHA-256).
4. Sensor-separated daily, monthly, annual, and grid aggregation.
5. Five count-reconciliation assertions: database rows, input source ledger and summary totals.
6. Unit and end-to-end test suite passed; Python notebook execution passed.
7. Read-only bounded SQL queries available as backend reference.

## 5. Quality caveats (not bugs to conceal)

**High priority:**

- No precise Indonesian coastline or province polygons have been joined. Filename + bounding box are insufficient for authoritative boundary-specific claims.
- No observation-availability normalization or MODIS–VIIRS harmonization has occurred. Raw counts must not be interpreted as equal sensor detectability.
- No confirmed ignition-cause labels exist. Intentional vs natural origin cannot be inferred as ground truth.
- No source-level near-duplicate clustering or multi-sensor fire-event entity resolution. Multiple satellite points may refer to one fire.

**Medium priority:**

- Missing daily/monthly buckets have not been populated with zero, to avoid confusing missing observation with zero burning.
- The geographic area of 0.25-degree grid cells varies slightly with latitude; area-normalized rates require equal-area projections or cell-area weighting.
- The `type=0` filter is presumed vegetation fire, not 'forest fire' validation.
- `sum_detected_pixel_frp_mw` is a sum of detected pixel FRP, not fire energy or burned area.
- Product versions and thermal bands differ; provenance remains intact but version harmonization is an independent science task.

## 6. Implementation handoff

**Interactive map:** Use the SQLite `hotspots` table for individual red dots and hover data, with a bounded time and viewport. For zoomed-out density, use `monthly_grid.csv` or `annual_grid.csv`. Stream/paginate rather than exporting all 6 million records to a browser.

**Timeline/calendar:** Use `daily_sensor.csv`, `monthly_sensor.csv`, and `annual_sensor.csv`, preserving the sensor dimension and UTC date.

**ML harmonization:** Begin a spatial-temporal observation-window alignment and independent evaluation. The current outputs are standardized *inputs*, not harmonized results. Compare held-out region/year generalization and report uncertainty.

**Fire Legacy:** Landsat and MapBiomas fire/land-cover products would be separate observational layers; they are **not** part of the supplied FIRMS CSV archive and have not been processed here.

## 7. Packaging & reproducibility

- Code package: Python ETL, read-only query examples, validator, optional PyArrow exporter, tests, engineering notebook and contracts.
- Aggregate package: five CSVs + two QA JSONs + this report.
- Complete detections database: a separately compressed `vestigium_hotspots.sqlite` (large; needed for full-scale individual-point hover queries).
- Input source archive `data.zip` is not copied into the packages because it was already supplied.
- Only SQLite and CSV are produced in this environment; writing Parquet requires `pyarrow`, which is unavailable here. Optional exporter provided and documented.

**Build runtime:** 111.8 seconds for extraction-free ingestion, indexing and aggregate exports in this environment. Runtime is environment-dependent.

## 8. Re-run

```bash
python -m unittest discover -s tests -v
python build_pipeline.py --input ../data.zip --output ./outputs
python validate_build.py --output ./outputs
python example_queries.py --db ./outputs/vestigium_hotspots.sqlite --year 2015 --month 9 --limit 10
```

**Outcome:** Ready for API integration and sensor harmonization experiments, with scientific limitations explicitly documented. Not yet a completed NASA harmonization model or a working public website.
