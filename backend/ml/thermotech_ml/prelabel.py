"""
Build the human review queue.

The handoff data has 861 hotspots and zero labels, so nothing can be trained
yet. Asking a teammate to label 861 blank rows by eye is how a hackathon
weekend disappears. This script instead:

  * runs the rule engine to attach a *suggested* class and a plain-English
    reason to every row,
  * ranks rows so the clearest examples of each class come first,
  * writes a balanced first batch that one person can get through in well
    under an hour.

The reviewer's only job is to put 0, 1 or 2 in the `label` column —
agreeing with the suggestion or overriding it. Overrides are the valuable
part: they are what stops the model from being a copy of the rules.

Usage:
    python -m thermotech_ml.prelabel
    python -m thermotech_ml.prelabel --batch-size 240
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .features import CLASS_NAMES, ID_COLUMNS
from .paths import LABEL_DIR as OUT_DIR, ML_ROOT as ROOT, UNLABELED_CSV as DEFAULT_SOURCE
from .rules import apply_rules

REVIEW_COLUMNS = [
    *ID_COLUMNS,
    "suggested_label",
    "suggested_class",
    "why_suggested",
    "label",  # <- the reviewer fills this in
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
    "osm_queried",
    "near_industrial",
    "near_residential",
    "near_agriculture",
    "industrial_distance",
    "residential_distance",
]


def build_queue(df: pd.DataFrame) -> pd.DataFrame:
    verdicts = apply_rules(df)
    q = df.copy()
    q["suggested_label"] = verdicts["label"]
    q["suggested_class"] = verdicts["class_name"]
    q["why_suggested"] = verdicts["reason"]
    q["_strength"] = verdicts["strength"]
    q["label"] = pd.NA

    for col in REVIEW_COLUMNS:
        if col not in q.columns:
            q[col] = pd.NA

    # Interleave classes so any prefix of the file is roughly balanced,
    # clearest-first inside each class.
    q = q.sort_values("_strength", ascending=False)
    q["_rank_in_class"] = q.groupby("suggested_label").cumcount()
    q = q.sort_values(["_rank_in_class", "suggested_label"]).reset_index(drop=True)

    return q[REVIEW_COLUMNS]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--batch-size", type=int, default=180,
                    help="rows in the first labeling batch (default 180, ~60 per class)")
    args = ap.parse_args()

    df = pd.read_csv(args.source)
    queue = build_queue(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    full_path = OUT_DIR / "review_queue_full.csv"
    batch_path = OUT_DIR / "batch_01_to_label.csv"
    queue.to_csv(full_path, index=False)
    queue.head(args.batch_size).to_csv(batch_path, index=False)

    print(f"Read {len(df)} hotspots from {args.source.name}")
    print("\nRule-engine suggestions across the full set:")
    counts = queue["suggested_label"].value_counts().sort_index()
    for cls, cnt in counts.items():
        print(f"  {cls} {CLASS_NAMES[cls]:<20} {cnt:>4}  ({cnt / len(queue):.0%})")

    print(f"\nWrote {full_path.relative_to(ROOT)}  ({len(queue)} rows)")
    print(f"Wrote {batch_path.relative_to(ROOT)}  ({min(args.batch_size, len(queue))} rows)")
    print("\nNext: someone fills the `label` column in the batch file, saves it as")
    print("      data/labeling/batch_01_labeled.csv, then run `python -m thermotech_ml.make_dataset`.")


if __name__ == "__main__":
    main()
