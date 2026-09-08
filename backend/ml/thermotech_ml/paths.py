"""
Where everything lives, in one place.

The repo layout is:

    ThermoTech/
      backend/
        app/            FastAPI
        ml/             <- this module
          thermotech_ml/
          data/labeling/
          models/
          reports/
      data/
        processed/      <- the data-engineering handoff CSVs live here

The hotspot CSVs are NOT copied into this folder. They stay where the
data-engineering member put them, in `data/processed/` at the repo root, so
there is exactly one copy and re-running their notebooks updates ours too.
"""

from __future__ import annotations

from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent.parent          # backend/ml
REPO_ROOT = ML_ROOT.parent.parent                         # repo root
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

LABEL_DIR = ML_ROOT / "data" / "labeling"
MODEL_DIR = ML_ROOT / "models"
REPORT_DIR = ML_ROOT / "reports"

UNLABELED_CSV = PROCESSED_DIR / "thermotech_ml_ready_unlabeled.csv"
TRAINING_CSV = ML_ROOT / "data" / "training_set.csv"

MODEL_PATH = MODEL_DIR / "thermotech_xgb.json"
META_PATH = MODEL_DIR / "model_meta.json"


def require(path: Path, hint: str = "") -> Path:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}\n{hint}".rstrip())
    return path
