# Frontend integration guide | VESTIGIUM

The frontend's **map** should remain the principal interaction. Visual appearance is Darkroom-first / investigative noir, but information accuracy takes precedence over decoration.

## Spatial data layers by zoom

- **Country overview (zoom ~3–5)**: serve the `monthly_grid_1deg.csv` aggregated cells, aggregated to chosen year/month/sensor.
- **Regional level (zoom ~5–7)**: switch to `monthly_grid_05deg.csv` or `monthly_grid_025deg.csv`.
- **Local exploration (zoom ~7–9)**: use `monthly_grid_01deg.csv` with bounded viewport query.
- **Individual points (zoom ~9+)**: retrieve source pixel records from existing SQLite `hotspots` table, bounded by viewport and request limit; cluster markers on the client or server for performance.

Thresholds are initial UX suggestions; benchmark on actual devices. Draw only bounded subsets at all times. Avoid rendering 6 million DOM nodes or markers in a browser.

## Hover and click

At aggregated zoom, tooltips must say **"satellite detections in grid cell"**, not **"fires"**. On an individual marker, show acquisition timestamp UTC (or explicitly labeled WIB/WITA/WIT), sensor, satellite, raw confidence, FRP in MW, latitude/longitude and pixel-size uncertainty where available. Avoid implying that the centroid is the exact ignition point.

## Temporal exploration

Monthly filters can read the geospatial aggregate tables. The original basic ETL has daily/annual sensor summaries for trend graphs. If a user needs daily, multi-source spatial heatmaps, these are **not** created in this stage: generate daily spatial grid tables in a dedicated later step, or query bounded source records.

## ML & science interface

- `sensor_comparison_025deg_raw.csv` is for exploratory alignment and **NOT** a harmonization model.
- Show raw MODIS/VIIRS series separately until a harmonization method has been evaluated on a hold-out.
- `recurrence_025deg_by_sensor.csv` can trigger "repeated satellite detections" warnings, but must not label "deliberate arson", "natural ignition", or confirmed repeat fire events.
- Preserve the visible source and filtering methodology for every aggregate.

## Proposed API routes (not implemented)

```text
GET /api/v1/grids?resolution=0.5&year=2015&month=9&sensor=VIIRS_SNPP&bbox=...
GET /api/v1/observations?year=2015&month=9&sensor=MODIS&bbox=...&limit=1000
GET /api/v1/recurrence?sensor=MODIS&bbox=...
GET /api/v1/data-quality
```

These are suggested contracts, not a claim that a FastAPI server exists.
