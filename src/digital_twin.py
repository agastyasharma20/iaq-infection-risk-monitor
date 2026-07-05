"""
digital_twin.py -- Live "What-If" Simulator (V3)
----------------------------------------------------
Given a room's CURRENT state (CO2, occupancy), simulates how its risk
trajectory would evolve over the next N minutes under different
interventions -- WITHOUT waiting for real time to pass. This is the
"Digital Twin" concept from your original brainstorm, made concrete and
directly usable: a facilities officer (or you, in a demo) can ask
"what if I open the windows now?" and see the projected outcome
immediately.

Physics reused from data/generate_sample_data.py's CO2 mass-balance
approach, but exposed here as an interactive, parameterized function
rather than a one-shot data generator.

Actions supported:
  - "no_action"        : ventilation stays at current baseline
  - "open_windows"      : ventilation factor boosted (faster CO2 decay)
  - "reduce_occupancy"  : occupancy is cut (simulates sending some students out)
"""

import sys
import os
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wells_riley import infection_risk_score, risk_category

ACTIONS = ["no_action", "open_windows", "reduce_occupancy"]


def simulate(co2_ppm: float, occupancy: int, action: str = "no_action",
             minutes_ahead: int = 60, step_minutes: int = 5,
             baseline_ventilation_factor: float = 1.0) -> pd.DataFrame:
    """
    Projects CO2 and infection risk forward in time under a chosen action.
    Returns a DataFrame with columns: minute, co2_ppm, occupancy, risk_score, risk_category.
    """
    if action not in ACTIONS:
        raise ValueError(f"Unknown action '{action}'. Must be one of {ACTIONS}")

    ventilation_factor = baseline_ventilation_factor

    if action == "open_windows":
        ventilation_factor *= 3.0   # much faster fresh-air exchange
    elif action == "reduce_occupancy":
        occupancy = int(occupancy * 0.5)  # simulate sending half the class out

    co2 = co2_ppm
    rows = []
    steps = int(minutes_ahead / step_minutes)

    for step in range(steps + 1):
        minute = step * step_minutes
        risk = infection_risk_score(co2, occupancy)
        rows.append({
            "minute": minute,
            "co2_ppm": round(co2, 1),
            "occupancy": occupancy,
            "risk_score": round(risk, 4),
            "risk_category": risk_category(risk),
        })

        # advance simulation by one step (same mass-balance style used in
        # the sample data generator, scaled to `step_minutes`)
        dt_fraction = step_minutes / 15.0  # generator's base unit was 15 min
        if occupancy > 0:
            generation = occupancy * 15.0 * dt_fraction
            removal = (co2 - 450) * 0.08 * ventilation_factor * dt_fraction
            co2 = co2 + generation - removal
        else:
            co2 = co2 - (co2 - 450) * 0.15 * ventilation_factor * dt_fraction
        co2 = float(np.clip(co2, 420, 3200))

    return pd.DataFrame(rows)


def compare_all_actions(co2_ppm: float, occupancy: int, minutes_ahead: int = 60) -> dict:
    """Runs the simulation for every available action, for side-by-side comparison."""
    return {action: simulate(co2_ppm, occupancy, action, minutes_ahead) for action in ACTIONS}


if __name__ == "__main__":
    results = compare_all_actions(co2_ppm=2800, occupancy=50, minutes_ahead=60)
    for action, df in results.items():
        final_row = df.iloc[-1]
        print(f"{action:20s} -> after 60 min: CO2={final_row.co2_ppm:.0f}ppm, "
              f"risk={final_row.risk_category} ({final_row.risk_score:.3f})")
