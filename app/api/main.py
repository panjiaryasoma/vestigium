"""VESTIGIUM geospatial serving API.

All fire records are satellite-detected pixels, not unique fires or evidence of cause.
Connect the original pipeline artifacts with the paths in .env.example.
Without those artifacts the API serves explicitly labelled deterministic synthetic demo data.
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import sqlite3
import statistics
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BASE = Path(__file__).resolve().parent
# Existing VESTIGIUM pipeline outputs live under the repository's data/processed/
# directory. Environment variable overrides allow separate deployments or storage.
REPO_ROOT = BASE.parents[1]


def source_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, str(REPO_ROOT / default))).expanduser().resolve()


DB = source_path("VESTIGIUM_DB", "data/processed/data-engineering/vestigium_hotspots.sqlite")
MONTHLY = source_path("VESTIGIUM_MONTHLY_CSV", "data/processed/data-engineering/monthly_sensor.csv")
CALENDAR = source_path("VESTIGIUM_CALENDAR_CSV", "data/processed/harmonization/harmonized_calendar_monthly.csv")
QUALITY = source_path("VESTIGIUM_QUALITY_JSON", "data/processed/data-engineering/quality_report.json")
MODE = "live" if DB.is_file() else "demo"
YEARS = list(range(2000, 2026))
SENSORS = ["MODIS", "VIIRS_SNPP", "VIIRS_NOAA20"]
REGIONS: dict[str, tuple[float, float, float, float]] = {
    "Sumatra": (94.5, -6.5, 106.5, 6.3),
    "Java": (105.0, -9.3, 115.0, -5.5),
    "Kalimantan": (108.0, -4.7, 120.0, 5.0),
    "Sulawesi": (118.0, -6.0, 126.0, 2.5),
    "Papua": (129.0, -10.2, 141.2, 1.8),
    "Bali & Nusa Tenggara": (114.0, -11.9, 126.3, -7.2),
    "Maluku": (125.2, -8.7, 135.5, 3.1),
}
# Demo-only synthetic point centers, with a few provinces as context. They are NOT data.
DEMO_CENTERS = [
    (101.2, 0.6, "Riau", 1.4), (103.8, -3.3, "South Sumatra", 1.3),
    (102.5, -1.3, "Jambi", 0.75), (99.3, 1.7, "North Sumatra", .6),
    (111.5, -0.5, "West Kalimantan", 1.4), (113.7, -2.2, "Central Kalimantan", 2.1),
    (115.0, -3.3, "South Kalimantan", 1.1), (117.4, 0.8, "East Kalimantan", .9),
    (120.4, -2.3, "Central Sulawesi", .55), (122.5, -8.8, "East Nusa Tenggara", .6),
    (138.5, -5.0, "Papua", .65), (132.0, -1.3, "West Papua", .4),
]

app = FastAPI(title="VESTIGIUM | Fire Archive API", version="0.1.0", docs_url="/api/docs", redoc_url=None)
origins = [v.strip() for v in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if v.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], allow_headers=["*"])


def database():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    return con


def intersect(bbox: tuple[float, float, float, float], region: str | None):
    if not region:
        return bbox
    if region not in REGIONS:
        raise HTTPException(422, "Unknown region")
    a, b, c, d = bbox
    x, y, z, w = REGIONS[region]
    return max(a, x), max(b, y), min(c, z), min(d, w)


def validate_bbox(value: str) -> tuple[float, float, float, float]:
    try:
        a, b, c, d = [float(x.strip()) for x in value.split(",")]
    except (ValueError, TypeError):
        raise HTTPException(422, "bbox must be min_lon,min_lat,max_lon,max_lat") from None
    if not all(math.isfinite(x) for x in (a, b, c, d)) or not (-180 <= a < c <= 180 and -90 <= b < d <= 90):
        raise HTTPException(422, "Invalid bbox coordinate range")
    return a, b, c, d


def to_feature(record: dict) -> dict:
    return {
        "type": "Feature", "geometry": {"type": "Point", "coordinates": [record["longitude"], record["latitude"]]},
        "properties": {key: value for key, value in record.items() if key not in ("longitude", "latitude")}
    }


@lru_cache(maxsize=400)
def demo_points(year: int, month: int) -> tuple[dict, ...]:
    if year == 2000 and month < 11:
        return tuple()
    rng = random.Random(year * 100 + month + 937)
    wet = 0.5 + 1.35 * max(0, math.sin((month - 5) * math.pi / 7))
    elnino = 2.35 if year in (2002, 2006, 2015, 2019, 2023) else 1
    count = max(30, round(45 * wet * elnino))
    weights = [c[3] for c in DEMO_CENTERS]
    records = []
    for i in range(count):
        lon, lat, province, _ = rng.choices(DEMO_CENTERS, weights=weights, k=1)[0]
        longitude = round(max(94.8, min(140.8, rng.gauss(lon, .42))), 5)
        latitude = round(max(-11.0, min(5.9, rng.gauss(lat, .35))), 5)
        day = rng.randint(1, 28)
        hour = rng.randint(0, 23)
        minute = rng.randint(0, 59)
        sensor = rng.choice(["MODIS"] if year < 2012 else (["MODIS", "VIIRS_SNPP"] if year < 2018 else SENSORS))
        records.append({
            "id": f"synthetic-{year}-{month:02d}-{i:04d}",
            "longitude": longitude, "latitude": latitude,
            "timestamp_utc": f"{year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00Z",
            "date_utc": f"{year}-{month:02d}-{day:02d}", "sensor": sensor,
            "satellite": "Synthetic reference", "frp_mw": round(rng.uniform(5, 110), 1),
            "confidence_modis_pct": round(rng.uniform(40, 98)) if sensor == "MODIS" else None,
            "confidence_viirs_label": rng.choice(["l", "n", "h"]) if sensor != "MODIS" else None,
            "province": province,
            "synthetic": True,
        })
    return tuple(records)


@lru_cache(maxsize=1)
def monthly_rows() -> tuple[dict, ...]:
    if MODE == "live":
        if MONTHLY.is_file():
            with MONTHLY.open(newline="", encoding="utf-8-sig") as f:
                rows = [{"year": int(r["year"]), "month": int(r["month"]), "sensor": r["sensor"],
                         "detection_count": int(float(r["detection_count"]))} for r in csv.DictReader(f)]
            return tuple(rows)
        with database() as con:
            rows = con.execute("SELECT year,month,sensor,COUNT(*) AS detection_count FROM hotspots GROUP BY year,month,sensor").fetchall()
            return tuple(dict(r) for r in rows)
    result = []
    for y in YEARS:
        for m in range(1, 13):
            counts = {s: 0 for s in SENSORS}
            for point in demo_points(y, m):
                counts[point["sensor"]] += 1
            for sensor in SENSORS:
                if (sensor == "VIIRS_SNPP" and y < 2012) or (sensor == "VIIRS_NOAA20" and y < 2018):
                    continue
                result.append({"year": y, "month": m, "sensor": sensor, "detection_count": counts[sensor]})
    return tuple(result)


@lru_cache(maxsize=1)
def calendar_rows() -> tuple[dict, ...]:
    if MODE != "live" or not CALENDAR.is_file():
        return tuple()
    with CALENDAR.open(newline="", encoding="utf-8-sig") as f:
        rows = []
        for record in csv.DictReader(f):
            out = dict(record)
            for key in ("year", "month"):
                out[key] = int(out[key])
            for key in ("MODIS", "VIIRS_SNPP", "VIIRS_NOAA20", "modis_reference_equivalent_proxy", "calendar_display_estimate"):
                raw = out.get(key)
                out[key] = round(float(raw), 2) if raw not in (None, "") else None
            rows.append(out)
        return tuple(rows)


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": MODE, "database_available": DB.is_file(), "calendar_available": MODE == "live" and CALENDAR.is_file()}


@app.get("/api/v1/meta")
def meta():
    return {
        "product": "VESTIGIUM", "mode": MODE, "synthetic": MODE == "demo", "years": YEARS,
        "sensors": SENSORS, "regions": list(REGIONS),
        "has_harmonization_calendar": MODE == "live" and CALENDAR.is_file(),
        "message": ("SYNTHETIC DEMONSTRATION. Coordinates, dates, and quantities are generated examples, NOT NASA observations."
                    if MODE == "demo" else "NASA FIRMS dataset configured; individual records are thermal pixel detections, not separate fires."),
        "time_zone": "UTC", "observation_unit": "satellite_thermal_pixel_detection_not_unique_fire_event",
        "viewport_note": "Regions are geographic bounding areas, not province polygons."
    }


@app.get("/api/v1/hotspots")
def hotspots(
    year: int = Query(2015, ge=2000, le=2025), month: int = Query(9, ge=1, le=12),
    sensor: Literal["ALL", "MODIS", "VIIRS_SNPP", "VIIRS_NOAA20"] = "ALL",
    region: str | None = None, bbox: str = "94,-12,142,7", limit: int = Query(1800, ge=1, le=5000)
):
    bounds = intersect(validate_bbox(bbox), region)
    a, b, c, d = bounds
    if a >= c or b >= d:
        return {"type": "FeatureCollection", "features": [], "meta": {"returned": 0, "limit": limit, "sampled": False, "synthetic": MODE == "demo"}}
    if MODE == "demo":
        records = [p for p in demo_points(year, month)
                   if a <= p["longitude"] <= c and b <= p["latitude"] <= d
                   and (sensor == "ALL" or p["sensor"] == sensor)]
        total = len(records)
        records = records[:limit]
    else:
        clauses = ["year=?", "month=?", "longitude>=?", "longitude<=?", "latitude>=?", "latitude<=?"]
        params: list = [year, month, a, c, b, d]
        if sensor != "ALL":
            clauses.append("sensor=?")
            params.append(sensor)
        with database() as con:
            rows = con.execute(
                "SELECT id,longitude,latitude,timestamp_utc,date_utc,sensor,satellite,frp_mw,confidence_modis_pct,confidence_viirs_label "
                f"FROM hotspots WHERE {' AND '.join(clauses)} ORDER BY id LIMIT ?",
                [*params, limit + 1]
            ).fetchall()
        total = len(rows)
        records = [dict(r) for r in rows[:limit]]
        for r in records:
            r["synthetic"] = False
    return {"type": "FeatureCollection", "features": [to_feature(r) for r in records],
            "meta": {"returned": len(records), "limit": limit, "truncated": total > limit,
                     "synthetic": MODE == "demo", "sampled": False,
                     "note": "Viewport-limited detections. Counts are not exhaustive when truncated."}}


@app.get("/api/v1/temporal")
def temporal(year: int | None = Query(None, ge=2000, le=2025), sensor: Literal["ALL", "MODIS", "VIIRS_SNPP", "VIIRS_NOAA20"] = "ALL",
             grain: Literal["monthly", "annual"] = "monthly"):
    result: dict[tuple[int, int | None], int] = {}
    for record in monthly_rows():
        if year is not None and int(record["year"]) != year:
            continue
        if sensor != "ALL" and record["sensor"] != sensor:
            continue
        key = (int(record["year"]), int(record["month"]) if grain == "monthly" else None)
        result[key] = result.get(key, 0) + int(record["detection_count"])
    data = [{"year": y, "month": m, "count": count, "date": f"{y}-{m:02d}" if m else str(y)}
            for (y, m), count in sorted(result.items())]
    return {"grain": grain, "sensor": sensor, "year": year, "data": data, "synthetic": MODE == "demo",
            "unit": "thermal_pixel_detections_not_fire_events",
            "warning": "Raw sensor detections cannot be summed into a harmonized fire-event count."}


@app.get("/api/v1/calendar")
def calendar(year: int = Query(2015, ge=2000, le=2025)):
    records = [r for r in calendar_rows() if r["year"] == year]
    if not records:
        return {"available": False, "year": year, "data": [], "synthetic": MODE == "demo",
                "warning": "No harmonization artifact configured. Showing raw detections separately is not calibration."}
    return {"available": True, "year": year, "data": records, "synthetic": False,
            "unit": "historical_MODIS_proxy_or_observed_VIIRS_SNPP_detected_pixel_count",
            "warning": "Experimental MODIS-positive-cell calibration. Structural break in 2012; no causal or fire-area inference."}


@app.get("/api/v1/analysis")
def analysis(year: int = Query(2015, ge=2000, le=2025)):
    monthly = monthly_rows()
    by_period: dict[tuple[int, int], int] = {}
    for r in monthly:
        key = (int(r["year"]), int(r["month"]))
        by_period[key] = by_period.get(key, 0) + int(r["detection_count"])
    findings = []
    for month in range(1, 13):
        value = by_period.get((year, month), 0)
        history = [by_period[(y, month)] for y in YEARS if y != year and (y, month) in by_period]
        if not history:
            continue
        median = statistics.median(history)
        mad = statistics.median([abs(v - median) for v in history])
        robust_z = (value - median) / max(1., 1.4826 * mad)
        findings.append({"month": month, "count": value, "baseline_median": round(median),
                         "deviation_score": round(robust_z, 2),
                         "classification": "Unusually elevated" if robust_z > 2.5 else "Within broad historical range"})
    findings.sort(key=lambda r: r["deviation_score"], reverse=True)
    return {"year": year, "findings": findings, "synthetic": MODE == "demo",
            "method": "Exploratory robust MAD comparison of raw multi-sensor monthly detection counts (not a trained cause classifier).",
            "warning": "Satellite coverage and sensor sensitivity differ through time. Scores cannot establish ignition cause, arson, or distinct fire events."}


@app.get("/api/v1/evaluation")
def evaluation():
    """Provenance-labelled archived evidence, NOT an inference run of this API."""
    return {
        "kind": "archived_historical_experiment_report_not_new_model_rerun",
        "as_of": "2026-11-15", "test_period": "2023–2025", "test_grid_months": 17291,
        "reference": "VIIRS S-NPP observations, MODIS-positive 25km grid-months only",
        "metrics": [
            {"method": "Raw MODIS", "mae": 15.67, "rmse": 43.59, "spearman": 0.634},
            {"method": "Global scaling", "mae": 11.56, "rmse": 21.87, "spearman": 0.634},
            {"method": "Seasonal scaling", "mae": 11.15, "rmse": 22.30, "spearman": 0.661},
            {"method": "Poisson ML", "mae": 10.24, "rmse": 24.68, "spearman": 0.730},
        ],
        "source": "VESTIGIUM repository: docs/harmonization/evidence/archived_metrics_2026-11-15.json",
        "warning": "Archived reported metrics. Reconstructed training pipeline has not been independently re-run on the entire original source archive."
    }


@app.get("/api/v1/data-quality")
def data_quality():
    if MODE == "live" and QUALITY.is_file():
        try:
            return {"available": True, "report": json.loads(QUALITY.read_text(encoding="utf-8")), "synthetic": False}
        except (OSError, ValueError):
            raise HTTPException(500, "Data quality report is unreadable") from None
    return {"available": False, "report": None, "synthetic": MODE == "demo",
            "warning": "No validated quality report artifact configured."}
