"""
ThermoTech — feature contract.

This is the SINGLE SOURCE OF TRUTH for what goes into the model.
Training, prediction and the backend all import from here, so the feature
order can never drift between them.

Two data-quality decisions are baked in here on purpose. Read them before
changing anything:

1. `road_distance` is dropped. It is 100% NaN in the handoff data and the
   data-engineering notebook never collected it. It must not be fabricated
   from another OSM category.

2. OSM context columns (`near_industrial`, distances, ...) are set to NaN
   for rows where `osm_queried == 0`. In the raw file those rows have 0,
   which means "we never checked", NOT "there is no industry nearby".
   Only 46 of 861 rows were actually queried. If we left them as 0 the
   model would learn "near_industrial == 1 => industrial fire" purely
   because those are the only rows anyone looked at. XGBoost handles NaN
   natively and learns a proper "unknown" branch instead. An explicit
   `osm_unknown` flag is added so the model can also use the missingness
   itself as a signal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Classes (fixed by the team's labeling scheme — do not renumber)
# --------------------------------------------------------------------------
CLASS_NAMES = {
    0: "PERSISTENT_SOURCE",
    1: "OTHER_ANOMALY",
    2: "NEW_ABNORMAL_EVENT",
}
CLASS_IDS = {v: k for k, v in CLASS_NAMES.items()}

# --------------------------------------------------------------------------
# Columns
# --------------------------------------------------------------------------
OSM_FLAG_COLUMNS = [
    "near_industrial",
    "near_agriculture",
    "near_forest",
    "near_residential",
    "near_commercial",
]
OSM_DISTANCE_COLUMNS = ["industrial_distance", "residential_distance"]

# Never used. Present in the raw files but always NaN.
EXCLUDED_COLUMNS = ["road_distance"]

BASE_FEATURES = [
    "frp",
    "confidence",
    "historical_count",
    "historical_frp_mean",
    "historical_frp_max",
    "persistence_days",
    "persistence_ratio",
    "has_baseline",
    "frp_zscore",
    "bright_ti4",
    "bright_ti5",
    "brightness_difference",
    "is_night",
]

# These are intentionally excluded from the classifier:
# OSM context (sparse/unknown in the current labeled batch), coordinates,
# acquisition identifiers, and rule-generated suggestion fields.
FEATURE_COLUMNS = BASE_FEATURES

TARGET_COLUMN = "label"

# Columns kept alongside predictions so results can be mapped back to a map pin
ID_COLUMNS = ["source_row_id", "latitude", "longitude", "acq_datetime"]

_EPS = 1e-6


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the exact 13-feature classifier input in a stable order."""
    out = df.copy()
    for col in FEATURE_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan

    for col in ("has_baseline", "is_night"):
        out[col] = (
            out[col]
            .map({True: 1, False: 0, "True": 1, "False": 0,
                  "true": 1, "false": 0})
            .fillna(out[col])
        )

    out[FEATURE_COLUMNS] = out[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan)
    return out[FEATURE_COLUMNS].astype("float64")


def check_data(df: pd.DataFrame) -> list[str]:
    """Cheap sanity report. Returns a list of human-readable warnings."""
    problems: list[str] = []
    n = len(df)
    if n == 0:
        return ["Dataset is empty."]

    if TARGET_COLUMN in df.columns:
        labeled = df[TARGET_COLUMN].notna().sum()
        problems.append(f"{labeled}/{n} rows carry a label.")
        if labeled:
            counts = df[TARGET_COLUMN].dropna().astype(int).value_counts().sort_index()
            for cls, cnt in counts.items():
                problems.append(f"  class {cls} ({CLASS_NAMES.get(cls, '?')}): {cnt}")
            missing = set(CLASS_NAMES) - set(counts.index)
            for cls in sorted(missing):
                problems.append(
                    f"  WARNING: class {cls} ({CLASS_NAMES[cls]}) has no labeled rows."
                )
    else:
        problems.append("No `label` column present — this file cannot be trained on.")

    if "osm_queried" in df.columns:
        queried = int(pd.to_numeric(df["osm_queried"], errors="coerce").fillna(0).sum())
        problems.append(
            f"OSM context available for {queried}/{n} rows "
            f"({100 * queried / n:.1f}%) — the rest are treated as unknown, not absent."
        )

    for col in EXCLUDED_COLUMNS:
        if col in df.columns and df[col].notna().any():
            problems.append(
                f"NOTE: `{col}` now has values but is excluded by the feature contract. "
                "Add it to BASE_FEATURES and retrain if it is genuinely collected."
            )

    feats = build_features(df)
    constant = [c for c in feats.columns if feats[c].nunique(dropna=True) <= 1]
    if constant:
        problems.append(
            "Zero-variance features in this batch (harmless, ignored by the model): "
            + ", ".join(constant)
        )

    return problems
