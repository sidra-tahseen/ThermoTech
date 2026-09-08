"""
Smoke test — run this first, on any machine, before anything else.

Checks that every dependency imports, that the feature contract builds a
clean matrix from the handoff CSV, that the rule fallback answers, and that
XGBoost + SHAP actually run on this box. Writes nothing except a temp dir.

    python -m thermotech_ml.selftest
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def _ok(msg):
    print(f"  [ok]   {msg}")


def _fail(msg):
    print(f"  [FAIL] {msg}")


def main() -> int:
    failures = 0
    print("ThermoTech ML self-test\n")

    print("Dependencies:")
    for mod in ("pandas", "numpy", "sklearn", "xgboost", "shap"):
        try:
            m = __import__(mod)
            _ok(f"{mod} {getattr(m, '__version__', '?')}")
        except ImportError as e:
            _fail(f"{mod} missing — run `pip install -r requirements.txt` ({e})")
            failures += 1
    if failures:
        return 1

    from .features import FEATURE_COLUMNS, build_features, check_data
    from .predict import classify, model_info
    from .rules import apply_rules

    print("\nData:")
    from .paths import UNLABELED_CSV as src
    if not src.exists():
        _fail(f"{src} not found — expected the data-engineering CSVs in data/processed/")
        return 1
    df = pd.read_csv(src)
    _ok(f"loaded {len(df)} hotspots")

    X = build_features(df)
    if list(X.columns) != FEATURE_COLUMNS:
        _fail("feature contract mismatch")
        failures += 1
    else:
        _ok(f"built feature matrix {X.shape} matching the contract")
    if np.isinf(X.to_numpy(dtype=float)).any():
        _fail("infinite values in feature matrix")
        failures += 1

    for line in check_data(df):
        print(f"         {line}")

    print("\nRule engine:")
    v = apply_rules(df.head(50))
    _ok(f"scored 50 rows, classes seen: {sorted(v['label'].unique().tolist())}")

    print("\nPrediction path:")
    info = model_info()
    res = classify(df.head(5))
    _ok(f"classify() returned {len(res)} results using '{info['model']}'")
    if not info["trained"]:
        print("         (no trained model yet — fallback rules in use, this is expected "
              "until labels exist)")

    print("\nXGBoost + SHAP on this machine:")
    try:
        from sklearn.model_selection import StratifiedKFold  # noqa: F401
        from xgboost import XGBClassifier
        import shap

        y = np.resize([0, 1, 2], len(X))
        m = XGBClassifier(n_estimators=20, max_depth=2, num_class=3,
                          objective="multi:softprob", tree_method="hist")
        m.fit(X, y)
        with tempfile.TemporaryDirectory() as td:
            m.save_model(str(Path(td) / "t.json"))
        shap.TreeExplainer(m).shap_values(X.head(5))
        _ok("trained, saved and explained a throwaway model")
    except Exception as e:  # noqa: BLE001
        _fail(f"{type(e).__name__}: {e}")
        failures += 1

    print("\n" + ("All checks passed." if not failures else f"{failures} check(s) failed."))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
