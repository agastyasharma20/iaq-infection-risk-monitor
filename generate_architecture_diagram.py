"""
generate_architecture_diagram.py -- draws the orchestrator pipeline
diagram used as the centerpiece visual of the final report.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os
os.makedirs("reports/_chart_assets", exist_ok=True)

fig, ax = plt.subplots(figsize=(11, 6.5))
ax.set_xlim(0, 11)
ax.set_ylim(-1, 6.5)
ax.axis("off")

def box(x, y, w, h, text, facecolor, textcolor="white", fontsize=9.5, fontweight="bold"):
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.12",
                        linewidth=1.2, edgecolor="#333333", facecolor=facecolor, zorder=2)
    ax.add_patch(b)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fontsize,
            color=textcolor, fontweight=fontweight, zorder=3, wrap=True)
    return b

def arrow(x1, y1, x2, y2, color="#555555"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
                         linewidth=1.6, color=color, zorder=1)
    ax.add_patch(a)

ax.text(5.5, 6.2, "Autonomous Decision Orchestrator -- process_reading()", ha="center",
        fontsize=13, fontweight="bold", color="#1a1a1a")
ax.text(5.5, 5.85, "One sensor reading in -> one complete, explained, actioned decision out",
        ha="center", fontsize=9.5, style="italic", color="#555555")

box(0.2, 4.9, 1.6, 0.7, "Sensor\nReading", "#4a4a4a")
arrow(1.8, 5.25, 2.3, 5.25)

box(2.3, 4.9, 1.9, 0.7, "1. Trust Check\n(Anomaly Detection)", "#8e44ad")
arrow(4.2, 5.25, 4.7, 5.25)

box(4.7, 4.9, 1.9, 0.7, "2. Risk +\nRoot Cause (SHAP)", "#2c5f8a")
arrow(5.65, 4.9, 5.65, 4.3)

box(4.7, 3.6, 1.9, 0.7, "3. Simulate Every\nAction (Digital Twin)", "#16a085")
arrow(5.65, 3.6, 5.65, 3.0)

box(4.7, 2.3, 1.9, 0.7, "4. Pick Best Action\n(RL Advisor)", "#d68910")
arrow(5.65, 2.3, 5.65, 1.7)

box(4.7, 1.0, 1.9, 0.7, "5. Plain-English\nAdvisory (NLG)", "#c0392b")
arrow(6.6, 1.35, 7.1, 1.35)

box(7.1, 1.0, 2.0, 0.7, "One Sentence:\nWhat's happening +\nwhat to do", "#1a1a1a", fontsize=8.8)

arrow(5.65, 1.0, 5.65, 0.4)
box(4.7, -0.3, 1.9, 0.7, "6. Log Alert\n(if High risk)", "#7f8c8d")

box(7.4, 3.6, 2.3, 0.7, "Cross-Room Graph\n(neighbor escalation)", "#5b8c85", fontsize=8.8)
box(7.4, 2.5, 2.3, 0.7, "Building Health Score\n(whole-building grade)", "#5b8c85", fontsize=8.8)
box(7.4, 4.7, 2.3, 0.7, "SQLite Database\n(alerts, models, history)", "#5b8c85", fontsize=8.8)

arrow(6.6, 4.25, 7.4, 4.0, color="#aaaaaa")
arrow(6.6, 2.65, 7.4, 2.85, color="#aaaaaa")
arrow(6.6, 5.15, 7.4, 5.05, color="#aaaaaa")

ax.text(0.2, -0.75, "Also connects to: FastAPI (/analyze), Streamlit dashboard, continuous monitoring loop,\n"
                    "federated learning across institutions", fontsize=8, color="#666666", style="italic")

plt.tight_layout()
plt.savefig("reports/_chart_assets/architecture_diagram.png", dpi=170, bbox_inches="tight")
plt.close()
print("Architecture diagram saved.")
