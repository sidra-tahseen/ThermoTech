# API contract — ML module

For the **backend member** (FastAPI), the **frontend member** (React/Leaflet)
and the **explainability & risk member** (SHAP + risk engine).

This contract is stable. It does not change when the model is trained — only
the `model` field flips from `rules-v1` to `xgboost-1` and `probabilities` /
`key_factors` become populated. Build against it now.

---

## Python entry point

```python
from thermotech_ml.predict import classify, model_info
```

### `classify(records, explain=True) -> list[dict]`

`records` may be a list of dicts, a pandas DataFrame, or a single dict.
Returns one result dict per input row, in the same order.

Missing input fields are tolerated — they become `NaN` and the model handles
them. You do **not** need to pre-clean, impute or one-hot anything;
`features.py` owns all of that.

### `model_info() -> dict`

For a `/health` or `/model` endpoint:

```json
{"model": "xgboost-1", "trained": true, "trained_at": "2026-09-08T12:00:00+00:00",
 "n_labeled_rows": 180, "macro_f1": 0.81}
```

Before training:

```json
{"model": "rules-v1", "trained": false,
 "note": "No trained model yet — rule engine in use."}
```

---

## Input

Any subset of the columns in `data/processed/thermotech_ml_ready_unlabeled.csv`.
The ones that actually drive the prediction:

| Field | Type | Notes |
|---|---|---|
| `source_row_id` | int | echoed back, use it to join to your DB row |
| `latitude`, `longitude` | float | echoed back for the map pin |
| `acq_datetime` | str | echoed back |
| `frp` | float | fire radiative power |
| `confidence` | int | `0` nominal, `1` low, `2` high |
| `bright_ti4`, `bright_ti5`, `brightness_difference` | float | |
| `scan`, `track` | float | |
| `historical_count`, `historical_frp_mean`, `historical_frp_max` | float | grid-cell baseline |
| `persistence_days`, `persistence_ratio`, `has_baseline` | float / 0-1 | |
| `frp_zscore` | float | may be null when there is no baseline |
| `is_night`, `hour`, `day_of_week` | int | |
| `osm_queried` | 0/1 | **must be honest** — see below |
| `near_industrial`, `near_agriculture`, `near_forest`, `near_residential`, `near_commercial` | 0/1 | |
| `industrial_distance`, `residential_distance` | float, metres | null when not queried |

> **`osm_queried` is load-bearing.** When it is `0`, the module deliberately
> discards the `near_*` flags and distances for that row, because `0` there
> means "we never looked", not "nothing nearby". Never send `osm_queried: 1`
> with placeholder zeros — that is worse than sending nothing.

`road_distance` is ignored. It is 100% NaN in our data and must not be
fabricated.

---

## Output

```json
{
  "source_row_id": 429,
  "latitude": 21.7834,
  "longitude": 72.9931,
  "acq_datetime": "2026-09-06 20:41:00",
  "class_id": 2,
  "classification": "NEW_ABNORMAL_EVENT",
  "confidence": 0.87,
  "probabilities": {
    "PERSISTENT_SOURCE": 0.05,
    "OTHER_ANOMALY": 0.08,
    "NEW_ABNORMAL_EVENT": 0.87
  },
  "key_factors": [
    {"feature": "frp_over_hist_max", "label": "FRP relative to its historical peak",
     "value": 3.42, "contribution": 1.21, "direction": "supports"},
    {"feature": "historical_count", "label": "past detections at this location",
     "value": 10.0, "contribution": 0.64, "direction": "supports"},
    {"feature": "frp_zscore", "label": "FRP anomaly vs its own history",
     "value": 8.41, "contribution": 0.55, "direction": "supports"}
  ],
  "explanation": "Classified as NEW_ABNORMAL_EVENT, driven mainly by FRP relative to its historical peak (3.42), past detections at this location (10), FRP anomaly vs its own history (8.41).",
  "model": "xgboost-1"
}
```

| Field | Type | Notes |
|---|---|---|
| `class_id` | `0` / `1` / `2` | matches the team's labeling scheme |
| `classification` | str | `PERSISTENT_SOURCE`, `OTHER_ANOMALY`, `NEW_ABNORMAL_EVENT` |
| `confidence` | float 0–1 | highest class probability (trained) or rule strength (fallback) |
| `probabilities` | dict or `null` | `null` in fallback mode — guard for it in the UI |
| `key_factors` | list | up to 3, SHAP-ranked. Empty in fallback mode. |
| `explanation` | str | always present, always renderable |
| `model` | `"xgboost-1"` / `"rules-v1"` | show a "provisional" badge on `rules-v1` |

---

## Notes per role

**Backend** — `classify()` is stateless and the model is cached after the
first call, so a module-level import plus a call inside the route is fine. No
warm-up needed. Handle `probabilities: null`. Store `model` alongside each
prediction so we can tell later which classifications were provisional.

**Frontend** — colour pins by `classification`, size or sort by `confidence`,
and put `explanation` in the drill-down card. `key_factors` maps directly to
the "Key Factors" bullet list on slide 2 of our PPT.

**Explainability & risk** — SHAP is already wired in `explain.py`; call
`Explainer.top_factors()` if you want more than 3 factors or per-class
contributions. For the risk score, the useful inputs are `probabilities`,
`persistence_days`, `frp_zscore` and `residential_distance` — risk scoring
lives in your module, not in mine, so we do not end up with two definitions of
severity.
