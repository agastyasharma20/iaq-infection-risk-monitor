"""
orchestrator.py -- Autonomous Decision Orchestrator (V4)
--------------------------------------------------------------
THIS IS THE CENTERPIECE OF V4.

Every module built across V1-V3 does one thing well in isolation:
classify risk, explain it, forecast it, simulate interventions,
recommend an action, detect faulty sensors. Used separately, they're
still five things a person has to check one at a time.

`process_reading()` is the single function that runs the FULL pipeline
for one sensor reading and returns ONE unified, actionable result:

    sensor reading
        -> is this reading even trustworthy? (anomaly check)
        -> what is the current risk, and why? (classification + SHAP)
        -> if risky, what happens under each possible action? (Digital Twin)
        -> which action is actually best? (RL advisor)
        -> say it in one plain sentence (NLG)
        -> log an alert if needed, with the full reasoning attached

This is the "Autonomous Building Brain" concept from the original
research brainstorm, built as something that actually runs end-to-end
on one function call -- this is the project's core USP: one call in,
a complete, explained, actioned decision out.
"""

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from explainability import explain_reading
from anomaly_detection import check_reading_for_anomaly
from digital_twin import compare_all_actions
from rl_advisor import recommend_action
from nlg_advisory import generate_advisory
from alerts import check_and_alert
from wells_riley import risk_category as categorize
from logging_setup import get_logger

logger = get_logger("orchestrator")


def process_reading(room_id: str, co2_ppm: float, temperature_c: float,
                     humidity_pct: float, occupancy: int,
                     timestamp: datetime = None) -> dict:
    """
    Runs the full autonomous decision pipeline for one sensor reading.
    Returns a single structured dict containing every stage's output,
    so a caller (API, dashboard, monitoring loop) gets everything in
    one call instead of orchestrating five separate ones.
    """
    timestamp = timestamp or datetime.now()

    result = {
        "room_id": room_id,
        "timestamp": timestamp.isoformat(),
        "input": {
            "co2_ppm": co2_ppm, "temperature_c": temperature_c,
            "humidity_pct": humidity_pct, "occupancy": occupancy,
        },
    }

    # ---- Stage 1: is this reading trustworthy? ----
    is_anomaly = check_reading_for_anomaly(
        room_id=room_id, co2_ppm=co2_ppm, temperature_c=temperature_c,
        humidity_pct=humidity_pct, occupancy=occupancy, timestamp=timestamp,
    )
    result["sensor_anomaly_detected"] = is_anomaly

    if is_anomaly:
        # Don't make risk decisions on data we don't trust -- this is a
        # deliberate safety choice, not an oversight.
        result["risk_category"] = None
        result["root_cause"] = None
        result["recommended_action"] = None
        result["advisory"] = (
            f"{room_id}: sensor reading looks anomalous (possible fault) -- "
            f"skipping risk assessment until a valid reading arrives."
        )
        logger.warning(f"[{room_id}] Anomalous reading -- skipping risk pipeline.")
        return result

    # ---- Stage 2: current risk + explanation ----
    explanation = explain_reading(co2_ppm, temperature_c, humidity_pct, occupancy)
    result["risk_category"] = explanation["prediction"]
    result["contributions"] = explanation["contributions"]
    result["root_cause"] = explanation["root_cause"]

    # ---- Stage 3 & 4: simulate options + recommend the best one ----
    # (only worth the extra computation if risk isn't already Low)
    projected_category = None
    recommended = "no_action"

    if explanation["prediction"] != "Low":
        rl_result = recommend_action(co2_ppm, occupancy)
        recommended = rl_result["recommended_action"]
        result["rl_recommendation"] = rl_result

        sim_results = compare_all_actions(co2_ppm, occupancy, minutes_ahead=60)
        result["simulation_summary"] = {
            action: {
                "final_co2_ppm": float(df.iloc[-1].co2_ppm),
                "final_risk_category": df.iloc[-1].risk_category,
            }
            for action, df in sim_results.items()
        }
        projected_category = result["simulation_summary"][recommended]["final_risk_category"]

    result["recommended_action"] = recommended

    # ---- Stage 5: plain-English advisory ----
    result["advisory"] = generate_advisory(
        room_id=room_id, risk_category=explanation["prediction"],
        root_cause=explanation["root_cause"], recommended_action=recommended,
        projected_category=projected_category,
    )

    # ---- Stage 6: alert if needed ----
    fired = check_and_alert(
        room_id=room_id, risk_category=explanation["prediction"],
        timestamp=timestamp, root_cause=explanation["root_cause"],
    )
    result["alert_fired"] = fired

    logger.info(f"[{room_id}] {explanation['prediction']} risk, "
                f"recommend={recommended}, alert_fired={fired}")

    return result


if __name__ == "__main__":
    import json
    # Demo: one clearly risky reading
    result = process_reading(
        room_id="Room_4", co2_ppm=2900, temperature_c=27,
        humidity_pct=60, occupancy=52,
    )
    print(json.dumps(result, indent=2, default=str))
    print("\n--- Advisory ---")
    print(result["advisory"])
