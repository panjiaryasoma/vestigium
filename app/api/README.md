# VESTIGIUM | API

Python 3.10+ · FastAPI. All public text, code comments, and API output are in English.

## Run

```bash
cd app/api
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/api/docs . Tests: `python -m pytest -q`.

## Connect actual data

This ZIP contains only `web/` and `api/` source code. It **does not bundle the ~1.4 GB hotspot SQLite database**, original NASA FIRMS data, or model artifacts. Set these environment variables using the files previously produced by the VESTIGIUM pipeline:

If you run the API inside the VESTIGIUM repository, the API automatically finds artifacts in the existing `data/processed/` folders created by `scripts/run_all.py`:

- `data/processed/data-engineering/vestigium_hotspots.sqlite` (hotspot SQLite, see `docs/data-engineering/DATA_CONTRACT.md`).
- `data/processed/data-engineering/monthly_sensor.csv` (columns `year,month,sensor,detection_count`).
- `data/processed/harmonization/harmonized_calendar_monthly.csv` (harmonized calendar, optional).
- `data/processed/data-engineering/quality_report.json` (data quality, optional).

These data files are **not** committed to GitHub and must be produced or mounted independently. When deploying the backend outside the monorepo, override those locations using `VESTIGIUM_DB`, `VESTIGIUM_MONTHLY_CSV`, `VESTIGIUM_CALENDAR_CSV`, and `VESTIGIUM_QUALITY_JSON`. For example on PowerShell:

```powershell
$env:VESTIGIUM_DB='D:\\vestigium-data\\vestigium_hotspots.sqlite'
$env:VESTIGIUM_MONTHLY_CSV='D:\\vestigium-data\\monthly_sensor.csv'
$env:VESTIGIUM_CALENDAR_CSV='D:\\vestigium-data\\harmonized_calendar_monthly.csv'
python -m uvicorn main:app --reload --port 8000
```

If SQLite is missing, API switches to **explicitly labelled deterministic synthetic demo data**; all coordinates, counts, times, and FRP then are fabricated for UI testing. The calendar and quality-report endpoints are unavailable in this mode, even if stale standalone files exist. Never cite demo data as NASA observations. The `/api/v1/evaluation` endpoint holds **previously archived** test metrics, not a live evaluation of the mounted data.

## Scientific rules

- Observation unit: detected thermal **pixel**, not one ignition, unique wildfire, burned hectare, or forest loss event.
- UTC time only. The frontend labels UTC explicitly.
- Never infer intentionality or natural cause from hotspot patterns.
- Separate raw sensor counts; two sensors are not independent fire events.
- The archived harmonization model was calibrated for MODIS-positive grid-months and is not an all-fire census.
- Map API is viewport-limited. If the limit is exceeded, `meta.truncated=true`; these are not nationwide totals.
- Region filter is a rough geographic viewport filter, **not** administrative province joining.

Endpoints: `/api/health`, `/api/v1/meta`, `/api/v1/hotspots`, `/api/v1/temporal`, `/api/v1/calendar`, `/api/v1/analysis`, `/api/v1/evaluation`, `/api/v1/data-quality`.
