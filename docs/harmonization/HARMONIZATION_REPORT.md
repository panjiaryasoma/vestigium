# VESTIGIUM | MODIS–VIIRS S-NPP Harmonization: Experimental Baseline

**Study area:** Indonesia (coarse source-region bounding box, not a verified national polygon clip)  
**Coverage:** 2000–2025 source detections; calibration overlap 2013–2025  
**Data source:** NASA FIRMS active fire / thermal anomaly products, `type = 0` presumed vegetation fire  
**Release:** 15 November 2026 | Team Ga Tidur | NASA Space Apps Challenge 2026  
**Status:** Experimental *proxy calibration*; not ground-truth harmonization, burned-area estimation, or verified individual fire events.

## Executive assessment

We implemented and evaluated an interpretable pair of statistical baselines plus a machine-learning model to estimate **VIIRS S-NPP-like detected-pixel counts** from MODIS records over monthly, equal-area 25 km cells (EPSG:6933). These outputs are *conditional on MODIS registering at least one pixel in the cell/month*. There is no independent information about missing clear-sky coverage, satellite overpass opportunity, or fire events.

- Source: **473,862 sensor-grid-month rows** representing **5,997,676 presumed vegetation pixel detections**, with 185,083 MODIS-positive cell-months.
- Data splits: **2013–2021 training (64,436)**, **2022 validation (3,696)**, **2023–2025 untouched temporal test (17,291)**.
- **Selected for the prototype:** `ml_poisson_hgbr` because it had the lowest *2022 validation RMSE* among actual harmonization candidates (the raw MODIS count is a comparator, not a calibrated model).
- On the untouched test, ML delivered MAE **10.24**, versus **11.15** for the seasonal baseline. **However, ML test RMSE was 24.68**, worse than the global scaling baseline (21.87). No method dominates every error metric.
- Across all S-NPP-positive grid-months in 2013–2025, only **89.6% of S-NPP detections** lie in grid-months that also have MODIS detections. The other **10.4%** are **not recoverable from a MODIS-positive-only historical calibration**. In 2022 specifically, that within-MODIS share fell to **60.2%**.

## 1. Scientific question

Can a statistical model transform raw MODIS detection counts into a more comparable *VIIRS S-NPP reference-observation proxy* for spatial-temporal fire activity calendars, without conflating sensor coverage and satellite resolution with real changes in fires? **This cannot be answered fully by the present data**, but a conditional empirical calibration can be measured and displayed with limitations.

A **detected pixel ≠ confirmed fire event ≠ burned area**. Neither thermal anomalies nor the derived model describe whether a fire was deliberately started.

## 2. Exact input data and grain

Source: `monthly_equal_area_25km.csv` from VESTIGIUM Advanced Geospatial Preprocessing.

**Primary key:** `sensor, year, month, cell_x, cell_y`; every row is one sensor/UTC month/25 km projected cell. Sensor names: `MODIS`, `VIIRS_SNPP`, `VIIRS_NOAA20`. The 25 km cell has 625 square kilometers in projection, **not** 625 square kilometers burned. The original data filtering kept `type=0` only.

**Features:** MODIS detected pixel count, `log1p` sum and maximum FRP (MW), MODIS day-fraction, seasonal sine/cosine, longitude/latitude of equal-area grid center. Exact same-day/time overpass matching was **not** performed; a monthly grid match does not prove the sensors observed the same physical event.

**Reference:** VIIRS S-NPP detected-pixel count over same UTC month/cell. The reference is not absolute physical truth and includes different detection opportunities. Missing S-NPP detections for a MODIS-positive cell-month are numerically zero in the conditional evaluation, which must **not** be interpreted as a confirmed fire-free or cloud-free cell.

## 3. Training and candidate estimators

- **Raw comparator**: raw MODIS count, *not* a calibrated series.
- **Global ratio**: training-period ratio of S-NPP counts to MODIS counts across MODIS-positive cell-months, **4.634**. Estimated total = MODIS count × global ratio. A resampling exercise over training years yielded range **4.151–4.906**, which is *not* a calibrated prediction interval.
- **Seasonal ratio**: separate factors by calendar month, regularized toward the global ratio with a 1,000-MODIS-pixel equivalent pseudocount.
- **ML Poisson boosting**: `HistGradientBoostingRegressor(loss='poisson')`; 140 iterations, learning rate 0.055, max 18 leaves/5 depth, min leaf 90, L2 regularization 8, reproducible seed 42. Trained once on 2013–2021 and never refit on validation or test.

Year is not an ML feature; thus the model cannot directly memorize a calendar-year outcome. Nevertheless, model drift, sensor versions, environmental trends, and spatial dependence remain major threats to transferability.

## 4. Validation metrics (year 2022)

| Method | MAE ↓ | RMSE ↓ | WAPE ↓ | Aggregate bias | Spearman ρ ↑ |
|---|---:|---:|---:|---:|---:|
| raw_modis | 6.42 | 20.02 | 83.29% | -68.8% | 0.426 |
| global_ratio | 7.77 | 17.15 | 100.71% | +44.4% | 0.426 |
| seasonal_ratio | 7.08 | 17.03 | 91.81% | +30.9% | 0.439 |
| ml_poisson_hgbr | 6.59 | 15.82 | 85.46% | +34.9% | 0.532 |

The selected model reduced validation RMSE, but exhibited **+34.9% aggregate count bias**. Choosing a model based on validation does not establish that the predicted values are unbiased or physically calibrated.

![2022 model validation RMSE](outputs/figures/02_validation_rmse.png)

## 5. Untouched temporal test (years 2023–2025)

| Method | MAE ↓ | RMSE ↓ | WAPE ↓ | Aggregate bias | Spearman ρ ↑ |
|---|---:|---:|---:|---:|---:|
| raw_modis | 15.67 | 43.59 | 79.67% | -75.8% | 0.634 |
| global_ratio | 11.56 | 21.87 | 58.76% | +12.1% | 0.634 |
| seasonal_ratio | 11.15 | 22.30 | 56.69% | +11.9% | 0.661 |
| ml_poisson_hgbr | 10.24 | 24.68 | 52.09% | +11.3% | 0.730 |

Test metrics are computed **only in MODIS-positive cell-months**. They must not be compared directly with full-national S-NPP totals. The test-target aggregate in this subset is **340,004** S-NPP pixel detections. The chosen ML model produces **378,269** equivalent pixel-count proxy units (a fractional *expected count*, not new simulated points).

![Temporal holdout](outputs/figures/03_temporal_holdout_2023_2025.png)
![Annual test totals](outputs/figures/07_holdout_annual_totals.png)

### Regional failure modes (untouched test)

| Approximate longitude band | Reference S-NPP | Selected model estimate | Bias |
|---|---:|---:|---:|
| central_110_125E | 210,300 | 219,046 | +4.2% |
| east_>=125E | 37,767 | 42,318 | +12.0% |
| west_<110E | 91,937 | 116,905 | +27.2% |


These *rough longitude bands* are diagnostic and **not** verified Indonesian administrative provinces. Regional calibration varies; no one scaling factor is accurate across every region.

![Regional model bias](outputs/figures/04_regional_bias.png)

## 6. Coverage mismatch and unseen detections

The reference sensor frequently reports a detected pixel in a grid/month where MODIS reports none. MODIS-only backcasting cannot reconstruct this pattern without external observations and a separate model for missing detections. This study explicitly preserves the unmatched S-NPP count in `overlap_coverage_diagnostics.csv`.

![VIIRS-only coverage](outputs/figures/05_modis_blind_spot_diagnostic.png)

## 7. Historical calendar product

**Primary continuous experiment:** `modis_reference_equivalent_proxy` is estimated consistently **from MODIS** for every available year, including 2000–2011. This is a MODIS-conditioned reference-equivalent proxy, not a fully corrected series of active fires.

**Additional optional display:** `calendar_display_estimate` uses modeled MODIS in 2000–2011, VIIRS S-NPP reported detections from 2012 onward. **This line has a structural measurement break at 2012**. Do not present its jump as a real change in burning. 2000 includes only November–December. S-NPP started in January 2012 (its first January is incomplete), and NOAA-20 is available in this archive from 2018.

![Monthly harmonized MODIS proxy](outputs/figures/06_harmonized_monthly_heatmap.png)

**No reliable uncertainty interval is provided for historical backcasts.** The `out_of_training_range` flag only notes extreme high-tail MODIS count/FRP values versus training; it does not prove in-domain predictions are accurate.

## 8. Claims we deliberately do NOT make

1. No verified ignition cause or human intent (arson vs natural fire).
2. No number of unique wildfires or burned hectares.
3. No exact pixel-level matching of different satellite overpasses or cloud/clear-sky denominators.
4. No correction for sensor aging, observation geometry, orbital coverage, missed detections, biome class, or industrial thermal anomalies beyond basic source `type=0` filtering.
5. No formal uncertainty coverage for modeled history or future forecasts.
6. No causal attribution of the 2015 and 2019 peaks.

## 9. Recommended product/UI integration

- For raw red markers and hover, use the previously constructed **full individual-point SQLite** or a viewport-limited API. Never convert fractional model grid estimates into individual fire coordinates.
- For activity calendars, use `harmonized_calendar_monthly.csv`; show an explicit **Observed vs Modeled** label and a 2012 instrument boundary. Show raw MODIS, S-NPP, NOAA-20 separately for inspection.
- For a monthly map heat layer, use `calibrated_modis_25km_monthly.csv` at 25 km equal-area resolution; draw **grid-level intensity**, not simulated pixel markers or burned area.
- Explain `type=0` means **presumed vegetation fire**, not validated ignition origin.
- Do not use the present calibration to rank landowners or accuse actors. The separate Fire Legacy project requires burned-area and land-cover products, plus external legal/cadastral evidence.

## 10. Key next validation work

1. Include satellite overpass opportunities, cloud masks and observation geometry.
2. Co-register detections in narrower UTC time windows and assess potential duplicate detections.
3. Evaluate with independent burned-area products (e.g., MODIS MCD64A1 and VIIRS burned area), clearly recognizing they measure a different construct.
4. Use spatially blocked validation and test sensitivity to smaller grid cells/shorter time windows.
5. Examine calibration drift by year/satellite product version, vegetation type, daytime/nighttime, and province after validated administrative boundaries are available.
6. Test calibration uncertainty and compare with simple seasonally varying coefficients before claiming science-grade harmonization.

## Source references

- NASA Space Apps 2026 challenge: https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/
- NASA FIRMS alert notes: https://firms.modaps.eosdis.nasa.gov/alerts/notes.php
- NASA FIRMS map disclaimer: https://firms.modaps.eosdis.nasa.gov/map/
- NASA VIIRS fire product details: https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html
- Source data download: https://firms.modaps.eosdis.nasa.gov/download/