"""
The one function the rest of the system calls.

    from thermotech_ml.predict import classify
    results = classify(list_of_hotspot_dicts)

`classify` always returns the same shape, whether a trained model exists or
not. If `models/thermotech_xgb.json` is missing it transparently falls back
to the rule engine and stamps `"model": "rules-v1"` on every result, so the
backend, the dashboard and the demo can be built and tested today and get
better silently the moment the model lands. Nothing downstream has to change.

Output per hotspot:

    {
      "source_row_id": 136,
      "latitude": 7.9979,
      "longitude": 80.38068,
      "acq_datetime": "2026-09-05 08:13:00",
      "class_id": 2,
      "classification": "NEW_ABNORMAL_EVENT",
      "confidence": 0.87,
      "probabilities": {"PERSISTENT_SOURCE": 0.05, "OTHER_ANOMALY": 0.08,
                        "NEW_ABNORMAL_EVENT": 0.87},
      "key_factors": [{"feature": "frp_over_hist_max", "label": "...",
                       "value": 3.4, "contribution": 1.21,
                       "direction": "supports"}, ...],
      "explanation": "Classified as NEW_ABNORMAL_EVENT, driven mainly by ...",
      "model": "xgboost-1"
    }

CLI (from backend/ml/):
    python -m thermotech_ml.predict
"""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .explain import Explainer, factors_to_sentence
from .features import CLASS_NAMES, FEATURE_COLUMNS, ID_COLUMNS, build_features
from .paths import META_PATH, ML_ROOT as ROOT, MODEL_PATH, REPORT_DIR, UNLABELED_CSV
from .rules import apply_rules


@lru_cache(maxsize=1)
def _load_model():
    """Load once per process. Returns (model, explainer) or (None, None)."""
    if not MODEL_PATH.exists():
        return None, None
    from xgboost import XGBClassifier

    model = XGBClassifier()
    model.load_model(str(MODEL_PATH))
    return model, Explainer(model, FEATURE_COLUMNS)


def model_info() -> dict:
    """What the backend can show on a /health or /model endpoint."""
    if not MODEL_PATH.exists():
        return {"model": "rules-v1", "trained": False,
                "note": "No trained model yet — rule engine in use."}
    meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
    if meta.get("bootstrap"):
        # Trained on rule-generated labels. Never present this as a validated
        # model: no macro_f1 field, and the name says what it is.
        return {
            "model": "xgboost-bootstrap",
            "trained": True,
            "validated": False,
            "trained_at": meta.get("trained_at"),
            "label_source": meta.get("label_source"),
            "agreement_with_rules": meta.get("agreement_with_rules"),
            "warning": meta.get("warning"),
        }
    return {
        "model": "xgboost-1",
        "trained": True,
        "validated": True,
        "trained_at": meta.get("trained_at"),
        "n_labeled_rows": meta.get("n_labeled_rows"),
        "macro_f1": meta.get("cross_validation", {}).get("macro_f1_mean"),
    }


def classify(records, explain: bool = True) -> list[dict]:
    """Classify hotspots. `records` may be a DataFrame, a list of dicts, or one dict."""
    if isinstance(records, dict):
        records = [records]
    df = records.copy() if isinstance(records, pd.DataFrame) else pd.DataFrame(records)
    if df.empty:
        return []
    df = df.reset_index(drop=True)

    model, explainer = _load_model()
    ids = {c: (df[c] if c in df.columns else pd.Series([None] * len(df))) for c in ID_COLUMNS}

    if model is None:
        verdicts = apply_rules(df)
        return [
            {
                **{c: _clean(ids[c].iloc[i]) for c in ID_COLUMNS},
                "class_id": int(verdicts["label"].iloc[i]),
                "classification": verdicts["class_name"].iloc[i],
                "confidence": round(float(verdicts["strength"].iloc[i]), 3),
                "probabilities": None,
                "key_factors": [],
                "explanation": verdicts["reason"].iloc[i],
                "model": "rules-v1",
            }
            for i in range(len(df))
        ]

    model_name = model_info()["model"]
    X = build_features(df)
    proba = model.predict_proba(X)
    pred = proba.argmax(axis=1)
    factors = explainer.top_factors(X, pred) if explain else [[] for _ in range(len(df))]

    results = []
    for i in range(len(df)):
        name = CLASS_NAMES[int(pred[i])]
        results.append(
            {
                **{c: _clean(ids[c].iloc[i]) for c in ID_COLUMNS},
                "class_id": int(pred[i]),
                "classification": name,
                "confidence": round(float(proba[i].max()), 3),
                "probabilities": {
                    CLASS_NAMES[c]: round(float(proba[i][c]), 3) for c in range(proba.shape[1])
                },
                "key_factors": factors[i],
                "explanation": factors_to_sentence(factors[i], name),
                "model": model_name,
            }
        )
    return results


def _clean(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return v.item() if hasattr(v, "item") else v


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=UNLABELED_CSV)
    ap.add_argument("--out-csv", type=Path, default=REPORT_DIR / "predictions.csv")
    ap.add_argument("--out-json", type=Path, default=REPORT_DIR / "predictions.json")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    results = classify(df)

    info = model_info()
    print(f"Model in use: {info['model']}" + ("" if info["trained"] else "  (fallback)"))
    print(f"Classified {len(results)} hotspots")

    flat = pd.DataFrame(
        [{**{k: v for k, v in r.items() if k not in ("probabilities", "key_factors")},
          **{f"p_{k}": v for k, v in (r["probabilities"] or {}).items()}}
         for r in results]
    )
    args.out_csv.parent.mkdir(exist_ok=True)
    flat.to_csv(args.out_csv, index=False)
    args.out_json.write_text(json.dumps(results, indent=2))

    print("\nPredicted class distribution:")
    for name, cnt in flat["classification"].value_counts().items():
        print(f"  {name:<20} {cnt:>4}  ({cnt / len(flat):.0%})")
    print(f"\nWrote {args.out_csv.relative_to(ROOT)} and {args.out_json.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
