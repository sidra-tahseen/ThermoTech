from risk_engine import calculate_risk


# ---------------------------------------------------------------------------
# TRAINED-MODEL STYLE TEST
# ---------------------------------------------------------------------------

trained_result = calculate_risk(
    probabilities={
        "PERSISTENT_SOURCE": 0.05,
        "OTHER_ANOMALY": 0.08,
        "NEW_ABNORMAL_EVENT": 0.87
    },
    class_id=2,
    classification="NEW_ABNORMAL_EVENT",
    confidence=0.87,
    persistence_days=3,
    frp_zscore=3.5,
    residential_distance=800
)

print("TRAINED MODEL STYLE TEST")
print("------------------------")
print("Risk Score:", trained_result["risk_score"])
print("Severity:", trained_result["severity"])
print("Risk Factors:", trained_result["risk_factors"])
print()


# ---------------------------------------------------------------------------
# FALLBACK RULE-ENGINE TEST
# ---------------------------------------------------------------------------

fallback_result = calculate_risk(
    probabilities=None,
    class_id=1,
    classification="OTHER_ANOMALY",
    confidence=0.45,
    persistence_days=2,
    frp_zscore=1.5,
    residential_distance=None
)

print("FALLBACK RULE-ENGINE TEST")
print("--------------------------")
print("Risk Score:", fallback_result["risk_score"])
print("Severity:", fallback_result["severity"])
print("Risk Factors:", fallback_result["risk_factors"])
print()


# ---------------------------------------------------------------------------
# LOW-RISK TEST
# ---------------------------------------------------------------------------

low_result = calculate_risk(
    probabilities={
        "PERSISTENT_SOURCE": 0.90,
        "OTHER_ANOMALY": 0.08,
        "NEW_ABNORMAL_EVENT": 0.02
    },
    class_id=0,
    classification="PERSISTENT_SOURCE",
    confidence=0.90,
    persistence_days=1,
    frp_zscore=0.2,
    residential_distance=5000
)

print("LOW-RISK TEST")
print("-------------")
print("Risk Score:", low_result["risk_score"])
print("Severity:", low_result["severity"])
print("Risk Factors:", low_result["risk_factors"])
print()


# ---------------------------------------------------------------------------
# INVALID INPUT TEST
# ---------------------------------------------------------------------------

print("INVALID INPUT TEST")
print("-------------------")

try:
    calculate_risk(
        class_id=2,
        persistence_days=-1,
        frp_zscore=2,
        residential_distance=1000
    )

    print("Invalid input accepted")

except ValueError as e:
    print("Error:", e)