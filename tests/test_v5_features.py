"""
test_v5_features.py
----------------------
Tests for V5: multi-step RL, graph-based cross-room risk propagation,
building health history logging, and the full monitoring loop as an
end-to-end integration test.
"""

import os
import sys
from datetime import datetime
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import resolve_path

RL_MODEL_PATH = resolve_path("reports", "rl_q_table.joblib")
ALL_MODELS_READY = all(os.path.exists(resolve_path("reports", f)) for f in [
    "fuzzy_tree_model.joblib", "rl_q_table.joblib", "anomaly_model.joblib",
])


# ---------------- Graph Propagation ----------------

def test_graph_propagation_no_effect_when_weight_zero():
    from graph_propagation import propagate_risk
    predictions = {"Room_1": "Low", "Room_2": "High", "Room_3": "Low"}
    result = propagate_risk(predictions, influence_weight=0.0)
    for room, data in result.items():
        assert data["own_category"] == data["adjusted_category"]


def test_graph_propagation_escalation_detected_for_isolated_low_room():
    from graph_propagation import propagate_risk, find_escalation_risks
    predictions = {
        "Room_1": "Low", "Room_2": "Low", "Room_3": "High",
        "Room_4": "High", "Room_5": "Low", "Room_6": "Low",
        "Room_7": "Low", "Room_8": "Low", "Room_9": "Low",
    }
    result = propagate_risk(predictions, influence_weight=0.35)
    escalations = find_escalation_risks(result)
    assert len(escalations) > 0


def test_graph_propagation_json_serializable_neighbor_types():
    from graph_propagation import propagate_risk
    import json
    predictions = {"Room_1": "Low", "Room_2": "Low", "Room_3": "High"}
    result = propagate_risk(predictions)
    json.dumps(result)


def test_graph_build_building_graph_grid_has_expected_edge_count():
    from graph_propagation import build_building_graph
    rooms = [f"Room_{i}" for i in range(1, 10)]
    g = build_building_graph(rooms)
    assert g.number_of_edges() == 12


# ---------------- Building Health History ----------------

def test_building_health_log_roundtrip():
    from db import log_building_health, get_building_health_history
    log_building_health(datetime.now(), score=75.5, grade="B", rooms_at_risk=2, total_rooms=9)
    history = get_building_health_history(limit=1000)
    assert len(history) > 0
    assert any(h.score == 75.5 and h.grade == "B" for h in history)


# ---------------- Multi-step RL sanity ----------------

@pytest.mark.skipif(not os.path.exists(RL_MODEL_PATH), reason="RL advisor not trained yet")
def test_rl_advisor_still_returns_valid_action_after_v5_upgrade():
    from rl_advisor import recommend_action, ACTIONS
    result = recommend_action(2800, 50)
    assert result["recommended_action"] in ACTIONS


# ---------------- End-to-end integration test ----------------

@pytest.mark.skipif(not ALL_MODELS_READY, reason="Not all models trained yet")
def test_full_monitoring_cycle_integration():
    """
    Integration test: runs one full monitoring cycle across every room
    in the real labeled dataset via the orchestrator, and checks the
    aggregate output is well-formed end to end.
    """
    import pandas as pd
    from monitor_loop import run_monitoring_cycle

    data_path = resolve_path("data", "labeled_data.csv")
    df = pd.read_csv(data_path, parse_dates=["timestamp"])

    health = run_monitoring_cycle(df)

    assert 0 <= health["score"] <= 100
    assert health["grade"] in ["A", "B", "C", "D", "F"]
    assert health["total_rooms"] == df["room_id"].nunique()
    assert 0 <= health["rooms_at_risk"] <= health["total_rooms"]
