"""
pages/1_Room_Detail.py
------------------------
Per-room CO2/risk trend, 1-hour-ahead forecast, and SHAP-based
explainability with root-cause diagnosis.
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
from wells_riley import risk_category  # noqa: E402

st.set_page_config(page_title="Room Detail", layout="wide")
cfg = load_config()

MODEL_PATH = resolve_path(cfg["paths"]["reports_dir"], "fuzzy_tree_model.joblib")
DATA_PATH = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])
FORECAST_MODEL_PATH = resolve_path(cfg["paths"]["reports_dir"], "forecast_model.joblib")

st.title("🔍 Room Detail, Forecast & Explanation")

if not os.path.exists(MODEL_PATH):
    st.error("No trained model found. Run `python src/train_and_compare.py` first.")
    st.stop()

model = joblib.load(MODEL_PATH)
df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
rooms = sorted(df["room_id"].unique())
COLOR = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}

room_choice = st.selectbox("Select a room to inspect", rooms)
room_df = df[df["room_id"] == room_choice].sort_values("timestamp")

selected_time = pd.Timestamp(st.session_state.get("selected_time", room_df["timestamp"].iloc[len(room_df)//3]))
if selected_time not in set(room_df["timestamp"]):
    selected_time = room_df["timestamp"].iloc[len(room_df) // 3]

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
try:
    from explainability import explain_reading
    current_room_row = room_df[room_df["timestamp"] == selected_time]
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
