"""
test_v3_features.py
----------------------
Tests for the V3 additions: database layer, Digital Twin simulator,
RL advisor, and anomaly detection. Model/data-dependent tests skip
gracefully if the relevant training step hasn't been run yet.
"""

import os
import sys
from datetime import datetime, timedelta
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import resolve_path

# ---------------- Database layer ----------------

def test_db_alert_roundtrip():
    from db import log_alert, get_recent_alert
    ts = datetime.now()
    log_alert("Room_TestX", "High", ts, "Test root cause")
    recent = get_recent_alert("Room_TestX")
    assert recent is not None
    assert recent.room_id == "Room_TestX"
    assert recent.risk_category == "High"


def test_db_model_registry_promotes_better_model():
    from db import register_model, get_model_history
    import uuid
    model_name = f"Test Model XYZ {uuid.uuid4().hex[:8]}"
    register_model(model_name, 0.80, notes="baseline")
    promoted = register_model(model_name, 0.90, notes="improved")
    assert promoted is True
    history = get_model_history(model_name)
    champions = [m for m in history if m.is_champion]
    assert len(champions) == 1
    assert champions[0].accuracy == 0.90


def test_db_model_registry_does_not_promote_worse_model():
    from db import register_model
    import uuid
    model_name = f"Test Model ABC {uuid.uuid4().hex[:8]}"
    register_model(model_name, 0.95, notes="strong baseline")
    promoted = register_model(model_name, 0.70, notes="worse run")
    assert promoted is False


# ---------------- Digital Twin ----------------

def test_digital_twin_empty_room_has_zero_risk():
    from digital_twin import simulate
    df = simulate(co2_ppm=500, occupancy=0, action="no_action", minutes_ahead=30)
    assert (df["risk_score"] == 0).all()


def test_digital_twin_reduce_occupancy_lowers_or_equals_risk():
    from digital_twin import simulate
    baseline = simulate(co2_ppm=1800, occupancy=30, action="no_action", minutes_ahead=60)
    reduced = simulate(co2_ppm=1800, occupancy=30, action="reduce_occupancy", minutes_ahead=60)
    assert reduced["risk_score"].iloc[-1] <= baseline["risk_score"].iloc[-1]


def test_digital_twin_invalid_action_raises():
    from digital_twin import simulate
    with pytest.raises(ValueError):
        simulate(co2_ppm=1000, occupancy=20, action="not_a_real_action")


def test_digital_twin_compare_all_actions_returns_all():
    from digital_twin import compare_all_actions, ACTIONS
    results = compare_all_actions(1800, 30, minutes_ahead=30)
    assert set(results.keys()) == set(ACTIONS)


# ---------------- RL Advisor ----------------

RL_MODEL_PATH = resolve_path("reports", "rl_q_table.joblib")


@pytest.mark.skipif(not os.path.exists(RL_MODEL_PATH), reason="RL advisor not trained yet")
def test_rl_advisor_recommends_valid_action():
    from rl_advisor import recommend_action, ACTIONS
    result = recommend_action(2800, 50)
    assert result["recommended_action"] in ACTIONS
    assert set(result["q_values"].keys()) == set(ACTIONS)


@pytest.mark.skipif(not os.path.exists(RL_MODEL_PATH), reason="RL advisor not trained yet")
def test_rl_advisor_prefers_no_action_when_safe():
    from rl_advisor import recommend_action
    result = recommend_action(450, 2)
    assert result["recommended_action"] == "no_action"


# ---------------- Anomaly Detection ----------------

ANOMALY_MODEL_PATH = resolve_path("reports", "anomaly_model.joblib")


@pytest.mark.skipif(not os.path.exists(ANOMALY_MODEL_PATH), reason="Anomaly detector not trained yet")
def test_anomaly_detector_flags_impossible_co2():
    from anomaly_detection import check_reading_for_anomaly
    flagged = check_reading_for_anomaly("Room_TestAnom", co2_ppm=9999, temperature_c=26,
                                          humidity_pct=55, occupancy=35)
    assert flagged is True


@pytest.mark.skipif(not os.path.exists(ANOMALY_MODEL_PATH), reason="Anomaly detector not trained yet")
def test_anomaly_detector_passes_normal_reading():
    from anomaly_detection import check_reading_for_anomaly
    flagged = check_reading_for_anomaly("Room_TestNormal", co2_ppm=1800, temperature_c=26,
                                          humidity_pct=55, occupancy=35)
    assert flagged is False
