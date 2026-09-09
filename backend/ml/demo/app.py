"""
Local test harness for the ThermoTech classifier.

This is NOT the team dashboard — the frontend member owns that. This is a
throwaway rig so the ML member can see what the model is actually doing on
real hotspots, and so the backend member has a working reference for how to
call `classify()` from FastAPI.

Run from `backend/ml/`:

    python -m uvicorn demo.app:app --port 8500 --reload

Then open http://127.0.0.1:8500

Port 8500, not 8000, so it never fights the real backend in `backend/app/`.

It works right now with the rule fallback and picks up the trained model
automatically the moment `models/thermotech_xgb.json` exists — no code change,
no restart flag. The badge in the corner tells you which one answered.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from thermotech_ml.features import CLASS_NAMES  # noqa: E402
from thermotech_ml.paths import UNLABELED_CSV as SAMPLE  # noqa: E402
from thermotech_ml.predict import classify, model_info  # noqa: E402

app = FastAPI(title="ThermoTech classifier — local test harness")


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "index.html")


@app.get("/api/model")
def model():
    return model_info()


@app.get("/api/hotspots")
def hotspots(limit: int = 861):
    """Classify the sample dataset and return results plus a few raw fields.

    The CSV is ordered by source_row_id, which is roughly geographic, so
    `.head(limit)` would show one corner of India. When limit is smaller than
    the file we take an even stride through it instead.
    """
    if not SAMPLE.exists():
        return JSONResponse({"error": f"Sample data missing at {SAMPLE}"}, status_code=500)

    df = pd.read_csv(SAMPLE)
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


@app.post("/api/classify")
def classify_endpoint(records: list[dict]):
    """Reference implementation of the real backend route. POST a list of hotspot dicts."""
    return {"model": model_info(), "results": classify(records)}


def _py(v):
    if hasattr(v, "item"):
        return v.item()
    return v
