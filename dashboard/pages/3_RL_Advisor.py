"""
pages/3_RL_Advisor.py
------------------------
Shows the trained Q-learning ventilation advisor's recommendation for a
chosen state, along with the Q-values for every action (full
transparency into why it recommended what it did).
"""

import streamlit as st
import pandas as pd
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import resolve_path  # noqa: E402

st.set_page_config(page_title="RL Advisor", layout="wide")
st.title("🤖 RL Ventilation Advisor")
st.caption("A tabular Q-learning agent trained on the Digital Twin's simulated dynamics, "
           "balancing risk reduction against a simple energy/disruption cost.")

Q_TABLE_PATH = resolve_path("reports", "rl_q_table.joblib")

if not os.path.exists(Q_TABLE_PATH):
    st.error("RL advisor not trained yet. Run `python src/rl_advisor.py` first.")
    st.stop()

from rl_advisor import recommend_action, ACTION_COST  # noqa: E402

col1, col2 = st.columns(2)
with col1:
    co2_ppm = st.slider("Current CO₂ (ppm)", 420, 3200, 2600, step=50)
with col2:
    occupancy = st.slider("Current occupancy", 0, 60, 45)

result = recommend_action(co2_ppm, occupancy)

action_labels = {
    "no_action": "😐 No action",
    "open_windows": "🌬️ Open windows",
    "reduce_occupancy": "🚶 Reduce occupancy",
}

st.markdown(f"## Recommended action: **{action_labels[result['recommended_action']]}**")

q_df = pd.DataFrame(
    [{"Action": action_labels[a], "Q-value (higher = better)": v, "Action cost": ACTION_COST[a]}
     for a, v in result["q_values"].items()]
).sort_values("Q-value (higher = better)", ascending=False)
st.dataframe(q_df, width="stretch")

st.caption(
    "Q-values represent the agent's learned estimate of long-term outcome quality for each "
    "action in this state (higher/less negative = better). Note: this is a simplified "
    "single-step (bandit-style) Q-learning setup, trained via the Digital Twin simulator -- "
    "a good demonstration of the RL concept, not a fully validated multi-step control policy."
)

st.markdown("---")
st.markdown("### How the recommendation changes across the full CO₂/occupancy range")
import numpy as np
co2_range = np.linspace(420, 3200, 15)
occ_range = np.linspace(0, 60, 13)
heatmap_data = []
for occ in occ_range:
    row = []
    for co2 in co2_range:
        rec = recommend_action(co2, occ)["recommended_action"]
        row.append({"no_action": 0, "open_windows": 1, "reduce_occupancy": 2}[rec])
    heatmap_data.append(row)

heatmap_df = pd.DataFrame(
    heatmap_data,
    index=[f"{int(o)}" for o in occ_range],
    columns=[f"{int(c)}" for c in co2_range],
)
st.dataframe(
    heatmap_df.style.background_gradient(cmap="RdYlGn_r", axis=None),
    width="stretch",
)
st.caption("Rows = occupancy, columns = CO₂ (ppm). 0=No action (green), 1=Open windows, "
           "2=Reduce occupancy (red). Shows the learned policy's overall shape.")
