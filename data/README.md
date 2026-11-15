# Data directory

This directory describes the data products used by VESTIGIUM.

## Layout

```text
data/
  README.md
  raw/                  # Local-only: NASA FIRMS source CSV ZIPs (gitignored)
  interim/              # Local-only: working/cleaned extracts (gitignored)
  processed/            # Local-only: grid, calendar, and hotspot SQLite outputs (gitignored)
  external/             # Local-only: optional boundary files / other datasets (gitignored)
  samples/              # Small, checked-in non-sensitive sample files only, if needed
```

**Raw and processed production datasets are intentionally not in GitHub.** This includes approximately 6 million individual hotspot detections, the full SQLite database, raster imagery, and fitted model binaries. Store large artifacts in controlled external storage and document their checksums and provenance before distributing them.

## Existing project outputs (built outside this repository)

- NASA FIRMS MODIS (2000–2025), VIIRS S-NPP (2012–2025), and VIIRS NOAA-20 (2018–2025).
- `type=0` records: presumed vegetation-fire thermal detections, **not unique fire events or burned areas**.
- Data engineering: hotspot SQLite, sensor-wise daily/monthly/annual statistics, 0.25-degree spatial aggregates.
- Advanced geospatial: multi-resolution grid summaries and 25-km equal-area grid-month observations.
- Harmonization: experimental MODIS to VIIRS S-NPP reference-scale estimate, with temporal hold-out evaluation.

See [EDA](../docs/eda/EDA_REPORT.md), [data contract](../docs/data-engineering/DATA_CONTRACT.md), [spatial QA](../docs/geospatial/GEOSPATIAL_QA_REPORT.md), and [harmonization report](../docs/harmonization/HARMONIZATION_REPORT.md) for methods, definitions, and limitations.

## Reproduce a basic daily summary

1. Obtain NASA FIRMS CSV files for Indonesia from the official archive; comply with the source attribution and access terms.
2. Place the source archive at `data/raw/data.zip`.
3. Run `uv sync --locked`, create `data/processed/` locally, and execute from the repository root:

```bash
mkdir -p data/processed
uv run python src/pipelines/build_vestigium_daily_baseline.py data/raw/data.zip data/processed/daily_sensor_baseline.csv
```

This script produces **unharmonized** detection counts per UTC date and sensor family. It is not the complete geospatial/harmonization pipeline; see the notebooks and methodological reports for the other stages.

## Responsible interpretation

Coordinates are observation-pixel positions, not proven ignition points. MODIS and VIIRS do not share the same spatial resolution, sensitivity, or confidence representation. Avoid adding raw detection counts across sensors or interpreting patterns as proof of deliberate ignition.
