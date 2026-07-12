"""
pages/10_Cross_Room_Risk.py
-------------------------------
V5: shows how risk propagates between adjacent rooms -- the per-room
models predict each classroom independently, but rooms sharing a
corridor/HVAC duct realistically influence each other. This page
surfaces rooms that look safe on their own but are being pulled up by
a risky neighbor.
"""

import streamlit as st
import pandas as pd
import joblib
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import load_config, resolve_path  # noqa: E402
from graph_propagation import build_building_graph, propagate_risk, find_escalation_risks  # noqa: E402

st.set_page_config(page_title="Cross-Room Risk", layout="wide")
st.title("🕸️ Cross-Room Risk Propagation")
st.caption("Each room's risk is normally predicted independently. This page adds a "
           "lightweight graph model -- rooms sharing a wall/corridor/HVAC duct can "
           "pull each other's risk up, and this surfaces that effect. "
           "Room adjacency is read from `config.yaml` (`building_layout.adjacency`) -- "
           "edit that list to match your real floor plan.")

cfg = load_config()
MODEL_PATH = resolve_path(cfg["paths"]["reports_dir"], "fuzzy_tree_model.joblib")
DATA_PATH = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])

if not os.path.exists(MODEL_PATH):
    st.error("Models not trained yet. Run the training steps in the README first.")
    st.stop()

model = joblib.load(MODEL_PATH)
df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

unique_timestamps = sorted(df["timestamp"].unique())
selected_time_str = st.session_state.get("selected_time")
selected_time = pd.Timestamp(selected_time_str) if selected_time_str else unique_timestamps[len(unique_timestamps) // 3]
if selected_time not in set(df["timestamp"]):
    selected_time = unique_timestamps[len(unique_timestamps) // 3]

current = df[df["timestamp"] == selected_time]

influence_weight = st.slider(
    "Neighbor influence weight", 0.0, 0.6, 0.25, step=0.05,
    help="0 = rooms are fully independent (matches the base model). Higher = neighboring "
         "rooms' risk affects this room's adjusted score more strongly.",
)

room_predictions = {}
for _, row in current.iterrows():
    input_df = pd.DataFrame([{
        "co2_ppm": row.co2_ppm, "temperature_c": row.temperature_c,
        "humidity_pct": row.humidity_pct, "occupancy": row.occupancy,
    }])
    room_predictions[row.room_id] = model.predict(input_df)[0]

result = propagate_risk(room_predictions, influence_weight=influence_weight)
escalations = find_escalation_risks(result)

COLOR = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}

st.markdown("### Own prediction vs. neighbor-adjusted prediction")
table_df = pd.DataFrame([
    {
        "Room": room,
        "Own Prediction": f"{COLOR[data['own_category']]} {data['own_category']}",
        "Adjusted (with neighbors)": f"{COLOR[data['adjusted_category']]} {data['adjusted_category']}",
        "Neighbors": ", ".join(data["neighbors"]),
    }
    for room, data in result.items()
])
st.dataframe(table_df, width="stretch")

st.markdown("### ⚠️ Rooms escalated by a risky neighbor")
if escalations:
    for e in escalations:
        st.warning(f"**{e['room_id']}** looks {e['own_category']} on its own, but is at "
                   f"**{e['adjusted_category']}** once its neighbors ({', '.join(e['risky_neighbors'])}) "
                   f"are accounted for.")
else:
    st.success("No rooms are currently being escalated by a neighbor at this influence weight.")
