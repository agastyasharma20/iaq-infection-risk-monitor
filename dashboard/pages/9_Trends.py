"""
pages/9_Trends.py
--------------------
Historical view of the Building Health Score over time -- shows whether
the building is improving, worsening, or has a recurring daily pattern
(e.g. always dips during mid-morning classes). This is the page an
administrator would check weekly, not per-minute.
"""

import streamlit as st
import pandas as pd
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "src"))

from db import get_building_health_history  # noqa: E402

st.set_page_config(page_title="Trends", layout="wide")
st.title("📈 Building Health Trends")
st.caption("Historical Building Health Score over time. Run "
           "`python src/backfill_health_history.py` once to populate this from your "
           "historical data, or let it fill up naturally as `monitor_loop.py` runs.")

history = get_building_health_history(limit=2000)

if not history:
    st.info("No history yet. Run `python src/backfill_health_history.py` to populate this "
             "from your existing labeled data, or run `python src/monitor_loop.py` to start "
             "logging live.")
    st.stop()

df = pd.DataFrame([
    {"timestamp": h.timestamp, "score": h.score, "grade": h.grade,
     "rooms_at_risk": h.rooms_at_risk, "total_rooms": h.total_rooms}
    for h in history
])

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Latest Score", f"{df.iloc[-1]['score']}/100")
with col2:
    st.metric("Average Score (full period)", f"{df['score'].mean():.1f}/100")
with col3:
    trend = df.iloc[-1]["score"] - df.iloc[0]["score"]
    st.metric("Change Over Period", f"{trend:+.1f} points")

st.markdown("### Score over time")
st.line_chart(df.set_index("timestamp")[["score"]])

st.markdown("### Rooms needing attention over time")
st.line_chart(df.set_index("timestamp")[["rooms_at_risk"]])

st.markdown("### Grade distribution over the period")
grade_counts = df["grade"].value_counts().reindex(["A", "B", "C", "D", "F"]).fillna(0)
st.bar_chart(grade_counts)

st.caption(f"Showing {len(df)} logged snapshots from "
           f"{df['timestamp'].min():%d %b %Y} to {df['timestamp'].max():%d %b %Y}.")
