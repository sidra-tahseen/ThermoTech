# Labeling guide — 180 rows, roughly 45 minutes

**File to open:** `backend/ml/data/labeling/batch_01_to_label.csv`
**File to save as:** `backend/ml/data/labeling/batch_01_labeled.csv`
**Your only job:** put `0`, `1` or `2` in the empty `label` column.

Open it in Excel or Google Sheets. Every row already has a **suggested** class
and a one-line reason for that suggestion. Most of the time you will agree and
just copy the suggestion across. The rows where you *disagree* are the
valuable ones.

---

## The three classes

| Label | Class | What it means | Typical signature in the row |
|---|---|---|---|
| `0` | `PERSISTENT_SOURCE` | This location burns routinely — a gas flare, a kiln, a steel plant. Nothing new is happening. | `historical_count` high (5+), `persistence_days` 3+, current `frp` in line with `historical_frp_mean` |
| `2` | `NEW_ABNORMAL_EVENT` | Something is happening here that has not happened before, or a known source has jumped well above its normal level. This is the class that should trigger an alert. | `has_baseline` false with decent `frp`, **or** `frp_zscore` ≥ 2, **or** `frp` far above `historical_frp_max` |
| `1` | `OTHER_ANOMALY` | Real detection, but not an industrial story — crop burning, a wildfire, a weak or likely-false detection. | low `frp` (under ~2), thin or no history, `confidence` = 1 (low) |

`confidence` is encoded `0 = nominal`, `1 = low`, `2 = high`.

---

## How to decide, in order

1. **Does this location have a real history?** Look at `historical_count` and
   `persistence_days`. If it has burned many times over many days, it is a
   candidate for `0`.
2. **Is it burning harder than it normally does?** Compare `frp` against
   `historical_frp_mean` and `historical_frp_max`, and check `frp_zscore`.
   A known location behaving abnormally is `2`, not `0` — that is the
   escalation case from our PPT.
3. **No history at all?** Then it is `2` if the FRP is meaningful, `1` if it is
   a weak one-off.
4. **Still unsure?** Leave `label` blank. A blank row is simply skipped.
   A guessed row poisons the model. Blank is always better than a coin flip.

`near_industrial`, `industrial_distance` and friends are only filled in for
about 1 row in 20 — that is a known gap in the current data, not something you
did wrong. Ignore them when they are empty.

---

## Two things that matter more than speed

**Do not just copy every suggestion.** The suggestions come from a rule engine.
If you agree with all 180, the model learns nothing except those rules, and the
accuracy we report is a measure of the rules agreeing with themselves. Expect
to override somewhere between 10% and 30% of rows. `make_dataset.py` prints
your override count, so we will know.

**Two people beat one.** If two of you label the same 60 rows independently and
compare, the rows you disagree on tell us exactly where the class boundaries
are fuzzy — and that is genuinely worth a line in the final presentation.

---

## When you're done

Save as `batch_01_labeled.csv` in the same folder, commit, and tell the ML
member. If you have time for more, the next 180 rows are waiting in
`review_queue_full.csv` — save that batch as `batch_02_labeled.csv` and it gets
picked up automatically.

Minimum to train at all: 60 labeled rows with at least 10 in each class.
Comfortable: 150+ with 40+ each.
