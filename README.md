# 🏫 Classroom Air Quality & Infection Risk Monitor — Final (V6)

**The USP in one sentence:** send one sensor reading in, get back a complete,
explained, actioned, plain-English decision out — sensor trust check, risk level,
root cause, what-if simulation of every possible action, the best action, and a
one-sentence recommendation anyone can act on immediately.

Software-only. No new hardware, ever, across all six versions.

![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)

📄 **Full visual report:** [`reports/FINAL_REPORT.pdf`](reports/FINAL_REPORT.pdf)
(architecture diagrams, charts, complete feature matrix, honest limitations)
📝 **Concise version:** [`reports/FINAL_REPORT.md`](reports/FINAL_REPORT.md)

## Quickest possible start (one command)

```bash
pip install -r requirements.txt
python run_pipeline.py --with-tests
streamlit run dashboard/Home.py
```

That's it — `run_pipeline.py` runs all 9 setup steps (data, labeling, training every
model, backfilling history, smoke tests) in the correct order automatically. Run
`python verify_system.py` any time to check the system is fully ready (22 checks).

## What this project actually is

A software-only system that turns existing classroom air sensors into an autonomous
decision-support system — it detects infection risk, explains the cause, simulates
fixes, recommends the best action in plain English, watches for broken sensors,
tracks trends over time, accounts for how neighboring rooms affect each other, and
can train collaboratively across institutions without sharing raw data.

## Version history

| Ver. | Theme | Tests |
|---|---|---|
| V1 | The Core Model — Wells-Riley risk scoring, Fuzzy Tree vs Neural Network | 0 |
| V2 | The Explainer — forecasting, SHAP explainability, alerting, REST API | 10 |
| V3 | The Trust Layer — database, Digital Twin, RL advisor, anomaly detection | 21 |
| V4 | The Product (USP) — Autonomous Orchestrator, plain-English NLG | 31 |
| V5 | Fixing Limitations — multi-step RL, cross-room graph propagation | 39 |
| V6 | Closing the Gaps — configurable floor plan, role-based auth, federated learning | 48 |

See `CHANGELOG.md` for details, or `reports/V*_UPGRADE_REPORT.md` for the full story
behind each version, including bugs found and honest limitations.

## Manual step-by-step (if you don't want the one-command version)

```bash
pip install -r requirements.txt
python data/generate_sample_data.py
python src/label_dataset.py
python src/train_and_compare.py
python src/forecast_model.py
python src/anomaly_detection.py
python src/rl_advisor.py
python src/backfill_health_history.py
pytest tests/ -v
python src/orchestrator.py            # try the centerpiece directly
python src/federated_learning.py      # try the federated simulation directly
streamlit run dashboard/Home.py       # launch the 12-page dashboard
uvicorn api.main:app --reload         # launch the API (separate terminal)
python src/monitor_loop.py --interval 10 --iterations 3   # optional: continuous monitoring
```

## API access

Visit `http://127.0.0.1:8000/docs` for interactive documentation.

| Key | Role | Access |
|---|---|---|
| `admin-changeme-key-please-replace` | admin | Everything |
| `viewer-changeme-key-please-replace` | viewer | Read-only endpoints |
| *(none)* | — | `/health` and `/public/status` only |

**Before any real deployment, change:**
1. The API keys in `config.yaml`'s `api.users` list
2. The `building_layout.adjacency` list to match your real floor plan
3. The email credentials in `config.yaml`'s `alerting.email` section

## Folder structure

```
iaq_project/
├── run_pipeline.py          # one-command setup
├── verify_system.py         # system readiness check (22 checks)
├── generate_final_report.py # rebuilds reports/FINAL_REPORT.pdf
├── CHANGELOG.md
├── api/main.py               # FastAPI, 13+ endpoints, role-based auth
├── dashboard/                # Streamlit, 12 pages
│   ├── Home.py
│   └── pages/1_Room_Detail.py ... 11_Federated_Learning.py
├── src/                      # 20 modules: core model through federated learning
├── tests/                    # 48 tests across 6 test files
├── reports/
│   ├── FINAL_REPORT.pdf      # the complete visual capstone report
│   ├── FINAL_REPORT.md       # concise companion
│   └── V1-V6 upgrade reports
├── db.py / config.yaml / config_loader.py / logging_setup.py
├── Dockerfile / dashboard.Dockerfile / docker-compose.yml
├── requirements.txt
└── README.md
```

## Using YOUR real data instead of the sample data
Replace `data/sensor_data.csv` with your real logged data (same columns:
`timestamp, room_id, co2_ppm, temperature_c, humidity_pct, occupancy, room_capacity`),
then run `python run_pipeline.py --skip-data --with-tests`.

## Docker (ready, not required to run now)
```bash
docker-compose up --build
```


## License
**Proprietary — All Rights Reserved.** This code may not be copied, reused,
redistributed, or used in any form without prior written permission from the
author. See [LICENSE](LICENSE). Unauthorized use may result in legal action.
