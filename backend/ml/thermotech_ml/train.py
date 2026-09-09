"""
Train the 3-class XGBoost classifier.

Deliberate choices, because the dataset is small:

  * **Stratified 5-fold cross-validation, not a single train/test split.**
    With a few hundred labeled rows one split is mostly luck. CV gives a
    mean and a spread, and the spread is the honest part.
  * **Macro F1 as the headline metric, not accuracy.** The classes are
    unbalanced; accuracy would flatter a model that ignores the rare class.
  * **Class weights** so the rare class still costs something to get wrong.
  * **Shallow trees, few of them.** Deep XGBoost on 200 rows memorises.
  * **No NaN imputation.** Missing OSM context is information; XGBoost
    learns its own default branch for it.

The final saved model is refit on all labeled rows — CV is for estimating
how good it is, the shipped model should see every example available.

Usage:
    python -m thermotech_ml.train
    python -m thermotech_ml.train --data data/training_set.csv --folds 5
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from .features import CLASS_NAMES, FEATURE_COLUMNS, TARGET_COLUMN, build_features, check_data
from .paths import MODEL_DIR, ML_ROOT as ROOT, REPORT_DIR, TRAINING_CSV as DEFAULT_DATA

PARAMS = dict(
    n_estimators=250,
    max_depth=3,
    learning_rate=0.08,
    subsample=0.85,
    colsample_bytree=0.85,
    min_child_weight=2,
    reg_lambda=1.5,
    objective="multi:softprob",
    tree_method="hist",  # num_class is inferred by the sklearn wrapper; passing
                         # it explicitly breaks on some xgboost 2.x builds
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=4,
)

MIN_ROWS = 60
MIN_PER_CLASS = 10


def _new_model() -> XGBClassifier:
    return XGBClassifier(**PARAMS)


def cross_validate(X: pd.DataFrame, y: np.ndarray, folds: int) -> dict:
    n_splits = min(folds, int(pd.Series(y).value_counts().min()))
    if n_splits < 2:
        print("  Not enough rows in the smallest class for cross-validation; skipping.")
        return {}

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    scores, oof = [], np.full(len(y), -1)

    for tr, te in skf.split(X, y):
        m = _new_model()
        m.fit(X.iloc[tr], y[tr], sample_weight=compute_sample_weight("balanced", y[tr]))
        pred = m.predict(X.iloc[te])
        oof[te] = pred
        scores.append(f1_score(y[te], pred, average="macro"))

    labels = sorted(set(y))
    names = [CLASS_NAMES[c] for c in labels]
    print(f"\n  {n_splits}-fold macro F1: {np.mean(scores):.3f} (+/- {np.std(scores):.3f})")
    print(f"  per fold: {', '.join(f'{s:.3f}' for s in scores)}")
    print("\n  Out-of-fold classification report:")
    print(_indent(classification_report(y, oof, labels=labels, target_names=names, zero_division=0)))
    print("  Confusion matrix (rows = true, cols = predicted):")
    cm = confusion_matrix(y, oof, labels=labels)
    print(_indent(pd.DataFrame(cm, index=names, columns=names).to_string()))

    return {
        "folds": n_splits,
        "macro_f1_mean": float(np.mean(scores)),
        "macro_f1_std": float(np.std(scores)),
        "fold_scores": [float(s) for s in scores],
        "confusion_matrix": cm.tolist(),
        "class_order": names,
        "report": classification_report(
            y, oof, labels=labels, target_names=names, zero_division=0, output_dict=True
        ),
    }


def _indent(text: str, pad: str = "    ") -> str:
    return "\n".join(pad + line for line in text.splitlines())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--folds", type=int, default=5)
    args = ap.parse_args()

    if not args.data.exists():
        raise SystemExit(
            f"{args.data} not found.\n"
            "Run `python -m thermotech_ml.prelabel`, get the batch labeled, then "
            "`python -m thermotech_ml.make_dataset`."
        )

    df = pd.read_csv(args.data)
    print(f"Loaded {len(df)} rows from {args.data.name}")

    # Accept the human-readable labels produced by the labeling workflow.
    if df[TARGET_COLUMN].dtype == object:
        label_map = {name: idx for idx, name in CLASS_NAMES.items()}
        df[TARGET_COLUMN] = df[TARGET_COLUMN].map(label_map)
    for line in check_data(df):
        print("  " + line)

    df = df[df[TARGET_COLUMN].notna()].copy()
    y = df[TARGET_COLUMN].astype(int).to_numpy()
    X = build_features(df)

    counts = pd.Series(y).value_counts()
    if len(df) < MIN_ROWS or counts.min() < MIN_PER_CLASS or len(counts) < 3:
        raise SystemExit(
            f"\nRefusing to train: {len(df)} labeled rows, smallest class {counts.min()}, "
            f"{len(counts)} classes present.\n"
            f"Need at least {MIN_ROWS} rows with {MIN_PER_CLASS}+ in each of the 3 classes. "
            "A model fit below that will produce numbers nobody should put on a slide."
        )

    cv = cross_validate(X, y, args.folds)

    print("\n  Refitting on all labeled rows for the shipped model...")
    model = _new_model()
    model.fit(X, y, sample_weight=compute_sample_weight("balanced", y))

    MODEL_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    model.save_model(MODEL_DIR / "thermotech_xgb.json")

    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_labeled_rows": int(len(df)),
        "class_counts": {CLASS_NAMES[int(k)]: int(v) for k, v in counts.items()},
        "feature_columns": FEATURE_COLUMNS,
        "params": {k: v for k, v in PARAMS.items()},
        "cross_validation": cv,
    }
    (MODEL_DIR / "model_meta.json").write_text(json.dumps(meta, indent=2))

    imp = (
        pd.Series(model.feature_importances_, index=FEATURE_COLUMNS)
        .sort_values(ascending=False)
    )
    imp.to_csv(REPORT_DIR / "feature_importance.csv", header=["gain_importance"])
    print("\n  Top 10 features by gain:")
    print(_indent(imp.head(10).to_string()))

    print(f"\nSaved models/thermotech_xgb.json and models/model_meta.json")
    print("Next: `python -m thermotech_ml.predict`")


if __name__ == "__main__":
    main()
