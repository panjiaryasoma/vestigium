# Reproduce VESTIGIUM locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and use the pinned Python 3.11 runtime (`.python-version`). Source NASA FIRMS CSV ZIP for Indonesia is provided separately and is **not committed to GitHub**. Allow multi-GB disk space for the 6-million-record input and intermediate outputs.

```bash
uv sync --locked
uv run python -m unittest discover -s tests -v

# Place data.zip at data/raw/data.zip
uv run python scripts/run_all.py --input data/raw/data.zip
```

The three stages can also be executed individually:

```bash
uv run python src/pipelines/build_pipeline.py --input data/raw/data.zip --output data/processed/data-engineering
uv run python src/pipelines/run_advanced.py --database data/processed/data-engineering/vestigium_hotspots.sqlite --output data/processed/geospatial
uv run python src/pipelines/harmonize.py --input data/processed/geospatial/monthly_equal_area_25km.csv --output data/processed/harmonization
uv run python src/pipelines/validate_outputs.py --root .
```

**Inputs/outputs:** Source ZIP contains NASA FIRMS CSVs; only `type=0` presumed vegetation fire detections are used in these product tables. The SQLite database retains original observation coordinates and sensor-specific confidence values. Equal-area 25-km grids are derived using EPSG:6933. Harmonization predicts S-NPP-like *detected-pixel counts conditional on MODIS-positive grid-months*. The calendar has a known structural discontinuity at the 2012 sensor handoff. It is not a count of fire incidents or burned hectares.

## Validation status

GitHub Actions executes syntax compilation, unit tests and a **synthetic end-to-end fixture** that builds SQLite data, grid aggregates and ML outputs. These tests verify the code's runtime contracts and bookkeeping, **not real-data numerical parity** or calibration accuracy. Full-data parity requires actually running the commands above on the NASA archive and comparing outputs with historical stage reports.

The original source scripts from the approximately 498 MB `nasa.zip` bundle were not accessible for byte-by-byte extraction during repository migration. New entrypoints were reconstructed from the notebook code and committed data contracts. Their methodology should be treated as a transparent reproducible baseline, not a claim of exact equivalence to the older analysis.

The default repository notebooks are under [`notebooks/`](../notebooks/) and use local `data/processed/` folders. The original EDA/Geospatial full-report notebooks remain in their corresponding `*_REFERENCE.ipynb` files for historical comparison.

## Data policy

Do not upload source archive ZIP, six million raw hotspot rows, multi-GB SQLite files, cloud keys, or trained ML binary artifacts to GitHub. Store separately with provenance/checksums. Reports and source code belong in `docs/`, `notebooks/` and `src/`.
