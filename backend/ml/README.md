# ThermoTech — ML module

Owner: **ML member** (feature engineering + XGBoost classification + explainability).
SIH 2026, PS 26162, team GeoFlare.

This folder is self-contained. Everything downstream talks to it through
**one function**, `thermotech_ml.predict.classify()`.

---

## Read this first: the state of the handoff data

The data-engineering handoff gave us 861 VIIRS hotspots (5–7 Sep 2026) and a
`label` column that is **100% empty**. Three things follow from that, and the
whole design of this folder follows from those three things.

**1. Nothing can be trained until humans label some rows.** There is no way
around it. Section "Labeling" below turns that from a 861-row slog into a
~45-minute job for one person.

**2. The system must not be blocked on the ML member.** So `classify()`
falls back to a transparent rule engine (`rules.py`) that encodes the exact
decision tree from slide 3 of our PPT. It returns the *same JSON shape* as
the trained model and stamps `"model": "rules-v1"`. Backend, dashboard and
demo can be built and tested today; the day the model lands, nothing
downstream changes.

**3. There is a real data trap in the OSM columns.** Only **46 of 861 rows**
(`osm_query_status == "ok"`) were actually queried against OSM. In the other
815 rows `near_industrial` is `0` — which means *"we never checked"*, not
*"there is no industry nearby"*. If we feed those zeros in as real values,
XGBoost learns "near_industrial == 1 ⇒ industrial fire" purely because those
36 rows are the only ones anyone looked at, and our headline metric becomes a
lie. `features.py` therefore converts un-queried OSM context to `NaN` and adds
an explicit `osm_unknown` flag. XGBoost handles `NaN` natively.

> **For the data-engineering member:** the highest-value thing you can do for
> model quality is raise OSM coverage from 5% toward 100%. Nothing else in the
> pipeline comes close. `road_distance` is 100% NaN and is excluded by the
> feature contract — do not fabricate it from another OSM category; if you
> genuinely collect it later, add it to `BASE_FEATURES` in `features.py` and
> we retrain.

---

## Where this sits

This module lives at `backend/ml/`, the slot the repo README reserved for
Phase 5. It reads the handoff CSVs from `data/processed/` at the repo root —
it does **not** keep its own copy, so when the data-engineering member
re-runs their notebooks we pick up the new data automatically. All paths are
resolved in `thermotech_ml/paths.py`; nothing else hardcodes a location.

## Setup

```bash
cd backend
python -m venv venv && venv\Scripts\activate     # Windows
# source venv/bin/activate                       # macOS/Linux
pip install -r requirements.txt

cd ml
python -m thermotech_ml.selftest    # verifies deps, data, and that XGBoost/SHAP run here
```

Dependencies are already in `backend/requirements.txt` — scikit-learn,
xgboost, shap and joblib were listed there under "Phase 5". Nothing new to
add.

Run the `thermotech_ml` commands from inside `backend/ml/`.

---

## The pipeline, in order

### 1. Build the review queue (already done — output is committed)

```bash
python -m thermotech_ml.prelabel
```

Runs the rule engine over all 861 hotspots, attaches a **suggested** class and
a plain-English reason to each, ranks the clearest examples first, and writes:

- `data/labeling/review_queue_full.csv` — all 861 rows
- `data/labeling/batch_01_to_label.csv` — a balanced first batch of 180
  (60 suggested per class)

### 2. Label batch 1 — **this is the team's blocker, not mine**

See `LABELING_GUIDE.md`. One person opens `batch_01_to_label.csv` in Excel or
Google Sheets, reads the `why_suggested` column, and types `0`, `1` or `2` in
the empty `label` column — agreeing or overriding. Saves it as
`data/labeling/batch_01_labeled.csv`.

### 3. Assemble the training set

```bash
python -m thermotech_ml.make_dataset
```

Merges every `data/labeling/*_labeled.csv`, joins back to the full feature
table, writes `data/training_set.csv`, and reports how many labels *disagreed*
with the rule suggestion. That disagreement count matters — see the warning
in the labeling guide.

### 4. Train

```bash
python -m thermotech_ml.train
```

Stratified 5-fold CV (not a single split — with a couple hundred rows one
split is luck), balanced class weights, shallow trees. Prints macro F1 with
its spread, an out-of-fold classification report and a confusion matrix, then
refits on everything and saves:

- `models/thermotech_xgb.json`
- `models/model_meta.json` — metrics, class counts, feature list, timestamp
- `reports/feature_importance.csv`

It **refuses to train** below 60 labeled rows or 10 per class. That guard is
deliberate: a number produced under it is not worth putting on a slide.

### 5. Predict

```bash
python -m thermotech_ml.predict
```

Writes `reports/predictions.csv` and `reports/predictions.json`. SHAP top-3
key factors per hotspot, in plain English, for the "Explainable AI" claim.

---

## Test harness — see the model working

A one-page local rig for checking output on real hotspots. Not the team
dashboard (the frontend member owns that) — a rig for me, and a working
reference for how the backend should call `classify()`.

```bash
cd backend/ml
python -m uvicorn demo.app:app --port 8500 --reload
```

Open <http://127.0.0.1:8500>. Port 8500 so it never collides with the real
backend on 8000. A map of all 861 sample hotspots, coloured by
class and sized by confidence, with a ranked list beside it. Click any
hotspot for its explanation, class probabilities, SHAP key factors and the
raw feature values that produced them.

The badge in the top right says which classifier answered. It reads
"Provisional - rule engine" today and flips to "Trained model xgboost-1"
with the live macro F1 the moment `train.py` has run. Nothing to change.

Three endpoints, all reusable by the backend member:

| Endpoint | Purpose |
|---|---|
| `GET /api/hotspots?limit=861` | classify the sample set |
| `GET /api/model` | model status |
| `POST /api/classify` | POST a JSON list of hotspot dicts |

The same three routes exist on the real backend (`backend/app/main.py`) as
`/hotspots`, `/model` and `/classify` — without the `/api` prefix, because
Vite strips it when proxying.

---

## For the backend and dashboard members

Full schema and examples: **`API_CONTRACT.md`**. The short version:

```python
from thermotech_ml.predict import classify, model_info

results = classify(list_of_hotspot_dicts)   # or a pandas DataFrame, or one dict
```

Returns one dict per hotspot with `classification`, `confidence`,
`probabilities`, `key_factors` and `explanation`. Shape is identical whether
the rule fallback or the trained model answered — check the `model` field if
you want to show a "provisional" badge in the UI.

`classify()` is stateless and the model loads once per process, so it is safe
to call from a FastAPI route.

---

## Files

| Path | What it is |
|---|---|
| `thermotech_ml/features.py` | **Feature contract.** Single source of truth. Training and serving both import it, so they cannot drift. |
| `thermotech_ml/rules.py` | Decision tree from the PPT. Pre-label suggestions + safe fallback. |
| `thermotech_ml/prelabel.py` | Builds the human review queue. |
| `thermotech_ml/make_dataset.py` | Merges labeled batches into a training set. |
| `thermotech_ml/train.py` | XGBoost + cross-validation + metrics. |
| `thermotech_ml/predict.py` | `classify()` — the integration point. |
| `thermotech_ml/explain.py` | SHAP → readable key factors. |
| `thermotech_ml/selftest.py` | Environment smoke test. |
| `demo/app.py`, `demo/index.html` | Local test harness (FastAPI + one HTML page, no build step). |
| `../../data/processed/` | The handoff CSVs — read from there, never copied here. |
| `data/labeling/` | Review queue and labeled batches. |
| `models/`, `reports/` | Generated. Model artefacts and metrics. |

## Known limitations (say these out loud in the demo — they are strengths, not excuses)

- **5% OSM coverage.** Land-use context is unknown for most hotspots. The
  model treats unknown as unknown rather than guessing.
- **Three days of data** (5–7 Sep 2026), all VIIRS, all mainland India.
  Persistence features lean on the historical grid-cell baseline, not on this
  window.
- **Labels are human judgement from satellite features**, not ground-truth
  incident reports. Metrics measure agreement with our own reviewers.
- **`road_distance` unavailable.** Excluded rather than fabricated.
