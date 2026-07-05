# 🏫 Classroom Air Quality & Infection Risk Monitor — V3

Software-only, database-backed decision-support system built on top of a distributed
sensor-based Fuzzy Decision Tree IAQ project. Converts existing CO₂ / temperature /
humidity / occupancy sensor data into an actionable, explainable, forecastable,
simulate-able, and controllable infection-risk system — no new hardware.

![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)

## What's new in V3 (vs V2)

| Capability | V2 | V3 |
|---|---|---|
| Data persistence | Flat CSV files | ✅ SQLite database (alerts, anomalies, model registry) |
| **Digital Twin** | ❌ | ✅ Interactive what-if ventilation simulator (open windows / reduce occupancy / no action) |
| **RL Ventilation Advisor** | ❌ | ✅ Trained Q-learning agent recommends an action per room state |
| **Sensor anomaly detection** | ❌ | ✅ Hard bounds + Isolation Forest catch faulty/drifting sensors |
| **Model versioning** | ❌ | ✅ Model registry tracks every trained version + auto-promotes the best ("champion") |
| **API security** | Open | ✅ API key required (`X-API-Key` header) on all data endpoints |
| **PDF reporting** | ❌ | ✅ One-click, professional per-room PDF report (charts, tables, alerts, model performance) |
| **Dashboard structure** | Single page | ✅ Multi-page app: Home, Room Detail, Digital Twin, RL Advisor, Sensor Health, Alerts & Models, Reports |
| **API endpoints** | `/predict`, `/health` | ✅ + `/simulate`, `/simulate/compare_all`, `/recommend`, `/alerts`, `/model_history` |

## Folder structure

```
iaq_project/
├── .github/workflows/ci.yml     # CI: trains everything + runs tests on every push
├── api/
│   └── main.py                   # FastAPI service (V3: +security +5 new endpoints)
├── dashboard/
│   ├── Home.py                   # Live risk grid overview
│   └── pages/
│       ├── 1_Room_Detail.py       # Trend, 1-hr forecast, SHAP explanation
│       ├── 2_Digital_Twin.py      # Interactive what-if simulator
│       ├── 3_RL_Advisor.py        # Q-learning ventilation recommendation
│       ├── 4_Sensor_Health.py     # Anomaly detection
│       ├── 5_Alerts_and_Models.py # Alert history + model registry
│       └── 6_Reports.py           # On-demand PDF report generation
├── data/
│   └── generate_sample_data.py   # Sample data generator (swap for real sensor CSV)
├── src/
│   ├── wells_riley.py             # Risk-scoring formula (V1 core, unchanged)
│   ├── label_dataset.py           # Labels dataset with risk categories
│   ├── fuzzy_model.py             # Hand-built fuzzy inference system
│   ├── train_and_compare.py       # Trains + compares Fuzzy Tree vs Neural Network
│   ├── forecast_model.py          # 1-hour-ahead risk forecasting (V2)
│   ├── explainability.py          # SHAP explanations + root-cause diagnosis (V2)
│   ├── alerts.py                  # Alert logging with cooldown (V3: DB-backed)
│   ├── digital_twin.py            # V3: what-if ventilation simulator
│   ├── rl_advisor.py              # V3: Q-learning ventilation advisor
│   ├── anomaly_detection.py       # V3: sensor fault detection
│   └── report_generator.py        # V3: automated PDF reports
├── tests/                          # 21 automated tests across all modules
├── reports/                        # Trained models, accuracy reports, plots, PDFs
├── db.py                           # V3: SQLAlchemy database layer
├── config.yaml                     # Centralized configuration
├── config_loader.py                 # Config + path utilities
├── logging_setup.py                  # Logging setup
├── Dockerfile                        # API container
├── dashboard.Dockerfile               # Dashboard container
├── docker-compose.yml                 # Run both together
├── requirements.txt
├── LICENSE
└── README.md   <- you are here
```

## How to run it (local, in order)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate sample sensor data (skip once you have real data --
#    just replace data/sensor_data.csv, same column format)
python data/generate_sample_data.py

# 3. Label every reading with a risk score/category
python src/label_dataset.py

# 4. Train and compare the two classification models (also registers them in the DB)
python src/train_and_compare.py

# 5. Train the forecasting model
python src/forecast_model.py

# 6. Train the sensor anomaly detector
python src/anomaly_detection.py

# 7. Train the RL ventilation advisor
python src/rl_advisor.py

# 8. Run the test suite (21 tests)
pytest tests/ -v

# 9. Launch the multi-page dashboard
streamlit run dashboard/Home.py

# 10. (Separately) launch the API
uvicorn api.main:app --reload
# visit http://127.0.0.1:8000/docs -- include header: X-API-Key: changeme-iaq-v3-key
```

**Important:** change the `api_key` value in `config.yaml` before any real deployment --
the default `changeme-iaq-v3-key` is a placeholder, not a secret.

## Using YOUR real data instead of the sample data
Replace `data/sensor_data.csv` with your real logged data, keeping these exact column names:
`timestamp, room_id, co2_ppm, temperature_c, humidity_pct, occupancy, room_capacity`

Then re-run steps 3–9 above.

## Running with Docker (when you're ready — not required now)
```bash
docker-compose up --build
```
Train the models locally first (steps 2–7 above) so `reports/*.joblib` exist before building.

## Deploying later (not done yet, by design)
- **Dashboard only:** Streamlit Community Cloud (free, connects directly to your GitHub repo)
- **API only:** Render or Railway (free tier, deploys straight from a Dockerfile)
- **Both together:** any VM/cloud instance running `docker-compose up`

## License
MIT — see [LICENSE](LICENSE).
