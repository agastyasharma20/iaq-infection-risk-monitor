"""
pages/2_Digital_Twin.py
--------------------------
Interactive what-if ventilation simulator. Pick a starting CO2 level and
occupancy, choose an intervention, and see the projected risk trajectory
-- side by side against the other possible actions.
"""

import streamlit as st
import pandas as pd
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from digital_twin import simulate, compare_all_actions, ACTIONS  # noqa: E402

st.set_page_config(page_title="Digital Twin", layout="wide")
st.title("🧪 Digital Twin -- What-If Ventilation Simulator")
st.caption("Projects how a room's CO₂ and infection-risk score would evolve under different "
           "interventions, without waiting for real time to pass.")

col1, col2, col3 = st.columns(3)
with col1:
    co2_now = st.slider("Current CO₂ (ppm)", 420, 3200, 2600, step=50)
with col2:
    occupancy_now = st.slider("Current occupancy", 0, 60, 45)
with col3:
    minutes_ahead = st.slider("Minutes to project ahead", 15, 120, 60, step=15)

st.markdown("### Compare all interventions")
results = compare_all_actions(co2_now, occupancy_now, minutes_ahead)

action_labels = {
    "no_action": "😐 No action",
    "open_windows": "🌬️ Open windows",
    "reduce_occupancy": "🚶 Reduce occupancy (send some students out)",
}

chart_df = pd.DataFrame({
    action_labels[action]: df.set_index("minute")["risk_score"]
    for action, df in results.items()
})
st.line_chart(chart_df)
st.caption("Projected infection risk score over time under each intervention")

st.markdown("### Outcome after the projected period")
outcome_cols = st.columns(3)
for i, (action, df) in enumerate(results.items()):
    final = df.iloc[-1]
    with outcome_cols[i]:
        st.metric(
            label=action_labels[action],
            value=final.risk_category,
            delta=f"CO₂: {final.co2_ppm:.0f} ppm, risk score {final.risk_score:.2f}",
        )

st.markdown("---")
st.markdown("### Try a specific action in detail")
chosen_action = st.selectbox("Action", ACTIONS, format_func=lambda a: action_labels[a])
detail_df = simulate(co2_now, occupancy_now, action=chosen_action, minutes_ahead=minutes_ahead)
st.dataframe(detail_df, width="stretch")
