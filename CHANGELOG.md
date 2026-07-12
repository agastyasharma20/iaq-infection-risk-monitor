# Changelog

All notable changes to this project, by version.

## V6 (Final) — Closing the Gaps
- Configurable room adjacency for cross-room risk propagation (replaces hardcoded grid guess)
- Real per-user API authentication with roles (admin / viewer)
- Federated Learning simulation across synthetic institutions
- Test count: 48

## V5 — Fixing Honest Limitations
- Multi-step (episodic) Q-learning for the RL ventilation advisor
- Graph-based cross-room risk propagation
- Building Health history logging + Trends dashboard page
- Public, unauthenticated `/public/status` endpoint
- First end-to-end integration test
- Test count: 39

## V4 — The Product (USP)
- Autonomous Decision Orchestrator: one function call runs the entire pipeline
- Plain-English (template-based) advisory generator
- Building Health Score (0-100, grade A-F)
- Real email notification support (safe dry-run default)
- Continuous monitoring loop (`monitor_loop.py`)
- `/analyze` API endpoint (the USP, callable)
- Test count: 31

## V3 — The Trust Layer
- SQLite database (alerts, model registry, anomalies)
- Digital Twin what-if ventilation simulator
- Reinforcement Learning ventilation advisor (initial single-step version)
- Sensor anomaly detection (hard bounds + Isolation Forest)
- Model registry with automatic champion promotion
- API key authentication
- Automated PDF report generation
- Multi-page Streamlit dashboard
- Test count: 21

## V2 — The Explainer
- 1-hour-ahead risk forecasting
- SHAP-based explainability + root-cause diagnosis
- Alert logging with cooldown
- FastAPI service (`/predict`, `/health`)
- Centralized config, logging, first test suite
- Test count: 10

## V1 — The Core Model
- Wells-Riley infection risk formula applied to existing CO2/occupancy sensors
- Fuzzy Decision Tree vs Neural Network comparison (continuing the original research question)
- Streamlit dashboard (single page)
- Manual verification only, no automated tests
