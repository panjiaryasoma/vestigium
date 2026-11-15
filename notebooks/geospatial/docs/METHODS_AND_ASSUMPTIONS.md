# Geospatial methodology, quality controls, and boundaries

## 1. Scientific question and unit of observation

This data engineering stage supports a temporal and geographic web interface for Indonesian **satellite active-fire detections** from 2000 through 2025. The atomic source unit is a *satellite pixel observation*, with coordinates at the pixel center, UTC acquisition date/time, platform information, and fire radiative power (FRP). Neither a group of detections nor a marker should be called an individual, verified wildfire. No active-fire product alone establishes human intent, legal land cover, burned area, or causal ignition mechanisms.

## 2. Source inclusion and exclusion

The parser includes only filenames ending `_Indonesia.csv` under `MODIS/`, `viirs-snpp/`, or `viirs-jpss1/`. This guarantees that the unrelated `MODIS/modis_2003_Angola.csv` is not ingested. Presumed vegetation detections (`type == 0`) are retained. Types 1–3 are excluded from this vegetation-focused display but are not asserted to be scientifically invalid. The first-stage basic pipeline retains exclusion provenance.

## 3. QA and timestamp handling

Required coordinates and FRP must be finite. Coordinates must lie in the **coarse candidate Indonesia bounding box** (longitude 94–142°E, latitude 12°S–8°N); this check is a necessary sanity check but not national boundary proof. FRP must be nonnegative; dates must parse, match the source year, and have valid UTC acquisition hours/minutes. Day/night values are `D`/`N`. Each original sensor family remains identified separately. The process never compares MODIS numerical confidence (0–100) with VIIRS ordinal confidence (`l` / `n` / `h`) as if they were the same measurement.

## 4. Geographic grids for fast map exploration

Four coordinate aggregation resolutions are supplied: 1.0°, 0.5°, 0.25°, and 0.1°. At 0.25°/0.5°/1.0°, cells use the original basic-pipeline origin **(94°E, 12°S)** and exact integer coarsening from 0.25° indices. The newly computed 0.1° grid is globally anchored to **(-180°, -90°)**. These indices do **not** share a common origin, so the same `cell_x/cell_y` values are not join keys between the 0.1° and 0.25° products.

Use a zoom-dependent grid to avoid transmitting millions of point observations to the browser. Show density, cluster counts or cells at lower zoom and individual hotspot pixel records only at higher zoom via a viewport query. `detection_count` means number of observations in that UTC month and cell.

**Angular cells are not equal-area.** Never interpret their area directly in square kilometers. Grid centers are for displaying aggregated cells; the positions of actual fire pixels remain in the source SQLite database.

## 5. Equal-area analysis cells

All accepted individual pixel-center coordinates are transformed from WGS84 `EPSG:4326` to the World Cylindrical Equal Area projection `EPSG:6933`. The projected points are assigned to square 25,000 m × 25,000 m indexed cells. Each grid cell therefore occupies 625 km² **in projection space**, but this is not the area burned. The inverse-transformed centers are supplied for web map labeling only. Pixel-detection count per grid remains sensor- and observation-effort-dependent.

## 6. Recurrence as a descriptive feature

`distinct_years_with_detections` counts years with ≥1 accepted pixel detection in the **same 0.25° cell and sensor family**. It does not mean that a single site burned in that many separate incidents, nor that the same forest plot was affected. A valid harmonized recurrence analysis would require observation-process correction, deduplication/event grouping, appropriate spatial resolution, and independent validation.

## 7. Raw cross-sensor comparisons

The `sensor_comparison_025deg_raw.csv` table aligns MODIS, VIIRS S-NPP and NOAA-20 detection counts within UTC month and 0.25° grid. This is **co-location**, not calibrated harmonization. A zero in a sensor column means no accepted detection in the grouped source data; it does not prove satellite coverage, cloud-free visibility, a no-fire condition, or that a different sensor is wrong.

For a subsequent harmonization pipeline, require sensor-availability features, shared observation periods, consistent spatial support, temporal validation separated by year and region, and held-out error metrics. Do not sum raw MODIS/VIIRS counts as unique fires.

## 8. National and provincial boundaries

A Natural Earth 1:110m Indonesian polygon is included solely for a *diagnostic* and overview figure. It poorly represents very small islands/coastal boundaries; so none of the 5.99 million source rows was rejected based on this reference. A stratified 5,760-point sample gave 635 out-of-polygon diagnostics; those require higher-resolution boundary checking and may be valid Indonesia observations.

**ADM1 province enrichment was NOT executed**, because no suitable sourced province polygon was supplied or accessible locally. `scripts/assign_provinces_optional.py` performs strict, optional point-in-polygon enrichment when a valid boundary dataset is provided. It explicitly distinguishes `matched`, `unmatched`, and `ambiguous_overlap`, and must record boundary provenance and reference year. Province splits and boundary revisions since 2000 mean modern labels must not be described as historically accurate boundaries without additional sourcing.

## 9. Confidence, sampling, missingness and limitations

- MODIS is nominally ~1 km; VIIRS detection is nominally ~375 m, with scan/track pixel size variation; neither gives the exact ignition point.
- Missing detections are not identical to missing fires; clouds, overpass schedules, algorithm versions and sensor sensitivity matter.
- Data availability changes substantially over 2000–2025. VIIRS appears only in later years.
- 2000 contains a partial archive year. Counts are not annual burned area or counts of distinct fires.
- FRP sums are sums of **pixel-level observed power at sampling times**; not total fire energy, fire severity, hectares, or CO₂ emissions.
- Sample hover CSV provides a deterministic UI test example, not a full archive and not a scientifically unbiased sample.
- The 2015 interactive HTML preview shows the most-observed **1,250 occupied 0.25° cells**, not all individual hotspots, and uses online map tiles when opened.
- Source and administrative boundary licenses/attributions must be retained for public deployment.

## 10. Acceptance criteria

1. Source file selection excludes Angola.
2. All five geographic and equal-area aggregation outputs have identical summed `detection_count` to the accepted type=0 source population.
3. MODIS and VIIRS remain separate columns/families prior to harmonization.
4. UTC date/time is preserved for individual hover records through the base SQLite database and example sample.
5. All outputs carry units, CRS, grid origin and observational—not causal—interpretation.
6. Province matching, incident deduplication and ignition-cause classification remain unclaimed unless independently implemented and tested.
