"""
pages/5_Alerts_and_Models.py
-------------------------------
Alert history (from the database) and the model registry -- every
trained model version, its accuracy, and which one is currently the
"champion".
"""

import streamlit as st
import pandas as pd
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from db import get_all_alerts, get_model_history  # noqa: E402

st.set_page_config(page_title="Alerts & Models", layout="wide")
st.title("🔔 Alerts & 📦 Model Registry")

st.markdown("### Alert history")
alerts = get_all_alerts()
if alerts:
    alerts_df = pd.DataFrame([
        {"Timestamp": a.timestamp, "Room": a.room_id, "Category": a.risk_category, "Root Cause": a.root_cause}
        for a in alerts
    ])
    st.dataframe(alerts_df, width="stretch")
else:
    st.info("No alerts logged yet. Alerts fire automatically when a room's predicted risk is High.")

st.markdown("---")
st.markdown("### Model registry -- every trained version")
history = get_model_history()
if history:
    hist_df = pd.DataFrame([
        {"Trained At": m.trained_at, "Model": m.model_name, "Accuracy": f"{m.accuracy*100:.2f}%",
         "Champion": "🏆" if m.is_champion else "", "Notes": m.notes}
        for m in history
    ])
    st.dataframe(hist_df, width="stretch")
    st.caption("Every time you re-run `train_and_compare.py`, the new model is compared against "
               "the current champion for its type and promoted automatically if it's more accurate.")
else:
    st.info("No models registered yet. Run `python src/train_and_compare.py` first.")
