# VESTIGIUM | Advanced geospatial data contract

**Important:** All CSV timestamps refer to UTC calendar months. The grid tables are observational and uncalibrated.

## `monthly_grid_01deg.csv`

- `sensor`: `MODIS`, `VIIRS_SNPP`, or `VIIRS_NOAA20`.
- `year`: UTC acquisition year.
- `month`: UTC acquisition month (1–12).
- `cell_x`, `cell_y`: integer global grid indexes anchored at (-180°, -90°), step=0.1°.
- `detection_count`: number of accepted `type=0` pixel observations.
- `sum_detected_pixel_frp_mw`: sum of pixel FRP values, in MW (not fire energy).
- `max_detected_pixel_frp_mw`: maximum observed pixel FRP value in the cell/month/sensor group.
- `daytime_detections`, `nighttime_detections`: counts by FIRMS day/night flag.
- `center_longitude`, `center_latitude`: geographic center of the cell, EPSG:4326.

## `monthly_equal_area_25km.csv`

Same columns as the 0.1° output, except `cell_x` and `cell_y` index 25,000-meter square cells in **EPSG:6933**. The `center_longitude`, `center_latitude` are inverse-transformed from the square center for map use. For geospatial area calculations, the native projected geometry is authoritative.

## `monthly_grid_025deg.csv`

Preserves the basic ETL schema, which is **not** the same as the 0.1° cell indexing scheme:

- `sensor,year,month,grid_x,grid_y,detection_count,sum_detected_pixel_frp_mw,mean_detected_pixel_frp_mw,grid_center_lon,grid_center_lat`.
- Origins are **94°E, 12°S**; step=0.25°.

## `monthly_grid_05deg.csv`, `monthly_grid_1deg.csv`

- `sensor,year,month,cell_x,cell_y,detection_count,sum_detected_pixel_frp_mw,center_longitude,center_latitude`.
- Integer indices are coarsenings of the original 0.25° grid from the **(94°E, 12°S)** origin.

## `sensor_comparison_025deg_raw.csv`

- Join key: `year,month,grid_x,grid_y` of original 0.25° grid.
- `MODIS`, `VIIRS_SNPP`, `VIIRS_NOAA20`: *raw* counts in the same month and cell, missing source entries represented with zero. NO harmonization has occurred.
- `raw_modis_minus_snpp` is a simple numeric difference, not calibrated discrepancy or evidence of model bias.
- `sensor_overlap_period` indicates calendar availability from 2012 onward; it does not guarantee same-day or cloud-free co-observation.

## `recurrence_025deg_by_sensor.csv`

- `sensor,grid_x,grid_y,distinct_years_with_detections,total_detection_count,first_year,last_year`.
- Treat as **observation recurrence**; not true burned-area recurrence or separate fires.

## `example_hover_points_2015_09.csv`

- `sensor,satellite,acq_date,time_utc,latitude,longitude,frp_mw,confidence`.
- Source-level single pixel samples. **Modis confidence is numeric, VIIRS confidence categorical**; never cast both to percent.
- Retained only to demonstrate UX and verify coordinates; it is not the national historical record.

## Input SQL source of individual points

From the **prior** basic ETL `vestigium_hotspots.sqlite`, query:

```sql
SELECT id, sensor, satellite, timestamp_utc, latitude, longitude, frp_mw,
       confidence_modis_pct, confidence_viirs_label, scan_km, track_km
FROM hotspots
WHERE year = ? AND month = ? AND sensor = ?
  AND longitude BETWEEN ? AND ?
  AND latitude BETWEEN ? AND ?
ORDER BY date_utc, time_utc, id
LIMIT ?;
```

Store UTC timestamps as UTC; if showing local Indonesian time, label the timezone and date conversion explicitly.
