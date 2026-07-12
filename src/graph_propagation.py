"""
graph_propagation.py -- Cross-Room Risk Propagation (V5)
------------------------------------------------------------
The most research-novel idea from the original project brainstorm
(Graph Neural Networks for pollutant/risk diffusion across connected
rooms), implemented here as a lightweight, honestly-described graph
propagation model -- NOT a deep multi-layer GNN with learned embeddings
(that would need PyTorch Geometric and a lot more training data than a
9-classroom deployment realistically has). This is a single-layer graph
convolution: each room's predicted risk is nudged by a weighted average
of its neighbors' risk, where neighbors are rooms that share a wall,
corridor, or HVAC duct.

Why this matters: your original project's models predict each room
INDEPENDENTLY. In reality, if Room_3 is overcrowded and poorly
ventilated, some of that risk likely leaks into Room_4 next door
(shared corridor air, shared HVAC return). A per-room-only model can't
see that. This module adds that missing cross-room signal.

Building layout is defined once in ROOM_ADJACENCY below -- replace it
with your actual PIEMR floor plan's real adjacencies for a real
deployment; the sample layout here is a reasonable 9-room, 3x3 grid
guess (adjust to match reality before trusting the output).
"""

import sys
import os
import numpy as np
import networkx as nx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config

RISK_SCORE_MAP = {"Low": 0.1, "Medium": 0.45, "High": 0.8}
SCORE_TO_CATEGORY_BOUNDARIES = [(0.20, "Low"), (0.45, "Medium")]


def _score_to_category(score: float) -> str:
    for boundary, category in SCORE_TO_CATEGORY_BOUNDARIES:
        if score < boundary:
            return category
    return "High"


def build_building_graph(room_ids: list, layout: str = "config") -> nx.Graph:
    """
    Builds a graph of room adjacency.

    layout="config" (default, V6): reads the real adjacency list from
    config.yaml's building_layout.adjacency -- edit that file to match
    your actual floor plan. This replaces V5's hardcoded 3x3 grid guess.

    layout="grid_3x3": falls back to the old placeholder grid guess,
    kept only for quick demos/tests where no config is available.
    """
    G = nx.Graph()
    G.add_nodes_from(room_ids)

    if layout == "config":
        cfg = load_config()
        adjacency_pairs = cfg.get("building_layout", {}).get("adjacency", [])
        room_id_set = set(room_ids)
        edges_added = 0
        for pair in adjacency_pairs:
            if len(pair) != 2:
                continue
            a, b = pair
            if a in room_id_set and b in room_id_set:
                G.add_edge(a, b)
                edges_added += 1
        if edges_added == 0:
            # Config had no usable entries for these rooms -- fall back
            # to the grid guess rather than returning a graph with no
            # edges at all (which would make propagation a no-op).
            return build_building_graph(room_ids, layout="grid_3x3")
        return G

    if layout == "grid_3x3" and len(room_ids) == 9:
        # Placeholder guess: arrange as a 3x3 grid, connect horizontal/
        # vertical neighbors only (not diagonals). Use layout="config"
        # with a real adjacency list instead whenever possible.
        grid = np.array(room_ids).reshape(3, 3)
        for r in range(3):
            for c in range(3):
                if c + 1 < 3:
                    G.add_edge(grid[r, c], grid[r, c + 1])
                if r + 1 < 3:
                    G.add_edge(grid[r, c], grid[r + 1, c])
    else:
        # Last-resort fallback: connect each room to its immediate
        # neighbor in list order (a simple corridor-style layout)
        for i in range(len(room_ids) - 1):
            G.add_edge(room_ids[i], room_ids[i + 1])

    return G


def propagate_risk(room_predictions: dict, graph: nx.Graph = None,
                    influence_weight: float = 0.25) -> dict:
    """
    Single-layer graph convolution: each room's adjusted risk score is a
    weighted blend of its own predicted risk and the average risk of its
    graph neighbors.

    room_predictions: {room_id: risk_category}  (from the per-room Fuzzy Tree model)
    influence_weight: how much neighboring rooms affect this room's
                       adjusted score (0 = no cross-room effect, matching
                       the original per-room-only model; 1 = fully
                       determined by neighbors)

    Returns {room_id: {"own_score": ..., "adjusted_score": ...,
                        "own_category": ..., "adjusted_category": ...,
                        "neighbors": [...]}}
    """
    room_ids = list(room_predictions.keys())
    if graph is None:
        graph = build_building_graph(room_ids)

    own_scores = {r: RISK_SCORE_MAP.get(cat, 0.45) for r, cat in room_predictions.items()}
    adjusted_scores = {}

    for room_id in room_ids:
        neighbors = [str(n) for n in graph.neighbors(room_id)] if room_id in graph else []
        own_score = own_scores[room_id]

        if neighbors:
            neighbor_avg = np.mean([own_scores.get(n, own_score) for n in neighbors])
            adjusted = (1 - influence_weight) * own_score + influence_weight * neighbor_avg
        else:
            adjusted = own_score

        adjusted_scores[room_id] = {
            "own_score": round(own_score, 3),
            "adjusted_score": round(float(adjusted), 3),
            "own_category": room_predictions[room_id],
            "adjusted_category": _score_to_category(adjusted),
            "neighbors": neighbors,
        }

    return adjusted_scores


def find_escalation_risks(propagation_result: dict) -> list:
    """
    Returns rooms where the cross-room-adjusted category is WORSE than
    the room's own independent prediction -- i.e. rooms that look fine
    in isolation but are at risk of being pulled up by a risky neighbor.
    This is the concrete, actionable output of this module.
    """
    order = {"Low": 0, "Medium": 1, "High": 2}
    escalations = []
    for room_id, data in propagation_result.items():
        if order[data["adjusted_category"]] > order[data["own_category"]]:
            escalations.append({
                "room_id": room_id,
                "own_category": data["own_category"],
                "adjusted_category": data["adjusted_category"],
                "risky_neighbors": data["neighbors"],
            })
    return escalations


if __name__ == "__main__":
    demo_predictions = {
        "Room_1": "Low", "Room_2": "Low", "Room_3": "High",
        "Room_4": "Low", "Room_5": "Medium", "Room_6": "Low",
        "Room_7": "Low", "Room_8": "Low", "Room_9": "Low",
    }
    result = propagate_risk(demo_predictions)
    for room, data in result.items():
        print(f"{room}: own={data['own_category']:6s} -> adjusted={data['adjusted_category']:6s} "
              f"(neighbors: {data['neighbors']})")

    print("\nRooms escalated by a risky neighbor:")
    for e in find_escalation_risks(result):
        print(f"  {e['room_id']}: {e['own_category']} -> {e['adjusted_category']} "
              f"(due to neighbors: {e['risky_neighbors']})")
