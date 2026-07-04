"""
explainability.py
-------------------
V2 addition: uses SHAP (SHapley Additive exPlanations) to explain WHY the
Fuzzy Decision Tree predicted a given risk level for a specific reading --
e.g. "occupancy contributed +0.31 to this room's risk score, CO2
contributed +0.18". This is the "Explainable AI" requirement from your
original brainstorm, applied directly to your working model rather than
being a separate demo.

Also includes a simple, human-readable root-cause classifier built on
top of the SHAP contributions: it labels the DOMINANT cause of risk as
"Overcrowding", "Poor Ventilation Baseline", "Combined", or "Normal".
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
import shap

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config, resolve_path
from logging_setup import get_logger

logger = get_logger("explainability")


def load_tree_model():
    cfg = load_config()
    model_path = resolve_path(cfg["paths"]["reports_dir"], "fuzzy_tree_model.joblib")
    return joblib.load(model_path), cfg


def explain_reading(co2_ppm: float, temperature_c: float, humidity_pct: float, occupancy: int) -> dict:
    """
    Returns a dict with the predicted category, per-feature SHAP
    contributions, and a plain-language root-cause label.
    """
    model, cfg = load_tree_model()
    features = cfg["features"]

    input_df = pd.DataFrame([{
        "co2_ppm": co2_ppm,
        "temperature_c": temperature_c,
        "humidity_pct": humidity_pct,
        "occupancy": occupancy,
    }])[features]

    prediction = model.predict(input_df)[0]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(input_df)

    # For multi-class trees, shap_values is a list (one array per class).
    # We explain the contribution toward the PREDICTED class specifically.
    class_index = list(model.classes_).index(prediction)
    if isinstance(shap_values, list):
        contributions = shap_values[class_index][0]
    else:
        contributions = shap_values[0, :, class_index]

    contrib_dict = {feat: float(val) for feat, val in zip(features, contributions)}

    root_cause = diagnose_root_cause(contrib_dict, occupancy, co2_ppm)

    return {
        "prediction": prediction,
        "contributions": contrib_dict,
        "root_cause": root_cause,
    }


def diagnose_root_cause(contrib_dict: dict, occupancy: int, co2_ppm: float) -> str:
    """
    Simple, explainable heuristic for root-cause labeling, using the
    SHAP contributions as evidence rather than raw thresholds alone.
    """
    occ_contrib = contrib_dict.get("occupancy", 0)
    co2_contrib = contrib_dict.get("co2_ppm", 0)

    if occ_contrib <= 0.01 and co2_contrib <= 0.01:
        return "Normal — no significant risk driver"

    if occ_contrib > co2_contrib * 1.5:
        return "Overcrowding — occupancy is the dominant risk driver"
    elif co2_contrib > occ_contrib * 1.5:
        return "Poor Ventilation Baseline — CO2 elevated independent of current headcount"
    else:
        return "Combined — both occupancy and poor ventilation are contributing"


if __name__ == "__main__":
    result = explain_reading(co2_ppm=2800, temperature_c=27, humidity_pct=60, occupancy=50)
    print("Prediction:", result["prediction"])
    print("Contributions:", result["contributions"])
    print("Root cause:", result["root_cause"])
