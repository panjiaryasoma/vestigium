# VESTIGIUM — Comprehensive NASA FIRMS Indonesia EDA (2000–2025)

**Team Ga Tidur | NASA Space Apps Challenge 2026**

This is the **English-language edition** of the original VESTIGIUM Exploratory Data Analysis (EDA). It preserves the original input dataset, all statistical findings, 20 derived tables, and 17 figures, while translating the report, visual labels, notebook annotations, code outputs, and documentation into English.

## Scope and interpretation

The original analysis covers **48 Indonesia CSV files**, with **6,355,534 thermal-anomaly observations**. A separate Angola file in the uploaded archive was excluded. The main `type=0` analysis includes **5,997,676 presumed vegetation-fire detections** from MODIS, VIIRS S-NPP, and VIIRS NOAA-20 across the available years within 2000–2025.

**A satellite hotspot is not a unique, verified forest fire.** Counts across MODIS and VIIRS must not be summed as distinct fires. Neither the observed FRP nor a hotspot location by itself establishes burned area, ignition cause, or post-fire land use. No sensor harmonization or machine-learning model was fitted in this EDA.

## Primary deliverables

| File / directory | Purpose |
|---|---|
| `VESTIGIUM_EDA_REPORT_EN.html` | **23-section self-contained HTML report** with all 17 images embedded; works offline |
| `VESTIGIUM_EDA_EN.ipynb` | **43-cell Jupyter Notebook**, including 20 executable Python cells and saved outputs |
| `VESTIGIUM_EDA_COMPLETE_EN.md` | Full English-language Markdown report |
| `figures/` | **17 PNG figures**, recreated with English axis labels, titles, and notes |
| `tables/` | **20 CSV/JSON detail tables**, unchanged original EDA results |
| `vestigium_eda.py` | Original full-data, chunked CSV audit and aggregation pipeline |
| `render_eda.py` | Figure generator using the existing aggregates; English chart labels |
| `build_english_report.py` | Regenerates the offline English HTML report from Markdown and images |
| `validate_outputs.py` | Original reconciliation and data-integrity tests |
| `summary.json`, `provenance.json` | Data profile and SHA-256 fingerprint of the original input ZIP |

## Open and review immediately

1. Open `VESTIGIUM_EDA_REPORT_EN.html` in a modern browser. It is self-contained and needs no internet connection.
2. Open `VESTIGIUM_EDA_EN.ipynb` from the same folder as `tables/` and `figures/` using JupyterLab or VS Code.
3. Read `VESTIGIUM_EDA_COMPLETE_EN.md` for a lightweight version with links to the figures.

## Re-run the notebook against the packaged aggregates

```bash
python -m pip install -r requirements.txt
jupyter lab VESTIGIUM_EDA_EN.ipynb
```

All numeric outputs and visualizations can be regenerated from the included CSV/JSON aggregates without parsing the entire raw archive again.

## Regenerate from the original raw archive (optional)

The uploaded `data.zip` is **not included** to avoid redistributing 116 MB of raw user data. Copy it into this folder before starting the following workflow:

```bash
python -m pip install -r requirements.txt
python vestigium_eda.py data.zip .
python render_eda.py
python build_english_report.py
python validate_outputs.py
```

The original input ZIP's SHA-256 digest is stored in `provenance.json`. Do not commit the raw ZIP or large rasters to GitHub.

## Reproducibility and limitations

- Observation timestamps remain in **UTC**. Explicit conversion is required for Indonesian time zones.
- Initial observation years are **partial**: MODIS 2000, S-NPP 2012, NOAA-20 2018.
- The dataset does not include VIIRS NOAA-21.
- MODIS and VIIRS confidence and brightness fields use **different scales / spectral channels**.
- The geographic screening uses an **approximate Indonesia bounding box**, not official administrative boundaries.
- The 0.5° EDA grid measures detection counts, **not hectares burned**.
- Ignition-cause inference requires independent verified labels and auxiliary data; it cannot be justified from these hotspot records alone.

## Original source documentation

- [NASA FIRMS MODIS](https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_MODIS_Firehotspots.html)
- [NASA FIRMS VIIRS](https://firms.modaps.eosdis.nasa.gov/descriptions/FIRMS_VIIRS_Firehotspots.html)
- [NASA FIRMS Archive Download](https://firms.modaps.eosdis.nasa.gov/download/)

**Translation note:** Scientific results were not recomputed with a different method. This English edition reuses the validated original aggregates and re-renders explanatory material and charts in English.
