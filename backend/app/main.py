"""
GeoFlare backend — Phase 1 skeleton with the classifier wired in.

NOTE FOR THE BACKEND MEMBER: this file is a stopgap, not a claim on your
work. The repo had no `app/` yet and the ML module needed something to be
reachable through, so this is the thinnest possible thing that works. Rip it
apart, split it into `app/api/` and `app/services/`, add the FIRMS ingest and
the database — none of that touches the ML side. The only rule is that the
classifier is called through `thermotech_ml.predict.classify()` and nowhere
else, so feature handling stays in one place.

Route paths have no `/api` prefix on purpose: `frontend/vite.config.js`
proxies `/api/*` here and strips the prefix, so the React app calls
`/api/hotspots` and this serves `/hotspots`.

Run from `backend/`:

    python -m uvicorn app.main:app --reload
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT / "ml"))

from thermotech_ml.features import CLASS_NAMES  # noqa: E402
from thermotech_ml.paths import UNLABELED_CSV  # noqa: E402
from thermotech_ml.predict import classify, model_info  # noqa: E402

app = FastAPI(title="GeoFlare API", version="0.1.0")

# Vite proxies in dev so this is belt-and-braces, but it saves an afternoon
# the first time someone opens the built frontend from a different origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "classifier": model_info()}


@app.get("/model")
def model():
    return model_info()


@app.get("/hotspots")
def hotspots(limit: int = 861):
    """Classified hotspots from the processed dataset.

    Phase 1 reads the CSV the data-engineering member produced. When live
    FIRMS ingest lands, swap the two lines below for the ingest service —
    the `classify()` call and everything downstream stays identical.
    """
    if not UNLABELED_CSV.exists():
        return JSONResponse(
            {"error": f"Processed dataset not found at {UNLABELED_CSV}"}, status_code=503
        )

    df = pd.read_csv(UNLABELED_CSV)
    if limit < len(df):
        df = df.iloc[:: max(1, len(df) // limit)].head(limit)
    df = df.reset_index(drop=True)

    results = classify(df)

    extras = [
        "frp", "confidence", "historical_count", "historical_frp_mean",
        "historical_frp_max", "persistence_days", "persistence_ratio",
        "frp_zscore", "has_baseline", "is_night", "osm_queried",
        "near_industrial", "industrial_distance",
    ]
    for i, r in enumerate(results):
        row = df.iloc[i]
        r["raw"] = {
            c: (None if pd.isna(row.get(c)) else _py(row.get(c)))
            for c in extras if c in df.columns
        }

    counts = {name: 0 for name in CLASS_NAMES.values()}
    for r in results:
        counts[r["classification"]] += 1

    return {"model": model_info(), "counts": counts, "total": len(results), "hotspots": results}


@app.post("/classify")
def classify_endpoint(records: list[dict]):
    """Classify arbitrary hotspot records. Schema: backend/ml/API_CONTRACT.md."""
    return {"model": model_info(), "results": classify(records)}


def _py(v):
    return v.item() if hasattr(v, "item") else v
