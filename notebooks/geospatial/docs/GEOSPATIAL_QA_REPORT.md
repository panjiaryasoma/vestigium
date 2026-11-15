# VESTIGIUM Advanced Geospatial Preprocessing | Execution & QA Report

## Summary

**Status: PASS** for all record-conservation checks. The workflow ran on **48 Indonesia CSV files** from the user-supplied archive, corresponding to **6,355,534 source detections**. It retained **5,997,676 type=0 presumed vegetation thermal detections**, consistent with prior first-stage Data Engineering output. The Angola file was excluded by filename. The pipeline completed in **26.08 seconds** in the authoring environment. Runtime on other computers will differ.

## Scope and source grain

An observational record is a single NASA FIRMS active-fire/thermal-anomaly pixel, not a verified unique fire incident. All counts below retain the satellite family, UTC period, and spatial cell. Input MODIS spans 2000–2025, VIIRS S-NPP 2012–2025, and NOAA-20 2018–2025. The data are not calibrated into one homogeneous measurement stream.

## Accepted records by sensor

| Sensor family | Accepted presumed-vegetation pixel detections |
|---|---:|
| MODIS | 1,443,591 |
| VIIRS S-NPP | 3,350,961 |
| VIIRS NOAA-20 | 1,203,124 |
| **Total** | **5,997,676** |

## Multi-resolution output reconciliation

| Output | Sensor-month/cell records | Total detections | Validation |
|---|---:|---:|---|
| 0.1° geographic | 921,441 | 5,997,676 | PASS |
| 0.25° geographic (reused baseline) | 432,387 | 5,997,676 | PASS |
| 0.5° geographic | 219,954 | 5,997,676 | PASS |
| 1.0° geographic | 104,745 | 5,997,676 | PASS |
| EPSG:6933 25-km equal-area | 473,862 | 5,997,676 | PASS |

Also generated 289,449 aligned raw sensor-month-grid records, 9,158 sensor-grid recurrence descriptors, and **16,000** sample source pixel records for frontend hover testing.

## Geographic sanity check: important caveat

The nationally framed archive was first constrained to a coarse candidate longitude/latitude bounding box. An additional diagnostic used a Natural Earth 1:110m **low-resolution country polygon**, applied to a deterministic stratified **5,760**-point sample. The result was **5,125 inside** versus **635 outside** this *low-resolution drawing*. These are **NOT invalid detections**. Low-resolution coastlines omit small islands and coastal nuances. No detections were discarded based on the polygon.

## Provincial mapping — NOT completed

No defensible ADM1 province dataset was available locally in this run. Consequently **no province assignments were made**, and no province-level totals are reported. The bundled optional spatial join script accepts GeoJSON/GPKG boundaries and explicitly flags ambiguous/unmatched points once sourced. Historical province names may differ from contemporary borders.

## Cross-sensor comparability — NOT harmonized

The raw MODIS/VIIRS co-location grid is a feature source, **not** an ML model or scientific correction. A missing value recorded as zero means *no detection in the source dataset for that sensor, month, and cell*, not proof of no ignition, full satellite coverage, or cloud-free conditions. Results remain conditioned on resolution, orbit, sensitivity and processing-version changes.

## Integrity and limitations

1. The total `type=0` count is identical across all five spatial resolutions. **PASS**.
2. Sensor-family accepted counts reconcile to the total. **PASS**.
3. Test suite covers geographic indexing, equal-area counting, timestamp acceptance, filename exclusion, and optional ADM1 point/polygon matching. **PASS**.
4. Longitude/latitude are pixel **centroids**, not exact ignition coordinates.
5. Raw confidence classes and categorical VIIRS confidence are not conflated.
6. FRP aggregates summarize detected pixel power values, not burned hectares or fire energy.
7. Country boundaries, administrative changes, observation-effort normalization and scientific sensor harmonization require subsequent evidence and processing.

## Follow-on work

- Obtain explicitly dated, licensed ADM1 province polygons and execute the optional spatial join with match-rate QA.
- Feed zoom-dependent aggregates to the MapLibre/deck.gl frontend; source individual hover coordinates from the existing indexed SQLite database.
- Build a harmonization benchmark that uses shared spatial supports, overlapping time windows, sensor observation availability, and held-out years/regions.
- If time allows, integrate independent burned-area and land-cover datasets for post-fire land-use history; hotspot detections alone cannot establish recovery, conversion or arson.

## Source references

- NASA FIRMS data archive: https://firms.modaps.eosdis.nasa.gov/download/
- MODIS detection fields: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html
- VIIRS detection fields: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html
- Optional province boundaries: https://www.geoboundaries.org/api.html
- Natural Earth 1:110m national polygon: https://www.naturalearthdata.com/
