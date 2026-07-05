"""
pages/7_Autonomous_Advisor.py
--------------------------------
The V4 USP, in dashboard form: pick a room's current reading (or use a
live one from the data) and get ONE unified, plain-English decision --
not five separate charts to mentally combine yourself.
"""

import streamlit as st
import pandas as pd
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import load_config, resolve_path  # noqa: E402

st.set_page_config(page_title="Autonomous Advisor", layout="wide")
st.title("🧠 Autonomous Advisor")
st.caption("**This is the core idea of V4:** one call runs the entire pipeline -- sensor "
           "trust check, risk classification, root-cause diagnosis, what-if simulation, "
           "the best action, and a plain-English summary -- instead of checking five "
           "separate tools yourself.")

cfg = load_config()
MODEL_PATH = resolve_path(cfg["paths"]["reports_dir"], "fuzzy_tree_model.joblib")

if not os.path.exists(MODEL_PATH):
    st.error("Models not trained yet. Run the training steps in the README first.")
    st.stop()

from orchestrator import process_reading  # noqa: E402

st.markdown("### Enter a reading (or pick a risky preset to see the full pipeline in action)")

preset = st.radio("Quick presets", ["Custom", "Calm room", "Overcrowded room", "Faulty sensor"],
                   horizontal=True)

defaults = {
    "Custom": (2500.0, 26.0, 55.0, 40),
    "Calm room": (600.0, 24.0, 45.0, 8),
    "Overcrowded room": (2950.0, 27.5, 62.0, 55),
    "Faulty sensor": (9999.0, 26.0, 55.0, 40),
}
d_co2, d_temp, d_hum, d_occ = defaults[preset]

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    room_id = st.text_input("Room ID", "Room_Demo")
with col2:
    co2_ppm = st.number_input("CO₂ (ppm)", value=d_co2)
with col3:
    temperature_c = st.number_input("Temperature (°C)", value=d_temp)
with col4:
    humidity_pct = st.number_input("Humidity (%)", value=d_hum)
with col5:
    occupancy = st.number_input("Occupancy", value=d_occ)

if st.button("🔍 Analyze (run full autonomous pipeline)", type="primary"):
    with st.spinner("Running: anomaly check → risk classification → simulation → recommendation..."):
        result = process_reading(
            room_id=room_id, co2_ppm=co2_ppm, temperature_c=temperature_c,
            humidity_pct=humidity_pct, occupancy=occupancy,
        )

    st.markdown("## 📋 Result")
    st.info(result["advisory"])

    if result["sensor_anomaly_detected"]:
        st.warning("⚠️ This reading was flagged as a likely sensor fault -- "
                   "no risk decision was made on untrustworthy data.")
    else:
        COLOR = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Risk Level", f"{COLOR[result['risk_category']]} {result['risk_category']}")
        with c2:
            st.metric("Root Cause", result["root_cause"].split(" — ")[0] if result["root_cause"] else "N/A")
        with c3:
            st.metric("Recommended Action", result["recommended_action"] or "N/A")

        if "simulation_summary" in result:
            st.markdown("### What each action would achieve")
            sim_df = pd.DataFrame(result["simulation_summary"]).T
            st.dataframe(sim_df, width="stretch")

        with st.expander("See full raw pipeline output (for the technically curious)"):
            st.json(result)
