"""
building_health.py -- Building Health Score (V4)
------------------------------------------------------
Aggregates every room's current risk into ONE number and letter grade
for the whole building -- the kind of single metric an administrator, principal,
or Smart City dashboard actually wants to see first, before drilling
into any one room.

Score = 100 - (weighted penalty for rooms not at Low risk)
Grade = A (90-100) / B (75-89) / C (60-74) / D (40-59) / F (<40)
"""

import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RISK_PENALTY = {"Low": 0, "Medium": 5, "High": 12}


def compute_building_health(room_predictions: dict) -> dict:
    """
    room_predictions: {room_id: risk_category}
    Returns a dict with the overall score, grade, and per-room breakdown.
    """
    n_rooms = len(room_predictions)
    if n_rooms == 0:
        return {"score": 100, "grade": "A", "rooms_at_risk": 0, "total_rooms": 0}

    total_penalty = sum(RISK_PENALTY.get(cat, 0) for cat in room_predictions.values())
    max_possible_penalty = n_rooms * RISK_PENALTY["High"]
    score = 100 - (total_penalty / max_possible_penalty * 100 if max_possible_penalty else 0)
    score = round(max(0, min(100, score)), 1)

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    rooms_at_risk = sum(1 for cat in room_predictions.values() if cat != "Low")

    return {
        "score": score,
        "grade": grade,
        "rooms_at_risk": rooms_at_risk,
        "total_rooms": n_rooms,
        "breakdown": room_predictions,
    }


if __name__ == "__main__":
    demo = {
        "Room_1": "Low", "Room_2": "Medium", "Room_3": "High",
        "Room_4": "High", "Room_5": "Low", "Room_6": "Medium",
        "Room_7": "Low", "Room_8": "Low", "Room_9": "High",
    }
    result = compute_building_health(demo)
    print(f"Building Health Score: {result['score']}/100 (Grade {result['grade']})")
    print(f"{result['rooms_at_risk']} of {result['total_rooms']} rooms need attention")
