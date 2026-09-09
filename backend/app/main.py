"""
ThermoTech backend — Phase 1 skeleton with the classifier wired in.

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
PROJECT_ROOT = BACKEND_ROOT.parent

sys.path.insert(0, str(BACKEND_ROOT / "ml"))
sys.path.insert(0, str(PROJECT_ROOT / "risk-engine"))

from thermotech_ml.features import CLASS_NAMES  # noqa: E402
from thermotech_ml.paths import UNLABELED_CSV  # noqa: E402
from thermotech_ml.predict import classify, model_info  # noqa: E402
from risk_engine import calculate_risk  # noqa: E402

app = FastAPI(title="ThermoTech API", version="0.1.0")

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
@app.get("/statistics")
def statistics():
    """Dashboard statistics including ML classification and risk."""

    if not UNLABELED_CSV.exists():
        return JSONResponse(
            {"error": f"Processed dataset not found at {UNLABELED_CSV}"},
            status_code=503,
        )

    df = pd.read_csv(UNLABELED_CSV).reset_index(drop=True)

    # Run the ML classifier
    results = classify(df)

    # Classification counts
    classification_counts = {
        name: 0 for name in CLASS_NAMES.values()
    }

    # Risk severity counts
    severity_counts = {
        "LOW": 0,
        "MEDIUM": 0,
        "HIGH": 0,
        "CRITICAL": 0,
    }

    risk_scores = []

    for i, result in enumerate(results):
        classification_counts[result["classification"]] += 1

        row = df.iloc[i]
        risk = _calculate_event_risk(row, result)

        severity_counts[risk["severity"]] += 1
        risk_scores.append(risk["risk_score"])

    # FRP statistics
    frp = pd.to_numeric(df["frp"], errors="coerce").dropna()

    return {
        "total_hotspots": len(df),
        "classification_counts": classification_counts,
        "risk_severity_counts": severity_counts,
        "average_risk_score": (
            round(sum(risk_scores) / len(risk_scores), 2)
            if risk_scores
            else 0
        ),
        "maximum_risk_score": (
            round(max(risk_scores), 2)
            if risk_scores
            else 0
        ),
        "average_frp": (
            round(float(frp.mean()), 2)
            if not frp.empty
            else 0
        ),
        "maximum_frp": (
            round(float(frp.max()), 2)
            if not frp.empty
            else 0
        ),
    }

@app.get("/trends")
def trends():
    """Return 24-hour FRP trend data from the collected FIRMS dataset."""

    if not UNLABELED_CSV.exists():
        return JSONResponse(
            {"error": f"Processed dataset not found at {UNLABELED_CSV}"},
            status_code=503,
        )

    df = pd.read_csv(UNLABELED_CSV)

    # Convert relevant columns to numeric values
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
    df["frp"] = pd.to_numeric(df["frp"], errors="coerce")
    df["historical_frp_mean"] = pd.to_numeric(
        df["historical_frp_mean"], errors="coerce"
    )

    # Keep valid hourly observations
    df = df.dropna(subset=["hour"])
    df["hour"] = df["hour"].astype(int)

    # Keep only valid 0–23 hour values
    df = df[df["hour"].between(0, 23)]

    # Aggregate collected observations by hour
    grouped = (
        df.groupby("hour")
        .agg(
            average_frp=("frp", "mean"),
            historical_baseline=("historical_frp_mean", "mean"),
            detections=("frp", "count"),
        )
        .reindex(range(24))
    )

    points = []

    for hour in range(24):
        row = grouped.loc[hour]

        points.append(
            {
                "hour": hour,
                "average_frp": (
                    round(float(row["average_frp"]), 2)
                    if pd.notna(row["average_frp"])
                    else 0
                ),
                "historical_baseline": (
                    round(float(row["historical_baseline"]), 2)
                    if pd.notna(row["historical_baseline"])
                    else 0
                ),
                "detections": (
                    int(row["detections"])
                    if pd.notna(row["detections"])
                    else 0
                ),
            }
        )

    return {
        "period": "24-hour",
        "source": "collected NASA FIRMS dataset",
        "points": points,
    }
@app.get("/critical-event")
def critical_event():
    """Return the highest-priority event from the collected dataset."""

    if not UNLABELED_CSV.exists():
        return JSONResponse(
            {"error": f"Processed dataset not found at {UNLABELED_CSV}"},
            status_code=503,
        )

    df = pd.read_csv(UNLABELED_CSV).reset_index(drop=True)

    # Run the existing classifier
    results = classify(df)

    # Attach classification results to each record
    events = []

    for i, result in enumerate(results):
        row = df.iloc[i]

        frp = pd.to_numeric(
            pd.Series([row.get("frp")]), errors="coerce"
        ).iloc[0]

        confidence = result.get("confidence", 0)
        risk = _calculate_event_risk(row, result)

        events.append(
            {
                "index": i,
                "classification": result.get("classification"),
                "risk_score": risk["risk_score"],
                "risk_level": risk["severity"],
                "risk_factors": risk["risk_factors"],
                "ai_confidence": confidence,
                "frp": 0 if pd.isna(frp) else round(float(frp), 2),
                "brightness_temp": (
                    None
                    if pd.isna(row.get("bright_ti4"))
                    else round(float(row.get("bright_ti4")), 2)
                ),
                "historical_persistence_days": (
                    0
                    if pd.isna(row.get("persistence_days"))
                    else round(float(row.get("persistence_days")), 2)
                ),
                "persistence_ratio": (
                    0
                    if pd.isna(row.get("persistence_ratio"))
                    else round(float(row.get("persistence_ratio")) * 100, 2)
                ),
                "historical_baseline": (
                    0
                    if pd.isna(row.get("historical_frp_mean"))
                    else round(float(row.get("historical_frp_mean")), 2)
                ),
                "industrial_distance": (
                    None
                    if pd.isna(row.get("industrial_distance"))
                    else round(float(row.get("industrial_distance")), 2)
                ),
            }
        )



    # Priority order: new abnormal event > persistent source > other anomaly
    priority = {
        "NEW_ABNORMAL_EVENT": 3,
        "PERSISTENT_SOURCE": 2,
        "OTHER_ANOMALY": 1,
    }

    # Select the strongest event based on class priority, then FRP
    events.sort(
        key=lambda event: (
            priority.get(event["classification"], 0),
            event["frp"],
        ),
        reverse=True,
    )

    critical = events[0]

    return {
        "event_id": f"EVT-{critical['index'] + 1:04d}",
        "priority": "PRIORITY 01",
        "classification": critical["classification"],
        "risk_level": critical["risk_level"],
        **critical,
    }

def _calculate_event_risk(row, result):
    """Combine ML classification with contextual risk signals."""

    def safe_value(column):
        value = row.get(column)

        if value is None or pd.isna(value):
            return None

        return _py(value)

    return calculate_risk(
        probabilities=result.get("probabilities"),
        class_id=result.get("class_id"),
        classification=result.get("classification"),
        confidence=result.get("confidence"),
        persistence_days=safe_value("persistence_days") or 0,
        frp_zscore=safe_value("frp_zscore"),
        residential_distance=safe_value("residential_distance"),
    )

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

    for i, result in enumerate(results):
        row = df.iloc[i]

        risk = _calculate_event_risk(row, result)

        result["risk"] = risk

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
    """Classify arbitrary hotspot records and calculate risk."""

    df = pd.DataFrame(records)

    results = classify(records)

    for i, result in enumerate(results):
        row = df.iloc[i]

        risk = _calculate_event_risk(row, result)

        result["risk"] = risk

    return {
        "model": model_info(),
        "results": results,
    }


def _py(v):
    return v.item() if hasattr(v, "item") else v
def _calculate_event_risk(row, result):
    """Combine ML classification with contextual risk signals."""

    def safe_value(column):
        value = row.get(column)

        if value is None or pd.isna(value):
            return None

        return _py(value)

    return calculate_risk(
        probabilities=result.get("probabilities"),
        class_id=result.get("class_id"),
        classification=result.get("classification"),
        confidence=result.get("confidence"),
        persistence_days=safe_value("persistence_days") or 0,
        frp_zscore=safe_value("frp_zscore"),
        residential_distance=safe_value("residential_distance"),
    )