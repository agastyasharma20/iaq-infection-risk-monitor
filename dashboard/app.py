"""
app.py -- Streamlit Dashboard (V2)
------------------------------------
V2 adds, on top of the V1 live risk grid:
  - Root-cause explanation (SHAP-based) for the selected room's current reading
  - Short-horizon risk forecast (~1 hour ahead) for the selected room
  - Alert history log viewer

RUN THIS WITH:
    streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from wells_riley import infection_risk_score, risk_category  # noqa: E402
from config_loader import load_config, resolve_path  # noqa: E402

st.set_page_config(page_title="Classroom Air Quality & Infection Risk Monitor", layout="wide")

cfg = load_config()
MODEL_PATH = resolve_path(cfg["paths"]["reports_dir"], "fuzzy_tree_model.joblib")
DATA_PATH = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])
FORECAST_MODEL_PATH = resolve_path(cfg["paths"]["reports_dir"], "forecast_model.joblib")
ALERTS_PATH = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["alerts_log_file"])

st.title("🏫 Classroom Air Quality & Infection Risk Monitor — V2")
st.caption("Software-only system — reuses existing CO₂ / temperature / humidity / occupancy sensors. "
           "V2 adds forecasting, explainability, root-cause diagnosis, and alerting.")


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH, parse_dates=["timestamp"])


model = load_model()
df = load_data()
rooms = sorted(df["room_id"].unique())

# ---------------- Sidebar controls ----------------
st.sidebar.header("Controls")
timestamps = sorted(df["timestamp"].unique())
selected_time = st.sidebar.select_slider(
    "Simulated current time",
    options=timestamps,
    value=timestamps[len(timestamps) // 3],
    format_func=lambda t: pd.Timestamp(t).strftime("%d %b, %H:%M"),
)
st.sidebar.markdown("---")
st.sidebar.markdown("**Risk color key**")
st.sidebar.markdown("🟢 Low &nbsp;&nbsp; 🟡 Medium &nbsp;&nbsp; 🔴 High")

current = df[df["timestamp"] == selected_time].sort_values("room_id")
COLOR = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}

# ---------------- Live grid ----------------
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

# ---------------- Room detail, forecast & explanation ----------------
st.subheader("Room detail, forecast & explanation")
room_choice = st.selectbox("Select a room to inspect", rooms)
room_df = df[df["room_id"] == room_choice].sort_values("timestamp")

col1, col2 = st.columns(2)
with col1:
    st.line_chart(room_df.set_index("timestamp")[["co2_ppm"]])
    st.caption("CO₂ over time (ppm)")
with col2:
    st.line_chart(room_df.set_index("timestamp")[["risk_score"]])
    st.caption("Predicted infection risk score over time (Wells-Riley based)")

st.markdown("#### 🔮 1-hour-ahead forecast")
if os.path.exists(FORECAST_MODEL_PATH):
    try:
        from forecast_model import forecast_for_room
        room_history_up_to_now = room_df[room_df["timestamp"] <= selected_time]
        forecasted_score = forecast_for_room(room_history_up_to_now)
        if forecasted_score is not None:
            forecasted_category = risk_category(forecasted_score)
            st.info(f"{COLOR[forecasted_category]} Forecasted risk in ~1 hour for **{room_choice}**: "
                    f"**{forecasted_category}** (score: {forecasted_score:.2f})")
        else:
            st.warning("Not enough recent history at this point in time to forecast yet.")
    except Exception as e:
        st.warning(f"Forecast unavailable: {e}")
else:
    st.warning("Forecast model not trained yet. Run `python src/forecast_model.py` first.")

st.markdown("#### 🧠 Why is this room at this risk level? (Explainable AI)")
if os.path.exists(MODEL_PATH):
    try:
        from explainability import explain_reading
        current_room_row = current[current["room_id"] == room_choice]
        if not current_room_row.empty:
            r = current_room_row.iloc[0]
            explanation = explain_reading(r.co2_ppm, r.temperature_c, r.humidity_pct, r.occupancy)
            st.write(f"**Predicted category:** {COLOR[explanation['prediction']]} {explanation['prediction']}")
            st.write(f"**Root cause diagnosis:** {explanation['root_cause']}")
            contrib_df = pd.DataFrame(
                explanation["contributions"].items(), columns=["Feature", "Contribution"]
            ).sort_values("Contribution", key=abs, ascending=False)
            st.bar_chart(contrib_df.set_index("Feature"))
            st.caption("Positive = pushes risk higher for the predicted category. "
                       "Negative = pushes risk lower. (SHAP values)")
    except Exception as e:
        st.warning(f"Explainability unavailable: {e}")

st.markdown("---")

# ---------------- Alert history ----------------
st.subheader("🔔 Alert history")
if os.path.exists(ALERTS_PATH):
    alerts_df = pd.read_csv(ALERTS_PATH)
    st.dataframe(alerts_df.sort_values("timestamp", ascending=False), width="stretch")
else:
    st.info("No alerts logged yet. Alerts fire automatically when a room's predicted risk is High "
            "(see src/alerts.py) — trigger some via the API to see them appear here.")

st.markdown("---")
st.subheader("Why this matters")
st.write(
    "Raw CO₂ numbers are hard to act on. This dashboard converts them into a plain risk level, "
    "explains WHY that risk level was predicted, forecasts where it's heading next, and logs "
    "alerts automatically — turning monitoring into a decision-support system."
)
