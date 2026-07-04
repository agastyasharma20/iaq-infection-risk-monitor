"""
test_models.py
----------------
Sanity tests for the trained Fuzzy Decision Tree model and the
explainability layer. These require the models to already be trained
(run src/train_and_compare.py first) -- tests skip gracefully if not.
"""

import os
import sys
import pandas as pd
import joblib
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import resolve_path, load_config

MODEL_PATH = resolve_path("reports", "fuzzy_tree_model.joblib")


@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Model not trained yet")
def test_model_predicts_valid_category():
    model = joblib.load(MODEL_PATH)
    cfg = load_config()
    input_df = pd.DataFrame([{
        "co2_ppm": 2500, "temperature_c": 26, "humidity_pct": 55, "occupancy": 45
    }])[cfg["features"]]
    pred = model.predict(input_df)[0]
    assert pred in ["Low", "Medium", "High"]


@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Model not trained yet")
def test_low_co2_low_occupancy_gives_low_risk():
    model = joblib.load(MODEL_PATH)
    cfg = load_config()
    input_df = pd.DataFrame([{
        "co2_ppm": 450, "temperature_c": 24, "humidity_pct": 50, "occupancy": 2
    }])[cfg["features"]]
    pred = model.predict(input_df)[0]
    assert pred == "Low"


@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Model not trained yet")
def test_explainability_returns_expected_keys():
    from explainability import explain_reading
    result = explain_reading(co2_ppm=2800, temperature_c=27, humidity_pct=60, occupancy=50)
    assert "prediction" in result
    assert "contributions" in result
    assert "root_cause" in result
    assert set(result["contributions"].keys()) == {"co2_ppm", "temperature_c", "humidity_pct", "occupancy"}
