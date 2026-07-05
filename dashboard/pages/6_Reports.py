"""
pages/6_Reports.py
---------------------
Generates a professional PDF report for a chosen room, on demand, and
offers it as a download.
"""

import streamlit as st
import pandas as pd
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from config_loader import load_config, resolve_path  # noqa: E402

st.set_page_config(page_title="Reports", layout="wide")
st.title("📄 Automated PDF Reports")
st.caption("Generates a per-room summary: risk-level breakdown, trend chart, alert history, "
           "and current model performance -- ready to hand to your HOD or facilities team.")

cfg = load_config()
DATA_PATH = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])

if not os.path.exists(DATA_PATH):
    st.error("No labeled data found. Run the data pipeline first (see README).")
    st.stop()

df = pd.read_csv(DATA_PATH)
rooms = sorted(df["room_id"].unique())
room_choice = st.selectbox("Select a room", rooms)

if st.button("Generate PDF report"):
    from report_generator import generate_room_report
    with st.spinner(f"Generating report for {room_choice}..."):
        path = generate_room_report(room_choice)
    st.success(f"Report generated: {os.path.basename(path)}")
    with open(path, "rb") as f:
        st.download_button(
            label="⬇️ Download PDF",
            data=f.read(),
            file_name=os.path.basename(path),
            mime="application/pdf",
        )
