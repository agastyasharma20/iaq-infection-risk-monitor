"""
test_v4_features.py
----------------------
Tests for the V4 additions: NLG advisory generator, the autonomous
orchestrator, and the building health score.
"""

import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import resolve_path

MODEL_PATH = resolve_path("reports", "fuzzy_tree_model.joblib")
RL_MODEL_PATH = resolve_path("reports", "rl_q_table.joblib")
ANOMALY_MODEL_PATH = resolve_path("reports", "anomaly_model.joblib")

ALL_MODELS_READY = all(os.path.exists(p) for p in [MODEL_PATH, RL_MODEL_PATH, ANOMALY_MODEL_PATH])


# ---------------- NLG Advisory ----------------

def test_nlg_low_risk_says_no_action_needed():
    from nlg_advisory import generate_advisory
    msg = generate_advisory("Room_1", "Low", "Normal — no significant risk driver", "no_action")
    assert "Low" in msg
    assert "No action needed" in msg


def test_nlg_high_risk_includes_room_cause_and_action():
    from nlg_advisory import generate_advisory
    msg = generate_advisory(
        "Room_5", "High", "Overcrowding — occupancy is the dominant risk driver",
        "reduce_occupancy", projected_category="Medium",
    )
    assert "Room_5" in msg
    assert "High" in msg
    assert "Medium" in msg


def test_nlg_handles_unknown_root_cause_gracefully():
    from nlg_advisory import generate_advisory
    # Should not crash even if root_cause text doesn't match a known template
    msg = generate_advisory("Room_2", "High", "Some new unexpected cause string", "open_windows")
    assert "Room_2" in msg


# ---------------- Building Health ----------------

def test_building_health_all_low_is_perfect_score():
    from building_health import compute_building_health
    result = compute_building_health({"R1": "Low", "R2": "Low", "R3": "Low"})
    assert result["score"] == 100
    assert result["grade"] == "A"
    assert result["rooms_at_risk"] == 0


def test_building_health_all_high_is_zero_score():
    from building_health import compute_building_health
    result = compute_building_health({"R1": "High", "R2": "High"})
    assert result["score"] == 0
    assert result["grade"] == "F"
    assert result["rooms_at_risk"] == 2


def test_building_health_empty_input_does_not_crash():
    from building_health import compute_building_health
    result = compute_building_health({})
    assert result["total_rooms"] == 0
    assert result["score"] == 100


def test_building_health_mixed_is_between_bounds():
    from building_health import compute_building_health
    result = compute_building_health({"R1": "Low", "R2": "Medium", "R3": "High"})
    assert 0 < result["score"] < 100


# ---------------- Orchestrator (needs all models trained) ----------------

@pytest.mark.skipif(not ALL_MODELS_READY, reason="Not all models trained yet")
def test_orchestrator_returns_expected_keys_for_normal_reading():
    from orchestrator import process_reading
    result = process_reading("Room_OrchTest", co2_ppm=1800, temperature_c=26,
                              humidity_pct=55, occupancy=30)
    for key in ["room_id", "risk_category", "root_cause", "recommended_action", "advisory", "alert_fired"]:
        assert key in result


@pytest.mark.skipif(not ALL_MODELS_READY, reason="Not all models trained yet")
def test_orchestrator_skips_risk_pipeline_on_anomaly():
    from orchestrator import process_reading
    result = process_reading("Room_OrchAnomTest", co2_ppm=99999, temperature_c=26,
                              humidity_pct=55, occupancy=30)
    assert result["sensor_anomaly_detected"] is True
    assert result["risk_category"] is None


@pytest.mark.skipif(not ALL_MODELS_READY, reason="Not all models trained yet")
def test_orchestrator_low_risk_skips_simulation_for_efficiency():
    """
    Uses a REAL logged Low-risk reading from the dataset rather than an
    invented value -- hand-picked round numbers (e.g. exactly 24.0C,
    exactly 50% humidity) can land in a sparse region of the anomaly
    detector's learned distribution and get (correctly, for that
    detector) flagged as unusual, even though the values look "normal"
    to a human. Sampling a genuine historical reading avoids that trap.
    """
    import pandas as pd
    from orchestrator import process_reading

    data_path = resolve_path("data", "labeled_data.csv")
    df = pd.read_csv(data_path)
    low_risk_rows = df[df["risk_category"] == "Low"]
    assert len(low_risk_rows) > 0, "Test dataset has no Low-risk rows to sample from"
    row = low_risk_rows.iloc[0]

    result = process_reading(
        "Room_OrchLowTest", co2_ppm=row.co2_ppm, temperature_c=row.temperature_c,
        humidity_pct=row.humidity_pct, occupancy=row.occupancy,
    )
    assert result["sensor_anomaly_detected"] is False
    assert result["risk_category"] == "Low"
    assert "simulation_summary" not in result  # optimization: only simulate if not already Low
