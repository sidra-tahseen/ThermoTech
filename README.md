# GeoFlare — Setup (Stage 0: installations & config)

This is just the installation/configuration stage. No FastAPI or React
logic yet — that's Phase 1, next.

## 1. Backend

```bash
cd GeoFlare/backend
python3 -m venv venv

# activate it
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

Installed: `fastapi`, `uvicorn`, `python-dotenv`, `requests`, `pandas`.
(This is deliberately minimal — GeoPandas/Rasterio/PostGIS/XGBoost/SHAP
come in later phases, not Stage 0.)

## 2. Get a NASA FIRMS MAP_KEY

1. Go to https://firms.modaps.eosdis.nasa.gov/api/map_key/
2. Sign in / register (free), generate a MAP_KEY.
3. Copy `backend/.env.example` to `backend/.env` and paste your key in:

```bash
cp .env.example .env
```

```
FIRMS_MAP_KEY=your_actual_key_here
```

`FIRMS_BBOX` in `.env` is set to a rough Telangana/AP bounding box by
default — change it to whatever region you're demoing.

## 3. Verify the FIRMS key works

```bash
python verify_setup.py
```

This hits FIRMS directly, prints your key's remaining transaction quota,
and pulls a sample of real hotspot rows. If this passes, we're ready
for Phase 1 (actual FastAPI endpoint + React/Leaflet map).

## 4. Frontend

```bash
cd GeoFlare/frontend
npm install
npm run dev
```

Installed: `react`, `react-dom`, `react-leaflet`, `leaflet`, `axios`,
plus `vite` as the dev server/bundler. This starts an empty Vite app on
`http://localhost:5173` — we haven't written `App.jsx` yet, so it'll
just show Vite's default page until Phase 1.

The `vite.config.js` already proxies `/api/*` to `http://localhost:8000`
(where FastAPI will run), so the frontend and backend can talk to each
other without CORS headaches once we write the actual code.

## Project layout so far

```
GeoFlare/
├── backend/
│   ├── app/
│   │   ├── api/          (empty — Phase 1)
│   │   ├── services/      (empty — Phase 1: firms.py goes here)
│   │   ├── models/        (empty — Phase 2)
│   │   └── database/      (empty — Phase 2)
│   ├── ml/                 (empty — Phase 5)
│   ├── requirements.txt
│   ├── .env.example
│   └── verify_setup.py
├── frontend/
│   ├── src/
│   │   ├── components/    (empty — Phase 1: Map.jsx goes here)
│   │   ├── pages/          (empty — Phase 1)
│   │   └── services/       (empty — Phase 1: api.js goes here)
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
└── .gitignore
```

## Next step (Phase 1)

Once `verify_setup.py` confirms real hotspot data is coming back:
- `backend/app/services/firms.py` — fetch + parse FIRMS CSV
- `backend/app/api/hotspots.py` — expose it as a FastAPI endpoint
- `frontend/src/components/Map.jsx` — Leaflet map plotting those hotspots

Say the word and we'll write that next.
