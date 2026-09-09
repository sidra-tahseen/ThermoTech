"""
Merge whatever has been labeled so far into one training set.

Picks up every `data/labeling/*_labeled.csv`, keeps rows where `label` is
filled with 0/1/2, joins them back to the full feature table on
`source_row_id`, and writes `data/training_set.csv`.

Safe to run repeatedly as more batches come back. Later batches win on
conflicts (someone re-reviewing a row is a correction, not a duplicate).

Usage:
    python -m thermotech_ml.make_dataset
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .features import CLASS_NAMES, check_data
from .paths import LABEL_DIR, ML_ROOT as ROOT, TRAINING_CSV as OUT_PATH, UNLABELED_CSV as FEATURE_SOURCE

VALID = {0, 1, 2}


def collect_labels() -> pd.DataFrame:
    files = sorted(LABEL_DIR.glob("*_labeled.csv"))
    if not files:
        raise SystemExit(
            f"No labeled files found in {LABEL_DIR}.\n"
            "Expected something like data/labeling/batch_01_labeled.csv with the "
            "`label` column filled in with 0, 1 or 2."
        )

    frames = []
    for f in files:
        d = pd.read_csv(f)
        if "label" not in d.columns or "source_row_id" not in d.columns:
            print(f"  skipping {f.name}: missing `label` or `source_row_id`")
            continue
        d["label"] = pd.to_numeric(d["label"], errors="coerce")
        good = d[d["label"].isin(VALID)][["source_row_id", "label"]]
        bad = d["label"].notna().sum() - len(good)
        print(f"  {f.name}: {len(good)} usable labels" + (f" ({bad} invalid, ignored)" if bad else ""))
        if "suggested_label" in d.columns:
            overrides = (
                d[d["label"].isin(VALID)]["label"].values
                != d[d["label"].isin(VALID)]["suggested_label"].values
            ).sum()
            print(f"      {overrides} of them disagree with the rule suggestion")
        frames.append(good)

    labels = pd.concat(frames, ignore_index=True)
    return labels.drop_duplicates(subset="source_row_id", keep="last")


def main() -> None:
    print(f"Reading labels from {LABEL_DIR}/")
    labels = collect_labels()

    feats = pd.read_csv(FEATURE_SOURCE)
    merged = feats.merge(labels, on="source_row_id", how="inner")
    merged["label"] = merged["label"].astype(int)

    if merged.empty:
        raise SystemExit("No labeled rows matched the feature table on source_row_id.")

    merged.to_csv(OUT_PATH, index=False)
    print(f"\nWrote {OUT_PATH.relative_to(ROOT)} — {len(merged)} labeled rows")
    for line in check_data(merged):
        print("  " + line)

    counts = merged["label"].value_counts()
    smallest = counts.min()
    if len(counts) < 3:
        missing = [CLASS_NAMES[c] for c in CLASS_NAMES if c not in counts.index]
        print(f"\n  BLOCKER: no examples of {', '.join(missing)}. Label some before training.")
    elif smallest < 20:
        print(f"\n  WARNING: smallest class has only {smallest} rows. "
              "Aim for at least 30-40 each before trusting the metrics.")


if __name__ == "__main__":
    main()
