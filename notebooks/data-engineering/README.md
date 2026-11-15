# VESTIGIUM: Fire Detection Data Engineering

**Team:** Ga Tidur · **Competition:** NASA Space Apps Challenge 2026  
**Source archive:** User-provided `data.zip`, NASA FIRMS annual CSV extracts, 2000–2025.  
**Goal:** A reproducible, auditable transformation of individual satellite active-fire *detections* into map-ready and analysis-ready datasets without conflating sensors, fire events, or causes.

## 1. What this pipeline actually delivers

| Output | Grain | Application use | Notes |
|---|---|---|---|
| `vestigium_hotspots.sqlite`, table `hotspots` | **One accepted satellite pixel detection** | Red-dot map; detection hover; area and date query | Preserves exact reported coordinates and UTC observation times. Not deduplicated into fire incidents. |
| `daily_sensor.csv` | **Sensor × UTC date** | Daily timeline/calendar | Dates with no emitted rows are not filled with zero. |
| `monthly_sensor.csv` | **Sensor × year × month** | Monthly historical chart | Counts are *detections*, not unique fires. |
| `annual_sensor.csv` | **Sensor × year** | Yearly recap | Keep sensor series separate. |
| `monthly_grid.csv` | **Sensor × year × month × 0.25° grid cell** | Zoomed-out hotspot clusters and spatiotemporal heatmap | Grid centers are display locations, not observed point coordinates. |
| `annual_grid.csv` | **Sensor × year × 0.25° grid cell** | Regional long-term map and model candidate features | A degree grid has nonconstant surface area by latitude. |
| `quality_report.json` | **Build + per source CSV** | ETL quality gates / provenance | Archive SHA-256, individual CSV SHA-256, counts, rejects, coverage. |

**Most important scientific distinction:** A detection is a satellite observation of a thermal anomaly. It is neither a verified wildfire incident nor an ignition event. `type=0` is *presumed vegetation fire*; it is **not** a label for intentional burning, forest fires, or fire origin.

## 2. Quick start

Python **3.10+**, standard library only. No third-party dependency is required to build SQLite and CSVs.

```bash
python -m unittest discover -s tests -v
python build_pipeline.py --input ../data.zip --output ./outputs
```

The original ZIP is read **directly**; extraction is unnecessary. The script creates `outputs/vestigium_hotspots.sqlite`, CSV tables and `quality_report.json`.

Try a bounded individual-point query:

```bash
python example_queries.py --db ./outputs/vestigium_hotspots.sqlite \
  --year 2015 --month 9 --west 108 --south -4 --east 119 --north 4 --limit 15
```

Quick smoke test with reduced, **nonrepresentative** input:

```bash
python build_pipeline.py --input ../data.zip --output ./test_outputs \
  --max-files 2 --max-rows-per-file 200
```

Never present smoke-test outputs as a national dataset.

## 3. Source inventory and exclusions

The supplied archive contains **49** CSVs. Exactly **48** are labeled Indonesia by filename and recognized sensor folder:

- `MODIS/modis_2000_Indonesia.csv` through `modis_2025_Indonesia.csv` (26 files)
- `viirs-snpp/viirs-snpp_2012_Indonesia.csv` through `viirs-snpp_2025_Indonesia.csv` (14 files)
- `viirs-jpss1/viirs-jpss1_2018_Indonesia.csv` through `viirs-jpss1_2025_Indonesia.csv` (8 files, VIIRS NOAA-20)

`MODIS/modis_2003_Angola.csv` is deliberately skipped. **NOAA-21 is not present.** The archive begins partway through 2000 for MODIS, 2012 for S-NPP and 2018 for NOAA-20; early partial years must not be treated as full years in a time-trend comparison.

A loose geographic bounding box provides a further gross-coordinate check (`94–142°E`, `12°S–8°N`). It is **not** a precise national landmask or an administrative polygon. Before any authoritative national or provincial totals are published, apply an Indonesian boundary polygon in a GIS workflow and document boundary provenance.

## 4. Transformation sequence

1. **Discover files.** Identify Indonesia CSVs using explicit path and year conventions. Exclude the Angola file and unknown formats. Compute archive and per-file SHA-256.
2. **Validate schemas.** Require latitude, longitude, date, time, FRP, satellite, sensor metadata, confidence, day/night, type, scan and track.
3. **Filter.** Keep `type=0` as *presumed vegetation fire*. Record counts of excluded other types; do not silently discard them.
4. **Validate row values.** Parse ISO dates, `HHMM` acquisition time, finite geographic coordinates, nonnegative FRP, valid day/night flags and sensor-specific confidence values.
5. **Normalize.** Store `timestamp_utc` as ISO-8601 UTC; source-specific satellite labels and product versions remain traceable. MODIS confidence (0–100) and VIIRS categorical confidence (`l/n/h`) are retained in **separate columns**.
6. **Geospatial indexing.** Preserve individual latitude/longitude in WGS84 and calculate a **0.25° cell** using a fixed origin at 94°E, 12°S; output `grid_x`/`grid_y` and display-only cell centers in grid CSVs.
7. **Load + index.** Persist each accepted detection in SQLite with indexes for date/sensor, year/month/bounding box and grid/date searches.
8. **Aggregate.** Materialize daily, monthly, annual and spatial-grid series by **sensor**. No cross-sensor deduplication or harmonization is claimed.
9. **Reconcile.** Check total accepted points against source-file accepted counts and sums in daily/monthly/annual outputs; emit machine-readable QA and provenance.

The SQLite store is regenerated from scratch on each build. Retain the original archive as an immutable input. `PRAGMA journal_mode=OFF` and `synchronous=OFF` are chosen **only during the offline rebuild** for throughput; if interrupted, discard the partial output and rerun.

## 5. Core data dictionary

The `hotspots` table includes:

| Column | Meaning / units |
|---|---|
| `id` | Unique **database row ID**, not a physical fire event ID. |
| `sensor` | `MODIS`, `VIIRS_SNPP`, `VIIRS_NOAA20`. |
| `satellite` | Source-specific raw value (Terra, Aqua, N, N20, etc.). |
| `date_utc`, `time_utc` | FIRMS observation date and zero-padded HHMM in **UTC**. |
| `timestamp_utc` | ISO 8601 UTC string, e.g. `2015-09-12T07:32:00Z`. |
| `year`, `month` | Derived from the **UTC** date; a local Indonesia date may differ. |
| `latitude`, `longitude` | **Reported detection pixel centroid**, WGS84 decimal degrees. |
| `grid_x`, `grid_y` | Integer indices of fixed-degree map aggregation cells. |
| `frp_mw` | Fire Radiative Power in megawatts for that **detection**. |
| `confidence_modis_pct` | MODIS numeric confidence, NULL on VIIRS. |
| `confidence_viirs_label` | VIIRS `l/n/h`, NULL on MODIS. |
| `scan_km`, `track_km` | Source scan/track footprint dimensions (see sensor source metadata). |
| `brightness_primary_k`, `brightness_secondary_k` | Source-dependent thermal band brightness; **not identical bands across sensors**. |
| `daynight` | Satellite day/night detection category. |
| `version` | Raw input product version, not normalized into a single common algorithm version. |
| `source_file_id` | Foreign key to SHA-256-tracked source file metadata. |

`source_files` stores input file name, nominal year, row counts, exclusions, minimum and maximum dates, SHA-256 and validation failures. `pipeline_metadata` records pipeline version, filtering and known limitations.

### What aggregated FRP represents

`sum_detected_pixel_frp_mw` is an arithmetic sum over **detections in a time/sensor bin**. It is *not* total fire energy, burned area, total incident count, or a calibrated multi-sensor measure of fire severity. Use clear captions in every plot.

## 6. Geospatial precision and map UX

- **Individual marker hover:** Query `hotspots` with year/month, bounding box and pagination/limit. Use individual `latitude`, `longitude`, `timestamp_utc`, `frp_mw`, `sensor` and sensor-specific confidence.
- **Zoomed-out layer:** Use `monthly_grid` / `annual_grid` for density; avoid rendering millions of markers simultaneously.
- **Fixed-degree cells:** At the equator, 0.25 degrees is approximately 27.8 km north–south. The width decreases at higher latitudes. Do not interpret cell counts as per-km² density without area correction.
- **Region filtering:** Administrative names/provinces are **not** assigned. Add polygon intersection before labeling a point with a province or national boundary decision.
- **Time display:** The DB stays UTC; UI can convert to WIB (UTC+7), WITA (+8), WIT (+9) when appropriate, clearly indicating the timezone.

## 7. ML contract and NASA challenge fit

This ETL prepares sensor-preserving features for **subsequent** harmonization research, but it does not do harmonization. A credible next stage:

1. Aggregate MODIS and VIIRS into common spatial cells and comparable observation windows.
2. Distinguish coverage and overpass timing differences, not only raw count differences.
3. Define a reference target / scientific evaluation criterion before choosing ML.
4. Fit a statistical baseline on overlapping years (2012–2025), then ML only if held-out region/year evaluation shows improvement.
5. Use independent burned-area reference products as a separate external validation signal, while respecting their own omission biases.
6. Publish uncertainty rather than a fake precise count of distinct fires.

There is **no label** for `intentional` vs `natural` ignition in these records. Do not train an “arson probability” model without independent, credible verified-cause datasets and defensible labels. Climate, lightning, proximity to roads, land change and recurrence are at best contextual features, **not a causal verdict**.

## 8. Operational quality gates

Checks implemented in `tests/` and `build_pipeline.py`:

- Country-file whitelist and exclusion of Angola.
- Required input columns, finite coordinates and FRP, valid dates/times and year agreement.
- Differentiated MODIS/VIIRS confidence scales.
- `source_rows = accepted + excluded + rejected` per full build.
- Reconciliation between SQLite accepted row count, source metadata counts and daily/monthly/annual aggregates.
- Immutable archive SHA and per-file hashes for provenance.
- Read-only parameterized bounded query examples.

Checks **not** yet implemented: national polygon point-in-polygon validation, observation completeness/satellite overpass correction, exact-duplicate verification across files, physical-fire incident clustering, ground-truth cause labels and bias correction across sensors.

## 9. Directory structure

```text
vestigium_de_pipeline/
  build_pipeline.py           # Original ZIP -> indexed SQLite & aggregate CSVs
  example_queries.py          # Bounded read-only viewport query
  export_parquet_optional.py  # Optional partitioned Parquet exports (requires pyarrow)
  validate_build.py           # Re-check output invariants after building
  tests/test_etl.py           # Unit and small end-to-end tests
  README.md                   # This guide
  DATA_CONTRACT.md            # Machine-consumer contracts and sample requests
  VESTIGIUM_DE_WALKTHROUGH.ipynb
```

## 10. Reproducibility and sharing

Keep large source data, generated SQLite and Parquet **outside of Git**. Commit the ETL code, tests, technical docs and optionally **small aggregated CSVs**. Never silently rewrite history, product versions or confidence conventions.

Data source: [NASA FIRMS archive](https://firms.modaps.eosdis.nasa.gov/download/). Sensor data descriptions: [MODIS](https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_MODIS_Firehotspots.html) and [VIIRS](https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_VIIRS_Firehotspots.html). Follow original data attribution / citation guidance.

## 11. Why SQLite rather than Parquet in this run?

The execution environment has no `pyarrow`, `fastparquet`, or DuckDB package and cannot install them. Instead of claiming non-existent Parquet files, this package produces **complete, indexed, queryable SQLite + interoperable CSV** using Python's standard library. For environments with PyArrow, an **optional** `export_parquet_optional.py` streams bounded chunks to Parquet; see below. Parquet is not required to run the main pipeline.
