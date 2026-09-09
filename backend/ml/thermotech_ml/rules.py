"""
Rule engine — encodes the PPT's "Core Logic" decision tree in plain Python.

It has two jobs:

1. **Pre-labeling assistant.** It suggests a class and a reason for every
   hotspot so a human reviewer confirms or corrects instead of labeling 861
   rows from a blank column. This is a *speed-up for humans*, not ground
   truth: if you train on unreviewed suggestions the model just re-learns
   these thresholds and every metric becomes meaningless.

2. **Safe fallback.** Until a trained model exists, `predict.classify()`
   falls back to these rules so the backend, dashboard and demo are never
   blocked waiting on the ML member. Outputs carry `model: "rules-v1"` so
   nobody mistakes a fallback for a real prediction.

Thresholds live at the top of the file. They are deliberate, defensible
starting points from the handoff data, not tuned parameters — adjust them
after the team has reviewed a first batch.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .features import CLASS_NAMES

# --- thresholds -----------------------------------------------------------
MIN_HISTORY_FOR_PERSISTENT = 5      # historical detections in the same grid cell
MIN_ACTIVE_DAYS = 3                 # distinct historical active days
# NOTE: persistence_ratio is deliberately NOT a gate. It is active-days over
# observed span, so a genuinely long-running flare with a wide history window
# scores LOW on it. Using it as an AND condition dropped the persistent class
# to 4% of the batch, which is wrong.
SPIKE_ZSCORE = 2.0                  # FRP anomaly vs its own history
SPIKE_RATIO_OVER_HIST_MAX = 2.0     # FRP more than 2x its historical peak
STRONG_FRP = 5.65                   # ~75th percentile of the handoff batch
WEAK_FRP = 1.87                     # ~25th percentile


def _row_verdict(r: pd.Series) -> tuple[int, str, float]:
    """Return (label, reason, strength 0-1) for one hotspot."""
    has_base = bool(r.get("has_baseline", 0) == 1)
    hist_n = float(r.get("historical_count", 0) or 0)
    ratio = float(r.get("persistence_ratio", 0) or 0)
    active_days = float(r.get("persistence_days", 0) or 0)
    frp = float(r.get("frp", 0) or 0)
    z = r.get("frp_zscore", np.nan)
    z = float(z) if pd.notna(z) else np.nan
    hist_max = float(r.get("historical_frp_max", 0) or 0)
    over_peak = frp > SPIKE_RATIO_OVER_HIST_MAX * hist_max if hist_max > 0 else False

    spiking = (pd.notna(z) and z >= SPIKE_ZSCORE) or over_peak
    established = (
        has_base
        and hist_n >= MIN_HISTORY_FOR_PERSISTENT
        and active_days >= MIN_ACTIVE_DAYS
    )

    # 1. Established thermal history, burning at its usual level -> persistent source
    if established and not spiking:
        return (
            0,
            f"Recurring cell: {int(hist_n)} historical detections across "
            f"{int(active_days)} active days ({ratio:.0%} of the observed span), "
            "FRP in line with its own history.",
            min(1.0, 0.45 + 0.25 * ratio + 0.015 * min(hist_n, 30)),
        )

    # 2. Established history but burning far above it -> escalation, treat as new event
    if established and spiking:
        return (
            2,
            f"Known thermal cell but FRP is anomalous "
            f"(z={z:.1f}{', above historical peak' if over_peak else ''}) — escalation watch.",
            0.75,
        )

    # 3. No baseline at all + meaningful energy -> new / abnormal
    if not has_base and frp >= STRONG_FRP:
        return (
            2,
            f"No historical thermal baseline for this cell and FRP is high ({frp:.1f}).",
            0.7,
        )

    # 4. Spiking without an established baseline
    if spiking and frp >= WEAK_FRP:
        return (
            2,
            f"FRP anomalous relative to sparse history (z={z:.1f})." if pd.notna(z)
            else "FRP well above the little history this cell has.",
            0.6,
        )

    # 5. Everything else — weak, one-off, or low-confidence detections
    bits = []
    if frp < WEAK_FRP:
        bits.append(f"low FRP ({frp:.1f})")
    if not has_base:
        bits.append("no baseline")
    elif hist_n < MIN_HISTORY_FOR_PERSISTENT:
        bits.append(f"thin history ({int(hist_n)} detections)")
    if r.get("confidence", 0) == 1:
        bits.append("low FIRMS confidence")
    return (
        1,
        "Weak / one-off detection: " + ", ".join(bits) if bits
        else "Does not match a persistent source or a clear anomaly.",
        0.45,
    )


def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Score a whole table. Returns columns: label, class_name, reason, strength."""
    verdicts = [_row_verdict(r) for _, r in df.iterrows()]
    out = pd.DataFrame(verdicts, columns=["label", "reason", "strength"], index=df.index)
    out["class_name"] = out["label"].map(CLASS_NAMES)
    return out[["label", "class_name", "reason", "strength"]]
