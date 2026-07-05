"""
Home.py -- Dashboard Home (V3, multi-page)
----------------------------------------------
V3 reorganizes the dashboard into multiple pages (see the sidebar):
  Home             - live risk grid across all rooms (this page)
  Room Detail      - per-room trend, 1-hr forecast, SHAP explanation
  Digital Twin     - interactive what-if ventilation simulator
  RL Advisor       - trained ventilation-action recommendation
  Sensor Health    - anomaly detection status
  Alerts & Models  - alert history + model registry/versioning
  Reports          - generate & download a PDF report per room

RUN WITH: streamlit run dashboard/Home.py
"""

import streamlit as st
import pandas as pd
import joblib
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import load_config, resolve_path  # noqa: E402

st.set_page_config(page_title="IAQ Infection Risk Monitor -- V3", layout="wide", page_icon="🏫")

cfg = load_config()
MODEL_PATH = resolve_path(cfg["paths"]["reports_dir"], "fuzzy_tree_model.joblib")
DATA_PATH = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])

st.title("🏫 Classroom Air Quality & Infection Risk Monitor")
st.caption("V3 -- software-only, database-backed, with forecasting, explainability, "
           "a Digital Twin simulator, an RL ventilation advisor, sensor anomaly detection, "
           "and automated PDF reporting. Use the sidebar to explore each capability.")


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH, parse_dates=["timestamp"])


if not os.path.exists(MODEL_PATH):
    st.error("No trained model found. Run `python src/train_and_compare.py` first.")
    st.stop()

model = load_model()
df = load_data()

st.sidebar.header("Controls")
timestamps = sorted(df["timestamp"].unique())
selected_time = st.sidebar.select_slider(
    "Simulated current time",
    options=timestamps,
    value=timestamps[len(timestamps) // 3],
    format_func=lambda t: pd.Timestamp(t).strftime("%d %b, %H:%M"),
)
st.session_state["selected_time"] = str(selected_time)

st.sidebar.markdown("---")
st.sidebar.markdown("**Risk color key**")
st.sidebar.markdown("🟢 Low &nbsp;&nbsp; 🟡 Medium &nbsp;&nbsp; 🔴 High")

current = df[df["timestamp"] == selected_time].sort_values("room_id")
COLOR = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}

cols = st.columns(3)
for i, (_, row) in enumerate(current.iterrows()):
    input_df = pd.DataFrame([{
        "co2_ppm": row.co2_ppm, "temperature_c": row.temperature_c,
        "humidity_pct": row.humidity_pct, "occupancy": row.occupancy,
    }])
    pred = model.predict(input_df)[0]
    with cols[i % 3]:
        st.metric(
            label=f"{COLOR[pred]} {row.room_id}",
            value=pred,
            delta=f"CO₂: {row.co2_ppm:.0f} ppm | Occupancy: {int(row.occupancy)}",
        )

st.markdown("---")
n_high = (current.apply(lambda r: model.predict(pd.DataFrame([{
    "co2_ppm": r.co2_ppm, "temperature_c": r.temperature_c,
    "humidity_pct": r.humidity_pct, "occupancy": r.occupancy}]))[0], axis=1) == "High").sum()
st.info(f"At this simulated time, **{n_high} of {len(current)} rooms** are at High risk. "
        f"Use **Room Detail** in the sidebar to investigate a specific room, "
        f"**Digital Twin** to test interventions, or **RL Advisor** for a recommended action.")
