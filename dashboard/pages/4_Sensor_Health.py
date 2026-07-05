"""
pages/4_Sensor_Health.py
---------------------------
Lets you test whether a given reading would be flagged as a likely
sensor fault, and shows the logged history of previously flagged
anomalies.
"""

import streamlit as st
import sys
import os
from datetime import datetime

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import resolve_path  # noqa: E402

st.set_page_config(page_title="Sensor Health", layout="wide")
st.title("🩺 Sensor Health -- Anomaly Detection")
st.caption("Combines hard physical-bounds checks with an Isolation Forest model to catch "
           "faulty or drifting sensors before they poison downstream predictions.")

ANOMALY_MODEL_PATH = resolve_path("reports", "anomaly_model.joblib")

if not os.path.exists(ANOMALY_MODEL_PATH):
    st.error("Anomaly detector not trained yet. Run `python src/anomaly_detection.py` first.")
    st.stop()

from anomaly_detection import check_reading_for_anomaly  # noqa: E402
from db import get_all_anomalies  # noqa: E402

st.markdown("### Test a reading")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    room_id = st.text_input("Room ID", "Room_Test")
with col2:
    co2_ppm = st.number_input("CO₂ (ppm)", value=2500.0)
with col3:
    temperature_c = st.number_input("Temperature (°C)", value=26.0)
with col4:
    humidity_pct = st.number_input("Humidity (%)", value=55.0)
with col5:
    occupancy = st.number_input("Occupancy", value=40)

if st.button("Check this reading"):
    is_anomaly = check_reading_for_anomaly(
        room_id=room_id, co2_ppm=co2_ppm, temperature_c=temperature_c,
        humidity_pct=humidity_pct, occupancy=occupancy, timestamp=datetime.now(),
    )
    if is_anomaly:
        st.error("🚩 This reading was flagged as a likely sensor anomaly.")
    else:
        st.success("✅ This reading looks normal.")

st.markdown("---")
st.markdown("### Anomaly history")
anomalies = get_all_anomalies()
if anomalies:
    import pandas as pd
    anomaly_df = pd.DataFrame([
        {"Timestamp": a.timestamp, "Room": a.room_id, "Reason": a.reason}
        for a in anomalies
    ])
    st.dataframe(anomaly_df, width="stretch")
else:
    st.info("No anomalies logged yet. Try the checker above with an implausible value "
            "(e.g. CO₂ = 9999) to see one appear here.")
