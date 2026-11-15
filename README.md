# VESTIGIUM
**Earth remembers what fire leaves behind.**

An evidence-focused exploration of historical satellite fire detections in Indonesia, built by **Team Ga Tidur** for **NASA Space Apps Challenge 2026**.

## Project goal

VESTIGIUM aims to make MODIS and VIIRS active-fire observations easier to explore and compare over time. The planned application combines an interactive Indonesia map, date and sensor filters, individual hotspot metadata, monthly/yearly summaries, and a research-backed sensor-harmonization baseline.

**Selected challenge:** Harmonization of MODIS and VIIRS Hot Spots.

## Scientific boundaries

- A satellite hotspot is a *thermal detection in a sensor pixel*, not proof of a unique fire incident, an ignition point, or burned area.
- MODIS and VIIRS have different detection capabilities. Their raw counts must not be treated as directly equivalent.
- Patterns in active-fire data alone **cannot establish intentional burning or identify a perpetrator**.
- Proposed post-fire land-cover tracking is a separate, future module requiring burned-area and land-cover data and independent validation.

## Intended modules

| Module | Purpose |
| --- | --- |
| `eda/` | Exploratory analysis and sensor-specific data-quality reports |
| `data_engineering/` | Raw-data validation, normalization, indexed storage, and temporal aggregates |
| `geospatial/` | Spatial validation, gridding, mapping, and geospatial QA |
| `harmonization/` | MODIS–VIIRS calibration baselines, models, evaluations, and uncertainty |
| `backend/` | API for map, hover detail, filters, and historical summaries |
| `frontend/` | Interactive investigative atlas, timeline, and analysis UI |
| `docs/` | Methods, provenance, citations, limitations, and team documentation |

These are **planned paths**, not a claim that every module is already committed.

## Data sources

- [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/) for MODIS and VIIRS active-fire detections.
- Future land-cover / burned-area analysis may reference [MapBiomas Indonesia](https://mapbiomas.id/) and other verified imagery sources.

**Data stewardship:** raw CSVs, large intermediate exports, trained model binaries, and SQLite databases are not stored directly in this Git repository. Track download instructions, schemas, reproducible scripts, and small non-sensitive examples instead.

## Interface direction

Darkroom-inspired investigative editorial design, with interaction patterns informed by scientific GIS and accessible map-based exploration. Visual identity must never obscure data uncertainty.

## Status

Repository organization is being established. Analysis packages will be added as separate, reviewable commits after inspecting and validating their contents.

## Attribution

Team Ga Tidur · NASA Space Apps Challenge 2026

This project is an independent participant project and is not an official NASA product.
