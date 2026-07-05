"""
rl_advisor.py -- Reinforcement Learning Ventilation Advisor (V3)
--------------------------------------------------------------------
Trains a simple tabular Q-learning agent, using the Digital Twin
(digital_twin.py) as its training environment, to learn WHEN to
recommend "open_windows" or "reduce_occupancy" vs "no_action" --
balancing risk reduction against a simple energy/disruption cost
(opening windows costs energy in winter; sending students out disrupts
class). This is the "Reinforcement Learning" + "Multi-Objective Control"
idea from your original brainstorm, implemented in the simplest form
that is still genuinely a trained policy (not just hardcoded rules).

State space: discretized (co2_bin, occupancy_bin)
Action space: no_action, open_windows, reduce_occupancy
Reward: -risk_score_after_5min - action_cost

This is intentionally simple (tabular Q-learning, not deep RL) so it
trains in seconds and is fully inspectable -- you can print the whole
Q-table and explain every decision in a viva.
"""

import sys
import os
import numpy as np
import joblib
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from digital_twin import simulate, ACTIONS
from config_loader import resolve_path
from logging_setup import get_logger

logger = get_logger("rl_advisor")

CO2_BINS = [420, 800, 1500, 2200, 2900, 3300]      # 5 bins
OCC_BINS = [0, 15, 30, 45, 61]                       # 4 bins

ACTION_COST = {
    "no_action": 0.0,
    "open_windows": 0.05,        # small energy cost
    "reduce_occupancy": 0.15,     # bigger disruption cost (students miss class time)
}


def discretize(co2_ppm: float, occupancy: int) -> tuple:
    co2_bin = np.digitize([co2_ppm], CO2_BINS)[0] - 1
    occ_bin = np.digitize([occupancy], OCC_BINS)[0] - 1
    co2_bin = int(np.clip(co2_bin, 0, len(CO2_BINS) - 2))
    occ_bin = int(np.clip(occ_bin, 0, len(OCC_BINS) - 2))
    return (co2_bin, occ_bin)


def train_q_learning(episodes: int = 3000, alpha: float = 0.2, gamma: float = 0.9,
                      epsilon: float = 0.3, seed: int = 42):
    rng = random.Random(seed)
    n_co2_bins = len(CO2_BINS) - 1
    n_occ_bins = len(OCC_BINS) - 1
    q_table = np.zeros((n_co2_bins, n_occ_bins, len(ACTIONS)))

    for ep in range(episodes):
        co2 = rng.uniform(420, 3200)
        occupancy = rng.randint(0, 60)
        state = discretize(co2, occupancy)

        # epsilon-greedy action choice
        if rng.random() < epsilon:
            action_idx = rng.randint(0, len(ACTIONS) - 1)
        else:
            action_idx = int(np.argmax(q_table[state[0], state[1], :]))
        action = ACTIONS[action_idx]

        sim_df = simulate(co2, occupancy, action=action, minutes_ahead=5, step_minutes=5)
        next_row = sim_df.iloc[-1]
        reward = -next_row.risk_score - ACTION_COST[action]

        next_state = discretize(next_row.co2_ppm, next_row.occupancy)

        best_next = np.max(q_table[next_state[0], next_state[1], :])
        td_target = reward + gamma * best_next
        td_error = td_target - q_table[state[0], state[1], action_idx]
        q_table[state[0], state[1], action_idx] += alpha * td_error

    return q_table


def recommend_action(co2_ppm: float, occupancy: int) -> dict:
    """
    Loads the trained Q-table and returns the recommended action for the
    given state, along with the Q-values for all actions (for transparency).
    """
    q_table_path = resolve_path("reports", "rl_q_table.joblib")
    q_table = joblib.load(q_table_path)

    state = discretize(co2_ppm, occupancy)
    q_values = q_table[state[0], state[1], :]
    best_action_idx = int(np.argmax(q_values))

    return {
        "recommended_action": ACTIONS[best_action_idx],
        "q_values": {a: float(q) for a, q in zip(ACTIONS, q_values)},
        "state_bin": state,
    }


if __name__ == "__main__":
    logger.info("Training RL ventilation advisor (Q-learning)...")
    q_table = train_q_learning()
    out_path = resolve_path("reports", "rl_q_table.joblib")
    joblib.dump(q_table, out_path)
    logger.info(f"Saved trained Q-table to {out_path}")

    # Demo: show recommendations for a few scenarios
    for co2, occ in [(600, 10), (1800, 30), (2800, 50), (3100, 58)]:
        rec = recommend_action(co2, occ)
        print(f"CO2={co2}, occupancy={occ} -> recommend: {rec['recommended_action']} "
              f"(Q-values: {rec['q_values']})")
