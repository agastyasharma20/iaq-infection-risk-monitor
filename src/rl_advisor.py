"""
rl_advisor.py -- Reinforcement Learning Ventilation Advisor (V3, upgraded in V5)
--------------------------------------------------------------------------------
Trains a tabular Q-learning agent, using the Digital Twin (digital_twin.py)
as its training environment, to learn WHEN to recommend "open_windows" or
"reduce_occupancy" vs "no_action" -- balancing risk reduction against a
simple energy/disruption cost (opening windows costs energy in winter;
sending students out disrupts class).

V5 CHANGE (fixes a documented V4 limitation): V3/V4 trained this with a
single-step ("bandit-style") setup -- each training episode was just one
action evaluated 5 minutes ahead, with no continuation. That's a real
simplification: it can't learn that "act now to avoid a worse state 30
minutes from now" is sometimes better than the locally-best-looking action.

V5 trains a genuine MULTI-STEP episodic MDP instead: each episode runs
12 sequential 5-minute steps (a full simulated hour), the agent's chosen
action changes the state it faces at the NEXT step (not just a one-off
snapshot), and Q-values are updated via standard bootstrapped TD-learning
across the whole trajectory. This lets the discount factor (gamma) do its
actual job -- valuing an action for what it enables later, not just its
immediate 5-minute effect.

State space: discretized (co2_bin, occupancy_bin)
Action space: no_action, open_windows, reduce_occupancy
Reward per step: -risk_score_after_5min - action_cost

Still intentionally tabular (not deep RL) so it trains in seconds and the
whole Q-table can be printed and explained directly in a viva.
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


def train_q_learning(episodes: int = 2000, steps_per_episode: int = 12,
                      alpha: float = 0.2, gamma: float = 0.9,
                      epsilon: float = 0.3, seed: int = 42):
    """
    V5: genuine multi-step episodic training. Each of `episodes` episodes
    runs `steps_per_episode` sequential 5-minute decisions (12 steps = a
    full simulated hour), with the state carrying forward between steps.
    """
    rng = random.Random(seed)
    n_co2_bins = len(CO2_BINS) - 1
    n_occ_bins = len(OCC_BINS) - 1
    q_table = np.zeros((n_co2_bins, n_occ_bins, len(ACTIONS)))

    for ep in range(episodes):
        co2 = rng.uniform(420, 3200)
        occupancy = rng.randint(0, 60)

        for step in range(steps_per_episode):
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

            # carry the resulting state forward to the NEXT step in this
            # episode -- this is the key difference from the old single-step
            # version, and what makes gamma (the discount factor) meaningful.
            co2, occupancy = float(next_row.co2_ppm), int(next_row.occupancy)
            next_state = discretize(co2, occupancy)

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
