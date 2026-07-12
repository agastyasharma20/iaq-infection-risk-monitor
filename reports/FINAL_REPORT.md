# Classroom Air Quality & Infection Risk Monitor
## Final Project Report — Version 6

> **See `reports/FINAL_REPORT.pdf` for the full visual report with diagrams and charts.**
> This file is the concise, text-only companion for quick reading on GitHub.

---

## What this project is, in one sentence

**A software-only system that turns existing classroom air sensors into an autonomous
decision-support system** — it detects infection risk, explains the cause, simulates
fixes, recommends the best action in plain English, watches for broken sensors, tracks
trends over time, accounts for neighboring-room effects, and can train collaboratively
across institutions — with **zero new hardware**, at any point across all six versions.

## The USP

> *"Send one sensor reading in. Get back a complete, explained, actioned, plain-English
> decision out."*

That's `src/orchestrator.py`'s `process_reading()` — the single function that ties
every other capability together into one callable decision.

## The core science, briefly

The original research found CO₂ alone cannot judge general air quality. This project
kept that finding and reframed it: CO₂ **is** an excellent proxy for how much air has
already been breathed by other people — exactly what the published **Wells-Riley
model** needs to estimate relative airborne infection risk. The original Fuzzy Decision
Tree vs Neural Network comparison was carried forward onto this new target
(99.26% vs 99.81% accuracy on the sample dataset).

## Version-by-version summary

| Ver. | Theme | Key additions | Tests |
|---|---|---|---|
| V1 | The Core Model | Wells-Riley scoring; Fuzzy Tree vs Neural Network | 0 |
| V2 | The Explainer | Forecasting; SHAP explainability; alerting; REST API | 10 |
| V3 | The Trust Layer | Database; Digital Twin; RL advisor; anomaly detection; PDF reports | 21 |
| V4 | The Product (USP) | Autonomous Orchestrator; plain-English NLG; Building Health Score | 31 |
| V5 | Fixing Limitations | Multi-step RL; cross-room graph propagation; trends; public endpoint | 39 |
| V6 | Closing the Gaps | Configurable floor plan; role-based API auth; federated learning | 48 |

## Complete feature list

**Core AI:** Wells-Riley risk scoring · Fuzzy Tree vs Neural Network · 1hr forecasting ·
SHAP explainability + root cause · sensor anomaly detection · Digital Twin simulator ·
multi-step RL ventilation advisor · graph-based cross-room propagation · federated
learning simulation

**Product:** Autonomous Decision Orchestrator · plain-English advisory (NLG) ·
Building Health Score (0–100, A–F) · historical trends · automated PDF reports

**Infrastructure:** SQLite database · model registry with auto-promotion · centralized
config · structured logging · real email notifications (safe dry-run) · continuous
monitoring loop · configurable real floor plan

**Operations:** REST API (13+ endpoints) · role-based auth (admin/viewer) · public
status endpoint · Docker · GitHub Actions CI · 48 automated tests · one-command setup
(`run_pipeline.py`) · system health check (`verify_system.py`)

## Honest limitations

- All results validated on **synthetic sample data**, not yet real sensor logs
- Room floor plan is configurable but ships with a placeholder layout
- Federated learning uses synthetic institution splits, not real partner institutions
- Graph propagation is a single-layer graph convolution, not a deep GNN
- Email notifications are implemented but untested against a live mailbox
- API auth uses static configured keys, not full identity federation (OAuth/SSO)

Every version's report states limitations explicitly — this is deliberate, and it's
the correct posture for both good research practice and a credible viva defense.

## Conclusion

This project took one real limitation from the original research and turned it into
the foundation of a complete, tested, documented, autonomous decision-support system —
without changing a single sensor. Every realistic idea from the original research
brainstorm that didn't require new hardware or real inter-institutional partnerships
has now been implemented and tested. The natural next step is validating this system
against real sensor data from the actual classroom deployment.

---
*Full technical detail for each version: `reports/PROJECT_REPORT.md` (V1) through
`reports/V6_UPGRADE_REPORT.md`. Full visual report: `reports/FINAL_REPORT.pdf`.*
