"""
report_generator.py -- Automated PDF Reports (V3)
------------------------------------------------------
Generates a professional, per-room (or whole-building) PDF summary
covering the logged period: risk trend chart, time spent in each risk
category, alert count, and the current model comparison table. This is
the kind of artifact you'd actually hand to your HOD or a facilities
manager weekly -- not just a dashboard screenshot.

Uses reportlab (Platypus) for layout + matplotlib for the embedded chart,
per the project's PDF skill guidance.
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config, resolve_path
from logging_setup import get_logger
from db import get_all_alerts, get_model_history

logger = get_logger("report_generator")


def _make_risk_trend_chart(room_df: pd.DataFrame, room_id: str, out_path: str):
    plt.figure(figsize=(7, 3))
    plt.plot(room_df["timestamp"], room_df["risk_score"], linewidth=1)
    plt.title(f"Infection Risk Score Over Time -- {room_id}")
    plt.xlabel("Time")
    plt.ylabel("Risk Score (0-1)")
    plt.xticks(rotation=45, fontsize=6)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def generate_room_report(room_id: str, output_path: str = None) -> str:
    cfg = load_config()
    data_path = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])
    df = pd.read_csv(data_path, parse_dates=["timestamp"])
    room_df = df[df["room_id"] == room_id].sort_values("timestamp")

    if room_df.empty:
        raise ValueError(f"No data found for room_id='{room_id}'")

    if output_path is None:
        reports_dir = resolve_path(cfg["paths"]["reports_dir"])
        output_path = os.path.join(reports_dir, f"{room_id}_weekly_report.pdf")

    chart_path = os.path.join(os.path.dirname(output_path), f"_tmp_chart_{room_id}.png")
    _make_risk_trend_chart(room_df, room_id, chart_path)

    category_counts = room_df["risk_category"].value_counts()
    total_readings = len(room_df)

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Classroom Air Quality &amp; Infection Risk Report", styles["Title"]))
    story.append(Paragraph(f"Room: {room_id}", styles["Heading2"]))
    story.append(Paragraph(
        f"Period covered: {room_df['timestamp'].min():%d %b %Y} to {room_df['timestamp'].max():%d %b %Y}",
        styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Risk Level Summary", styles["Heading2"]))
    summary_data = [["Risk Category", "Readings", "Percent of Time"]]
    for cat in ["Low", "Medium", "High"]:
        count = int(category_counts.get(cat, 0))
        pct = (count / total_readings * 100) if total_readings else 0
        summary_data.append([cat, str(count), f"{pct:.1f}%"])

    summary_table = Table(summary_data, colWidths=[150, 100, 150])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Risk Trend", styles["Heading2"]))
    story.append(Image(chart_path, width=6.5 * inch, height=2.8 * inch))
    story.append(Spacer(1, 16))

    # Alerts for this room
    all_alerts = get_all_alerts()
    room_alerts = [a for a in all_alerts if a.room_id == room_id]
    story.append(Paragraph(f"Alerts Logged for This Room: {len(room_alerts)}", styles["Heading2"]))
    if room_alerts:
        alert_data = [["Timestamp", "Category", "Root Cause"]]
        for a in room_alerts[:15]:
            alert_data.append([a.timestamp.strftime("%d %b %H:%M"), a.risk_category, a.root_cause])
        alert_table = Table(alert_data, colWidths=[130, 90, 220])
        alert_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c0392b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(alert_table)
    else:
        story.append(Paragraph("No High-risk alerts logged for this room in the covered period.", styles["Normal"]))

    story.append(PageBreak())

    # Model comparison appendix
    story.append(Paragraph("Appendix: Current Model Performance", styles["Heading2"]))
    model_history = get_model_history()
    if model_history:
        model_data = [["Model", "Accuracy", "Champion?", "Trained At"]]
        seen = set()
        for m in model_history:
            if m.model_name in seen:
                continue
            seen.add(m.model_name)
            model_data.append([
                m.model_name, f"{m.accuracy*100:.2f}%",
                "Yes" if m.is_champion else "No", m.trained_at.strftime("%d %b %Y")
            ])
        model_table = Table(model_data, colWidths=[180, 90, 90, 110])
        model_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27ae60")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(model_table)
    else:
        story.append(Paragraph("No model registry entries yet -- run src/train_and_compare.py.", styles["Normal"]))

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    doc.build(story)

    os.remove(chart_path)
    logger.info(f"Generated report: {output_path}")
    return output_path


if __name__ == "__main__":
    cfg = load_config()
    data_path = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])
    df = pd.read_csv(data_path)
    first_room = sorted(df["room_id"].unique())[0]
    path = generate_room_report(first_room)
    print(f"Report generated at: {path}")
