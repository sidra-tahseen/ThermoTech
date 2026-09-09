# ThermoTech

### Satellite Thermal Intelligence & Wildfire Risk Assessment

ThermoTech is an AI-assisted thermal anomaly analysis and risk prioritization platform designed to transform satellite-based thermal hotspot observations into actionable intelligence.

The system processes NASA FIRMS thermal detections, combines them with historical behavior and temporal features, classifies thermal events using an XGBoost model, explains predictions using SHAP, and assigns an independent risk score through a dedicated Risk Engine.

The result is an operational dashboard that helps distinguish persistent thermal sources from potentially abnormal events and prioritize areas requiring attention.

---

## What ThermoTech Does

ThermoTech follows an end-to-end pipeline:

```text
NASA FIRMS Thermal Data
          ↓
Historical & Temporal Analysis
          ↓
Feature Engineering
          ↓
XGBoost Classification
          ↓
SHAP Explainability
          ↓
Risk Engine
          ↓
Interactive Operational Dashboard
