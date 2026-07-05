"""
pages/8_Building_Health.py
-----------------------------
Single executive-summary score for the whole building, aggregated
across all rooms at the currently selected simulated time.
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
from building_health import compute_building_health  # noqa: E402

st.set_page_config(page_title="Building Health", layout="wide")
st.title("🏢 Building Health Score")
st.caption("One number for the whole building -- what an administrator or a Smart City dashboard "
           "would want to see first, before drilling into any one room.")

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
if selected_time_str:
    selected_time = pd.Timestamp(selected_time_str)
else:
    selected_time = unique_timestamps[len(unique_timestamps) // 3]

current = df[df["timestamp"] == selected_time]
if current.empty:
    current = df[df["timestamp"] == unique_timestamps[len(unique_timestamps) // 3]]

room_predictions = {}
for _, row in current.iterrows():
    input_df = pd.DataFrame([{
        "co2_ppm": row.co2_ppm, "temperature_c": row.temperature_c,
        "humidity_pct": row.humidity_pct, "occupancy": row.occupancy,
    }])
    room_predictions[row.room_id] = model.predict(input_df)[0]

health = compute_building_health(room_predictions)

GRADE_COLOR = {"A": "🟢", "B": "🟢", "C": "🟡", "D": "🟠", "F": "🔴"}

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Building Health Score", f"{health['score']}/100")
with col2:
    st.metric("Grade", f"{GRADE_COLOR[health['grade']]} {health['grade']}")
with col3:
    st.metric("Rooms Needing Attention", f"{health['rooms_at_risk']} / {health['total_rooms']}")

st.markdown("---")
st.markdown("### Per-room breakdown")
COLOR = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
breakdown_df = pd.DataFrame([
    {"Room": room, "Risk": f"{COLOR[cat]} {cat}"}
    for room, cat in health["breakdown"].items()
])
st.dataframe(breakdown_df, width="stretch")

st.caption(
    "Score = 100 minus a weighted penalty for every room not at Low risk "
    "(Medium = 5pt penalty, High = 12pt penalty, normalized to 0-100). "
    "Grade: A ≥90, B ≥75, C ≥60, D ≥40, F <40."
)
