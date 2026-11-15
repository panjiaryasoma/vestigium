# Local pipeline execution

From repository root, create a Python 3.11+ virtual environment and install packages:

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Copy your NASA FIRMS Indonesia raw archive to `data/raw/data.zip` (ignored by Git).

```bash
python src/pipelines/build_pipeline.py --input data/raw/data.zip --output data/processed/data-engineering
python src/pipelines/run_advanced.py --database data/processed/data-engineering/vestigium_hotspots.sqlite --output data/processed/geospatial
python src/pipelines/harmonize.py --input data/processed/geospatial/monthly_equal_area_25km.csv --output data/processed/harmonization
```

**Important:** these are reconstructed reproducible entrypoints based on the committed project data contracts, not byte-for-byte copies of the original scripts inside `nasa.zip`. **Full-data execution has not been independently rerun in this GitHub migration**. Performance and numeric equality with the previous reports require validation before judging. The scripts calculate new QA reports from the original raw data and must not silently inherit older validation labels.

Large local-only outputs are under `data/processed/`. Avoid committing .zip, .sqlite, raw NASA CSVs, large aggregate CSVs, or joblib model binaries. Use externally hosted artifacts with checksums if needed by deployment.

The notebooks under `notebooks/` are scientific walkthroughs originally created within earlier stage-specific bundles; some may still refer to those archived chart/table outputs. The command-line pipelines above are the supported runnable reconstruction.
