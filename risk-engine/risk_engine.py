"""
ThermoTech Risk Engine

This module is intentionally separate from the ML/SHAP module.

Input contract:
    - probabilities
    - class_id
    - classification
    - confidence
    - persistence_days
    - frp_zscore
    - residential_distance

The ML teammate's `classify()` remains the single source for
classification and SHAP explanations. This module only converts the
classification/context values into a risk score and severity.

Prototype weights/reference values are project design choices and should
only be tuned later after the team reviews real labelled data.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Prototype reference values
# ---------------------------------------------------------------------------

PERSISTENCE_MAX_DAYS = 7.0
ANOMALY_MAX_ZSCORE = 4.0
RESIDENTIAL_MAX_DISTANCE = 5000.0


# ---------------------------------------------------------------------------
# Risk weights
# ---------------------------------------------------------------------------
# These are prototype choices, not official emergency thresholds.

CLASSIFICATION_WEIGHT = 0.50
ANOMALY_WEIGHT = 0.25
PERSISTENCE_WEIGHT = 0.15
RESIDENTIAL_WEIGHT = 0.10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Keep a score inside the 0-100 range."""
    return max(minimum, min(float(value), maximum))


def _safe_float(value, default=None):
    """Convert a value to float while safely handling missing values."""
    if value is None:
        return default

    try:
        value = float(value)
    except (TypeError, ValueError):
        return default

    return value


# ---------------------------------------------------------------------------
# Individual scores
# ---------------------------------------------------------------------------

def calculate_classification_score(
    probabilities=None,
    class_id=None,
    confidence=None
):
    """
    Convert the ML classification into a 0-100 risk score.

    When probabilities are available (trained XGBoost):
        NEW_ABNORMAL_EVENT contributes the most risk,
        OTHER_ANOMALY contributes moderate risk,
        PERSISTENT_SOURCE contributes low risk.

    When probabilities are unavailable (rules-v1 fallback):
        class_id and confidence are used instead.
    """

    if isinstance(probabilities, dict):
        new_event = _safe_float(
            probabilities.get("NEW_ABNORMAL_EVENT"), 0.0
        )
        other_anomaly = _safe_float(
            probabilities.get("OTHER_ANOMALY"), 0.0
        )

        score = (
            new_event * 100.0
            + other_anomaly * 60.0
        )

        return clamp(score)

    # Fallback mode: probabilities are null.
    confidence = _safe_float(confidence, 0.5)
    confidence = clamp(confidence, 0.0, 1.0) / 100.0

    # classify() uses:
    # 0 = PERSISTENT_SOURCE
    # 1 = OTHER_ANOMALY
    # 2 = NEW_ABNORMAL_EVENT
    if class_id == 2:
        base_score = 100.0
    elif class_id == 1:
        base_score = 60.0
    elif class_id == 0:
        base_score = 25.0
    else:
        base_score = 50.0

    # Use the fallback confidence as a modest adjustment rather than
    # treating it as physical danger.
    return clamp(base_score * (0.75 + 0.25 * confidence))


def calculate_anomaly_score(frp_zscore):
    """Higher FRP anomaly relative to historical baseline = higher risk."""
    zscore = _safe_float(frp_zscore, 0.0)

    if zscore <= 0:
        return 0.0

    return clamp((zscore / ANOMALY_MAX_ZSCORE) * 100.0)


def calculate_persistence_score(persistence_days):
    """More historical active days = higher persistence contribution."""
    days = _safe_float(persistence_days, 0.0)

    if days <= 0:
        return 0.0

    return clamp((days / PERSISTENCE_MAX_DAYS) * 100.0)


def calculate_residential_score(residential_distance):
    """
    Closer residential context = higher potential exposure contribution.

    If residential distance is unavailable, return 0 rather than inventing
    a distance. The API contract allows this value to be null.
    """
    distance = _safe_float(residential_distance)

    if distance is None:
        return 0.0

    if distance <= 0:
        return 100.0

    if distance >= RESIDENTIAL_MAX_DISTANCE:
        return 0.0

    return clamp(
        (
            (RESIDENTIAL_MAX_DISTANCE - distance)
            / RESIDENTIAL_MAX_DISTANCE
        ) * 100.0
    )


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------

def get_severity(risk_score):
    """
    Prototype severity bands.

    0-25   LOW
    26-50  MEDIUM
    51-75  HIGH
    76-100 CRITICAL
    """
    if risk_score <= 25:
        return "LOW"

    if risk_score <= 50:
        return "MEDIUM"

    if risk_score <= 75:
        return "HIGH"

    return "CRITICAL"


# ---------------------------------------------------------------------------
# Main risk calculation
# ---------------------------------------------------------------------------

def calculate_risk(
    probabilities=None,
    class_id=None,
    classification=None,
    confidence=None,
    persistence_days=0,
    frp_zscore=None,
    residential_distance=None
):
    """
    Calculate the final ThermoTech risk score.

    This function accepts the output/context of `classify()` directly.
    It works both before and after XGBoost training.

    Returns:
        {
            "risk_score": float,
            "severity": str,
            "risk_factors": list[str],
            "classification_score": float,
            "anomaly_score": float,
            "persistence_score": float,
            "residential_score": float
        }
    """

    # ----------------------- Input validation ----------------------------

    persistence_days = _safe_float(persistence_days, 0.0)
    if persistence_days < 0:
        raise ValueError("persistence_days cannot be negative")

    frp_zscore_value = _safe_float(frp_zscore)

    residential_distance_value = _safe_float(residential_distance)
    if (
        residential_distance_value is not None
        and residential_distance_value < 0
    ):
        raise ValueError("residential_distance cannot be negative")

    if class_id is not None and class_id not in [0, 1, 2]:
        raise ValueError("class_id must be 0, 1, or 2")

    # ----------------------- Individual scores ---------------------------

    classification_score = calculate_classification_score(
        probabilities=probabilities,
        class_id=class_id,
        confidence=confidence
    )

    anomaly_score = calculate_anomaly_score(
        frp_zscore_value
    )

    persistence_score = calculate_persistence_score(
        persistence_days
    )

    residential_score = calculate_residential_score(
        residential_distance_value
    )

    # ----------------------- Overall risk ---------------------------------

    risk_score = (
        classification_score * CLASSIFICATION_WEIGHT
        + anomaly_score * ANOMALY_WEIGHT
        + persistence_score * PERSISTENCE_WEIGHT
        + residential_score * RESIDENTIAL_WEIGHT
    )

    risk_score = round(clamp(risk_score), 2)

    severity = get_severity(risk_score)

    # ----------------------- Explain risk ---------------------------------

    risk_factors = []

    if classification_score >= 75:
        risk_factors.append(
            "High likelihood of a new abnormal thermal event"
        )
    elif classification_score >= 45:
        risk_factors.append(
            "Anomalous thermal classification"
        )

    if anomaly_score >= 75:
        risk_factors.append(
            "Strong FRP anomaly relative to historical activity"
        )
    elif anomaly_score >= 50:
        risk_factors.append(
            "Elevated FRP anomaly relative to historical activity"
        )

    if persistence_score >= 75:
        risk_factors.append(
            "Persistent thermal activity"
        )
    elif persistence_score >= 50:
        risk_factors.append(
            "Repeated thermal activity"
        )

    if residential_score >= 75:
        risk_factors.append(
            "Very close to residential areas"
        )
    elif residential_score >= 50:
        risk_factors.append(
            "Close to residential areas"
        )

    if not risk_factors:
        risk_factors.append(
            "No strong risk indicators from the available inputs"
        )

    return {
        "risk_score": risk_score,
        "severity": severity,
        "risk_factors": risk_factors,
        "classification_score": round(classification_score, 2),
        "anomaly_score": round(anomaly_score, 2),
        "persistence_score": round(persistence_score, 2),
        "residential_score": round(residential_score, 2),
    }