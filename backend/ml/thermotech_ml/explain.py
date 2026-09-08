"""
SHAP explanations, turned into sentences a fire officer can read.

The PPT promises "Key factors for decision" on every classification. SHAP
gives us the per-row contribution of each feature to the predicted class;
this module turns the top few into phrases like
"burning 3.4x above its own historical peak".

Only meaningful once a real model is trained — the rule fallback supplies
its own reason string instead.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Plain-English name for every feature in the contract.
FEATURE_LABELS = {
    "frp": "fire radiative power",
    "confidence": "FIRMS confidence level",
    "bright_ti4": "brightness temperature (I4)",
    "bright_ti5": "brightness temperature (I5)",
    "brightness_difference": "I4-I5 brightness difference",
    "scan": "scan footprint size",
    "track": "track footprint size",
    "historical_count": "past detections at this location",
    "historical_frp_mean": "average historical FRP here",
    "historical_frp_max": "peak historical FRP here",
    "persistence_days": "days this location has been thermally active",
    "persistence_ratio": "share of days active",
    "has_baseline": "whether this location has thermal history",
    "frp_zscore": "FRP anomaly vs its own history",
    "is_night": "night-time detection",
    "hour": "hour of acquisition",
    "day_of_week": "day of week",
    "industrial_distance": "distance to nearest industrial site",
    "residential_distance": "distance to nearest residential area",
    "near_industrial": "industrial land use nearby",
    "near_agriculture": "agricultural land use nearby",
    "near_forest": "forest nearby",
    "near_residential": "residential area nearby",
    "near_commercial": "commercial land use nearby",
    "osm_queried": "OSM context was collected",
    "frp_over_hist_max": "FRP relative to its historical peak",
    "frp_over_hist_mean": "FRP relative to its historical average",
    "frp_minus_hist_max": "FRP excess over its historical peak",
    "log_frp": "fire radiative power (log scale)",
    "osm_unknown": "OSM land-use context unavailable",
}


class Explainer:
    """Lazy SHAP wrapper. Falls back to gain importance if SHAP is unavailable."""

    def __init__(self, model, feature_columns: list[str]):
        self.model = model
        self.feature_columns = feature_columns
        self._explainer = None
        self.available = True
        try:
            import shap  # noqa: F401
        except Exception:  # noqa: BLE001
            # Not just ImportError: shap 0.46 raises a TypeError at import time
            # under numpy >= 2. Either way, degrade to predictions without key
            # factors rather than taking the whole API down.
            self.available = False

    def _get(self):
        if self._explainer is None:
            import shap

            self._explainer = shap.TreeExplainer(self.model)
        return self._explainer

    def top_factors(self, X: pd.DataFrame, predicted: np.ndarray, k: int = 3) -> list[list[dict]]:
        """Top-k drivers of the predicted class for each row."""
        if not self.available:
            return [[] for _ in range(len(X))]

        vals = self._get().shap_values(X)
        # shap returns either (n, f, c) or a list of c arrays of (n, f)
        arr = np.stack(vals, axis=-1) if isinstance(vals, list) else np.asarray(vals)
        if arr.ndim == 2:  # binary edge case
            arr = arr[:, :, None]

        out = []
        for i in range(len(X)):
            cls = int(predicted[i])
            contrib = arr[i, :, cls] if arr.shape[2] > cls else arr[i, :, 0]
            order = np.argsort(np.abs(contrib))[::-1][:k]
            row = []
            for j in order:
                name = self.feature_columns[j]
                value = X.iloc[i, j]
                row.append(
                    {
                        "feature": name,
                        "label": FEATURE_LABELS.get(name, name),
                        "value": None if pd.isna(value) else float(value),
                        "contribution": float(contrib[j]),
                        "direction": "supports" if contrib[j] > 0 else "argues against",
                    }
                )
            out.append(row)
        return out


def factors_to_sentence(factors: list[dict], class_name: str) -> str:
    """One-line summary for the dashboard card."""
    if not factors:
        return f"Classified as {class_name}."
    supporting = [f for f in factors if f["contribution"] > 0] or factors
    parts = []
    for f in supporting[:3]:
        v = f["value"]
        parts.append(f["label"] if v is None else f"{f['label']} ({v:.4g})")
    return f"Classified as {class_name}, driven mainly by " + ", ".join(parts) + "."
