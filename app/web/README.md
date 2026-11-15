# VESTIGIUM | Web

Interactive research atlas · React 18 + TypeScript + Vite + MapLibre GL JS.

## Local development

```bash
cd app/web
npm install
npm run dev
```

Open http://localhost:5173. Start the backend in `app/api` first, using `uvicorn main:app --reload --port 8000`. Vite proxies `/api` requests to localhost:8000.

## Build

```bash
npm run build
npm run preview
```

Vite places production files in `web/dist/`. To deploy a static frontend on Vercel, set the Root Directory to `app/web`, Framework Preset to Vite, Build Command to `npm run build`, and Output Directory to `dist`. In hosting, set `VITE_API_BASE_URL` to the deployed FastAPI origin. Configure the backend `CORS_ORIGINS` accordingly. If your host doesn't provide SPA rewrites, route all paths to `index.html`.

## Visual system

Design system: **Investigative Brutalist Noir**. Primary inspiration: Darkroom Engineering, blended with Brimstone UXO (GIS map), Forensic Architecture (evidence/investigation), and Forbidden Stories (editorial impact). This is an original implementation, not a copy of any site's code or assets.

Palette: obsidian `#0c0d0e`, charcoal `#242424`, ivory `#f0ede5`, antique `#b3a58c`, signal red `#d84a40`. Signal red denotes thermal detections and meaningful research signals, not decorative UI noise.

Routes:
- `/`: editorial cinematic landing.
- `/explore`: map, clustered red detections, UTC hover, clicked evidence record, satellite/month/year/region filters, monthly timeline.
- `/archive`: 2000–2025 detection heatmap, annual timeline, conditional harmonized monthly records.
- `/analysis`: provenance-labeled archived model comparison, exploratory monthly anomaly scan, evidence limits.
- `/impact`: narrative framework for future post-fire land-cover analysis; no invented field conclusions.
- `/methodology`: source and uncertainty statements.

## Important limitations

The application source does not contain the raw NASA database. If the backend has no SQLite file, it provides synthetic demo data and visibly labels it as **SYNTHETIC DEMO**, not NASA observations. The API automatically discovers the repository's `data/processed/` pipeline outputs when present. See `app/api/README.md` for optional backend environment variable overrides.

The CARTO/OSM raster-vector basemap and Google fonts require an internet connection at runtime. All hotspot records are served from your API; the external basemap is for cartographic context only. Region filters use approximate large-island bounding extents, not true Indonesian administrative province polygons. Accurate province filters require an independent validated ADM1 spatial join.
