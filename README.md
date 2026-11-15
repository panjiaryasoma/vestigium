# VESTIGIUM

**Earth remembers what fire leaves behind.**

An evidence-led historical satellite fire-intelligence project for Indonesia (2000–2025). Developed by **Team Ga Tidur** for **NASA Space Apps Challenge 2026**.

**Challenge:** Harmonization of MODIS and VIIRS Hot Spots.

## Scientific scope

VESTIGIUM explores historical NASA FIRMS thermal anomalies on an Indonesia map, with per-sensor timeline summaries, reproducible geospatial gridding, and experimental MODIS-to-VIIRS S-NPP detection-count calibration.

**A satellite hotspot is a pixel detection, not a confirmed wildfire, a unique fire event, an ignition cause, burned area, or evidence of arson.** VIIRS and MODIS have different sensitivity, orbital coverage, spatial resolution, and confidence conventions. Raw counts must not be added together as distinct real-world fires.

## Repository layout

\`\`\`text
vestigium/
├── data/                   # README tracked; raw and processed data ignored by Git
├── docs/
│   ├── eda/                # Full English exploratory report
│   ├── data-engineering/   # Data contracts and QA
│   ├── geospatial/         # Equal-area method and limitations
│   └── harmonization/      # ML evaluation and contract
├── notebooks/
│   ├── eda/
│   ├── data-engineering/
│   ├── geospatial/
│   └── harmonization/
├── src/pipelines/          # Local data processing, harmonization, QA, map query
├── scripts/                # One-command local orchestrator and instructions
├── tests/                  # Unit and synthetic end-to-end pipeline checks
├── .github/workflows/      # CI validation
├── requirements.txt
└── README.md
\`\`\`

## Rebuild the pipeline locally

Use Python **3.11+** and the official NASA FIRMS CSV ZIP for Indonesia.

\`\`\`bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests -v

# Place your source archive at data/raw/data.zip
python scripts/run_all.py --input data/raw/data.zip
\`\`\`

The runner rebuilds:

1. **Data Engineering:** \`data/processed/data-engineering/vestigium_hotspots.sqlite\`, plus UTC sensor-wise day, month, year and 0.25° grid summaries.
2. **Advanced Geospatial:** \`data/processed/geospatial/monthly_equal_area_25km.csv\` and 1°, 0.5°, 0.25°, 0.1° grid layers.
3. **MODIS–VIIRS Calibration:** \`data/processed/harmonization/calibrated_modis_25km_monthly.csv\`, monthly/annual calendars, model test metrics, diagnostics, and figures.
4. **Validation:** conservation checks across all output levels.

**Important provenance note:** The command-line source scripts were reconstructed from earlier notebook and data-contract specifications, because the original large \`nasa.zip\` archive was inaccessible to automatic extraction during repository migration. They were validated in GitHub Actions using *synthetic data*, not rerun on all ~6 million Indonesian source records as part of this migration. The original historical EDA, QA, and harmonization report values reflect earlier runs; new outputs must be checked for numerical agreement before claims of exact reproduction. See [reproducibility details](scripts/README.md).

Large raw data, raster files, intermediate databases, and trained model artifacts are deliberately excluded from GitHub. Documentation and notebooks are tracked instead.

## Research

- [Documentation index](docs/README.md)
- [Notebook index](notebooks/README.md)
- [Data handling](data/README.md)
- [EDA report](docs/eda/EDA_REPORT.md)
- [Data Engineering execution report](docs/data-engineering/EXECUTION_REPORT.md)
- [Geospatial QA](docs/geospatial/GEOSPATIAL_QA_REPORT.md)
- [Harmonization evaluation](docs/harmonization/HARMONIZATION_REPORT.md)

## Next deliverables

- Production-ready backend and frontend integration for map viewport queries and timeline interaction.
- Independent observation-effort data (satellite overpasses, cloud cover) to strengthen calibration.
- Verified polygon boundaries for administrative mapping and independent data for burned-area/land-cover history.

## Attribution

[NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) supplies the source MODIS and VIIRS observations. This is an independent challenge participant project, **not** an official NASA product.
