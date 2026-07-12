"""
test_v6_features.py
----------------------
Tests for V6: configurable room adjacency, per-user API roles, and the
federated learning simulation.
"""

import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import resolve_path

DATA_READY = os.path.exists(resolve_path("data", "labeled_data.csv"))


# ---------------- Configurable room adjacency ----------------

def test_graph_uses_config_adjacency_by_default():
    from graph_propagation import build_building_graph
    rooms = [f"Room_{i}" for i in range(1, 10)]
    g = build_building_graph(rooms)  # default layout="config"
    assert g.number_of_edges() > 0


def test_graph_falls_back_gracefully_for_unknown_rooms():
    from graph_propagation import build_building_graph
    rooms = ["Nonexistent_Room_A", "Nonexistent_Room_B", "Nonexistent_Room_C"]
    g = build_building_graph(rooms)
    assert g.number_of_nodes() == 3


def test_grid_layout_still_available_explicitly():
    from graph_propagation import build_building_graph
    rooms = [f"Room_{i}" for i in range(1, 10)]
    g = build_building_graph(rooms, layout="grid_3x3")
    assert g.number_of_edges() == 12


# ---------------- API role-based access control ----------------

def test_api_lookup_user_resolves_configured_keys():
    from api.main import _lookup_user
    admin = _lookup_user("admin-changeme-key-please-replace")
    assert admin is not None
    assert admin["role"] == "admin"

    viewer = _lookup_user("viewer-changeme-key-please-replace")
    assert viewer is not None
    assert viewer["role"] == "viewer"


def test_api_lookup_user_rejects_bogus_key():
    from api.main import _lookup_user
    assert _lookup_user("not-a-real-key") is None
    assert _lookup_user(None) is None


def test_api_legacy_key_resolves_as_admin():
    from api.main import _lookup_user
    legacy = _lookup_user("changeme-iaq-v3-key")
    assert legacy is not None
    assert legacy["role"] == "admin"


def test_role_rank_ordering():
    from api.main import ROLE_RANK
    assert ROLE_RANK["admin"] > ROLE_RANK["viewer"]


# ---------------- Federated learning simulation ----------------

@pytest.mark.skipif(not DATA_READY, reason="Labeled data not generated yet")
def test_federated_simulation_returns_expected_structure():
    from federated_learning import run_federated_simulation
    result = run_federated_simulation(n_institutions=3)
    assert result["n_institutions"] == 3
    assert len(result["local_accuracies"]) == 3
    assert 0 <= result["federated_accuracy"] <= 1
    assert 0 <= result["single_institution_accuracy"] <= 1


@pytest.mark.skipif(not DATA_READY, reason="Labeled data not generated yet")
def test_federated_predict_matches_test_set_length():
    from federated_learning import _split_into_institutions, _train_local_model, federated_predict
    import pandas as pd
    from config_loader import load_config

    cfg = load_config()
    df = pd.read_csv(resolve_path("data", "labeled_data.csv"))
    institution_dfs = _split_into_institutions(df, n_institutions=2)
    models = [_train_local_model(idf, cfg["features"], random_state=42) for idf in institution_dfs]

    X_test = df[cfg["features"]].head(20)
    preds = federated_predict(models, X_test)
    assert len(preds) == 20
    assert set(preds).issubset({"Low", "Medium", "High"})
