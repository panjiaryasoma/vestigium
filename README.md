# VESTIGIUM

**Earth remembers what fire leaves behind.**

An evidence-led historical satellite fire-intelligence project for Indonesia (2000–2025). Developed by **Team Ga Tidur** for **NASA Space Apps Challenge 2026**.

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots.

## What VESTIGIUM aims to do

- Present an interactive map of Indonesia showing geolocated thermal detections, filterable by date, satellite sensor, and geographic extent.
- Let users inspect observation dates/times, pixel-center coordinates, sensor identity, fire radiative power (FRP), and available confidence indicators.
- Provide monthly and annual time-series summaries and a fire-activity calendar.
- Calibrate MODIS detections toward a VIIRS S-NPP-like reference scale, with explicit hold-out evaluation and limitations.
- In a future independent module, explore land-cover changes after burned-area events using additional validated datasets.

## Repository organization

```text
vestigium/
├── data/
│   └── README.md             # Local datasets and external artifact policy
├── docs/
│   ├── eda/
│   ├── data-engineering/
│   ├── geospatial/
│   └── harmonization/
├── notebooks/
│   ├── eda/
│   ├── data-engineering/
│   ├── geospatial/
│   └── harmonization/
├── src/
│   └── pipelines/
│       └── build_vestigium_daily_baseline.py
├── README.md
└── .gitignore
```

Frontend, backend, extended data pipelines, unit tests, and serving code will be added when their sources are inspected and verified. Do not infer their implementation from the directory plan alone.

## Research and reproducibility

Start with the [documentation index](docs/README.md), [notebook index](notebooks/README.md), and [data policy](data/README.md).

Available stage documentation:

1. [Exploratory Data Analysis](docs/eda/EDA_REPORT.md)
2. [Data Engineering](docs/data-engineering/EXECUTION_REPORT.md) and [data contract](docs/data-engineering/DATA_CONTRACT.md)
3. [Geospatial QA](docs/geospatial/GEOSPATIAL_QA_REPORT.md)
4. [MODIS–VIIRS Harmonization](docs/harmonization/HARMONIZATION_REPORT.md) and [output contract](docs/harmonization/DATA_CONTRACT.md)

Notebooks are stored without large executed outputs. They may require changes to input paths to run from the reorganized repository. Raw CSVs, the full hotspot SQLite database, large gridded outputs and model binaries are intentionally not committed to GitHub.

## Basic daily baseline

With source CSV archive available locally at `data/raw/data.zip`:

```bash
mkdir -p data/processed
python src/pipelines/build_vestigium_daily_baseline.py data/raw/data.zip data/processed/daily_sensor_baseline.csv
```

This creates unharmonized, sensor-wise daily summaries only. It does not perform geospatial harmonization or model training.

## Scientific boundaries

- A hotspot record represents a satellite-observed thermal anomaly in a pixel, not a proven individual fire event, ignition point, or burned-area measurement.
- MODIS and VIIRS differ in sensitivity, resolution, overpass coverage, and quality labels. Their counts cannot be naively summed or treated as equivalent.
- The experimental calibration is an estimate of VIIRS-like detection counts conditional on MODIS observations, not a verified number of fires.
- Active-fire patterns alone **cannot establish that a fire was deliberately set or identify a perpetrator**.

## Sources and attribution

- [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) for MODIS and VIIRS thermal-anomaly/active-fire detections.
- Future work may incorporate independent burned-area and land-cover products, such as MapBiomas Indonesia, subject to validation and licensing.

Visual direction: Darkroom-inspired investigative editorial identity paired with a scientifically readable, map-first exploration interface.

**Team Ga Tidur · NASA Space Apps Challenge 2026**. Independent participant project; not an official NASA product.
