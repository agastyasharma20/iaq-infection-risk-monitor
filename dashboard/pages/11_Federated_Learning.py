"""
pages/11_Federated_Learning.py
-----------------------------------
V6: interactive demo of the federated learning simulation -- split the
data across N synthetic institutions, train a model per institution
using ONLY that institution's own data, and compare the federated
(combined) accuracy against what a single institution would get alone.
"""

import streamlit as st
import pandas as pd
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

st.set_page_config(page_title="Federated Learning", layout="wide")
st.title("🤝 Federated Learning Simulation")
st.caption(
    "What if multiple colleges each had their own classrooms and wanted a better, shared "
    "risk model -- without sharing raw sensor data with each other? This simulates that: "
    "the data is split across N synthetic 'institutions', each trains its own model on "
    "**only its own data**, and only the trained models (never the underlying data) are "
    "combined into one federated prediction."
)

from config_loader import load_config, resolve_path  # noqa: E402

cfg = load_config()
DATA_PATH = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])

if not os.path.exists(DATA_PATH):
    st.error("No labeled data found. Run the data pipeline first (see README).")
    st.stop()

n_institutions = st.slider("Number of simulated institutions", 2, 5, 3)

if st.button("Run federated simulation", type="primary"):
    with st.spinner(f"Training {n_institutions} local models, then combining them..."):
        from federated_learning import run_federated_simulation
        result = run_federated_simulation(n_institutions=n_institutions)

    st.markdown("### Results")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Single institution alone", f"{result['single_institution_accuracy']*100:.2f}%")
    with col2:
        st.metric("Federated (combined)", f"{result['federated_accuracy']*100:.2f}%")
    with col3:
        st.metric("Improvement", f"{result['improvement_over_single']*100:+.2f} pts")

    st.markdown("### Per-institution local model accuracy")
    inst_df = pd.DataFrame({
        "Institution": [f"Institution {i+1}" for i in range(len(result["local_accuracies"]))],
        "Local accuracy": [f"{a*100:.2f}%" for a in result["local_accuracies"]],
    })
    st.dataframe(inst_df, width="stretch")

    st.info(
        "Each institution's model was trained using only its own rooms' data. The federated "
        "result combines their predictions (majority vote) without any institution ever "
        "seeing another's raw sensor readings -- that privacy property is the actual point "
        "of federated learning, not just the accuracy number."
    )

st.markdown("---")
st.caption(
    "**Honest note:** this is a genuine, runnable demonstration of the federated learning "
    "concept and its core privacy property, using synthetic institution splits from the "
    "sample dataset. It has not been validated with real partner institutions, which would "
    "require actual data-sharing agreements this project doesn't have."
)
