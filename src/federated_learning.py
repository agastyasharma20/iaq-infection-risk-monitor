"""
federated_learning.py -- Federated Learning Simulation (V6)
------------------------------------------------------------------
The last major untouched idea from the original research brainstorm
(Cluster D: cross-institution Federated Learning, and the Sakarya
University collaboration referenced in the original whiteboard).

WHAT FEDERATED LEARNING MEANS HERE: instead of one model trained on
one building's data, imagine several institutions (your college, plus
others) each want a better, more generalizable risk model -- but none
of them wants to share raw sensor data (privacy, competitive, or
policy reasons). Federated learning lets them collaboratively train
ONE shared model by exchanging only model updates, never raw data.

WHAT WAS ACTUALLY BUILT (described honestly): a real, working
implementation of the core federated-learning idea -- simulated across
multiple synthetic "institutions" (each gets its own slice of the
sensor data, standing in for a different college/campus). Each
institution trains a local model on ONLY its own data, and only the
trained models (not the underlying data) are combined into a global
ensemble. This is a genuine, runnable demonstration of the algorithm
and its core privacy property -- not a claim that this has been
validated with real partner institutions, which would require actual
inter-institutional data-sharing agreements this project doesn't have.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config, resolve_path
from logging_setup import get_logger

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

logger = get_logger("federated_learning")


def _split_into_institutions(df: pd.DataFrame, n_institutions: int, seed: int = 42) -> list:
    """
    Simulates multiple institutions by splitting the dataset by room
    (a room's full history stays with one 'institution', which is more
    realistic than a random row-level split -- a real institution owns
    whole rooms/buildings, not scattered individual readings).
    """
    rooms = sorted(df["room_id"].unique())
    rng = np.random.RandomState(seed)
    rng.shuffle(rooms)
    room_groups = np.array_split(rooms, n_institutions)
    return [df[df["room_id"].isin(group)].copy() for group in room_groups]


def _train_local_model(df: pd.DataFrame, features: list, random_state: int):
    X = df[features]
    y = df["risk_category"]
    model = DecisionTreeClassifier(max_depth=6, min_samples_leaf=10, random_state=random_state)
    model.fit(X, y)
    return model


def federated_predict(models: list, X: pd.DataFrame) -> np.ndarray:
    """
    Majority vote across all institutions' local models -- this IS the
    'global' federated prediction. (Real FedAvg averages neural network
    weights directly; decision trees don't have an aligned parameter
    structure to average, so an ensemble vote is the honest equivalent
    here -- each institution's model participates in the final answer
    without any institution's raw data ever leaving it.)
    """
    all_preds = np.array([m.predict(X) for m in models])
    final = []
    for col in range(all_preds.shape[1]):
        values, counts = np.unique(all_preds[:, col], return_counts=True)
        final.append(values[np.argmax(counts)])
    return np.array(final)


def run_federated_simulation(n_institutions: int = 3) -> dict:
    """
    Runs the full simulation: split data into N synthetic institutions,
    train a local model per institution (on ONLY that institution's
    data), combine them into a federated ensemble, and compare its
    accuracy against a single institution training alone -- the classic
    federated learning pitch: "the federation should generalize better
    than any one participant training in isolation."
    """
    cfg = load_config()
    features = cfg["features"]
    data_path = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])
    df = pd.read_csv(data_path)

    institution_dfs = _split_into_institutions(df, n_institutions)

    # Held-out global test set: sample evenly from every institution so
    # it's a fair test of generalization, not just one institution's
    # own distribution.
    test_frames = []
    train_frames = []
    for inst_df in institution_dfs:
        train_part, test_part = train_test_split(
            inst_df, test_size=0.25, random_state=cfg["model"]["random_state"]
        )
        train_frames.append(train_part)
        test_frames.append(test_part)

    global_test_df = pd.concat(test_frames, ignore_index=True)
    X_test = global_test_df[features]
    y_test = global_test_df["risk_category"]

    # Train one local model PER institution, using only that institution's data
    local_models = []
    local_accuracies = []
    for i, train_df in enumerate(train_frames):
        model = _train_local_model(train_df, features, random_state=cfg["model"]["random_state"] + i)
        local_models.append(model)
        local_acc = accuracy_score(y_test, model.predict(X_test))
        local_accuracies.append(local_acc)
        logger.info(f"Institution {i+1}/{n_institutions} local model accuracy on global test set: {local_acc*100:.2f}%")

    # Federated (combined) prediction
    federated_preds = federated_predict(local_models, X_test)
    federated_accuracy = accuracy_score(y_test, federated_preds)

    # Baseline: what if only ONE institution's data had been used (no federation)?
    single_institution_accuracy = local_accuracies[0]

    result = {
        "n_institutions": n_institutions,
        "local_accuracies": local_accuracies,
        "single_institution_accuracy": single_institution_accuracy,
        "federated_accuracy": federated_accuracy,
        "improvement_over_single": federated_accuracy - single_institution_accuracy,
    }

    logger.info(f"Single-institution accuracy: {single_institution_accuracy*100:.2f}% | "
                f"Federated accuracy: {federated_accuracy*100:.2f}% | "
                f"Improvement: {result['improvement_over_single']*100:+.2f} points")

    return result


if __name__ == "__main__":
    result = run_federated_simulation(n_institutions=3)
    print("\n=== Federated Learning Simulation Results ===")
    print(f"Institutions simulated: {result['n_institutions']}")
    for i, acc in enumerate(result["local_accuracies"]):
        print(f"  Institution {i+1} local model accuracy: {acc*100:.2f}%")
    print(f"Single institution alone: {result['single_institution_accuracy']*100:.2f}%")
    print(f"Federated (combined): {result['federated_accuracy']*100:.2f}%")
    print(f"Improvement from federating: {result['improvement_over_single']*100:+.2f} points")
