# VESTIGIUM Data Contracts & Serving Strategy

## Stage outputs and exact grains

- `hotspots`: individual satellite **pixel detection**, `id` is a surrogate row key, observations can recur across sensors.
- `daily_sensor.csv`: UTC day × sensor. Does **not** represent total distinct fire events.
- `monthly_sensor.csv`: UTC year × month × sensor.
- `annual_sensor.csv`: UTC year × sensor.
- `monthly_grid.csv`: UTC year × month × sensor × geographic cell (0.25°).
- `annual_grid.csv`: UTC year × sensor × geographic cell (0.25°).

All aggregate counts mean **number of accepted presumed-vegetation-fire detections**, not wildfires or burned hectares. Raw source categories 1/2/3 are recorded in QA exclusions but omitted from product tables.

## Map requests (backend contract suggestion)

```text
GET /api/v1/hotspots?year=2015&month=9&bbox=108,-4,119,4&sensor=MODIS&limit=500
GET /api/v1/temporal?grain=monthly&sensor=VIIRS_SNPP&year=2015
GET /api/v1/grid?grain=monthly&year=2015&month=9&sensor=VIIRS_SNPP
GET /api/v1/data-quality
```

These are **proposed endpoints**, not implemented endpoints. They can be implemented in FastAPI by reading `hotspots` and the aggregate CSV tables.

A sample hover payload from a **hypothetical record**:

```json
{
  "date_utc": "2015-09-12",
  "timestamp_utc": "2015-09-12T07:32:00Z",
  "latitude": -2.2145,
  "longitude": 113.9218,
  "sensor": "MODIS",
  "satellite": "Terra",
  "frp_mw": 42.8,
  "confidence_modis_pct": 85,
  "confidence_viirs_label": null,
  "label": "Satellite hotspot detection, presumed vegetation fire"
}
```

Frontend MUST show the relevant source and timezone; do not format a VIIRS confidence class as a percentage.

## SQL examples

### Read 2015 September markers in a viewport

```sql
SELECT latitude, longitude, timestamp_utc, frp_mw, sensor, satellite,
       confidence_modis_pct, confidence_viirs_label
FROM hotspots
WHERE year = 2015 AND month = 9
  AND longitude BETWEEN 108 AND 119
  AND latitude BETWEEN -4 AND 4
ORDER BY date_utc, time_utc, id
LIMIT 500;
```

### Annual counts by sensor

```sql
SELECT sensor, year, COUNT(*) AS detection_count
FROM hotspots
GROUP BY sensor, year
ORDER BY sensor, year;
```

### Fire detection recurrence indicator, not ignition recurrence

```sql
SELECT sensor, grid_x, grid_y, COUNT(DISTINCT year) AS years_with_detections
FROM hotspots
GROUP BY sensor, grid_x, grid_y
ORDER BY years_with_detections DESC;
```

## Recommended incremental next steps

1. Add Indonesia province polygons + a spatial join for correct province boundaries.
2. Convert grid from lat/lon degrees to equal-area zones for regional-area normalized comparisons.
3. Add satellite availability/overpass coverage as a separate quality and observation-process layer.
4. Build harmonization experiments with held-out year/region validation and uncertainty.
5. Implement paginated map tile/viewport API backed by spatial indexes (SQLite MVP; PostGIS for large-scale production).
6. Add MapBiomas FIRE/LANDY as independent source families for burned area and land-cover evolution, with verified source-specific labels.
