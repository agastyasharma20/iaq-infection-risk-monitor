# 🏫 Classroom Air Quality & Infection Risk Monitor — V2

Software-only extension of a distributed sensor-based Fuzzy Decision Tree IAQ project.
Converts existing CO₂ / temperature / humidity / occupancy sensor data into an
actionable, explainable, forecastable infection-risk signal — no new hardware.

![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)

## What's new in V2 (vs V1)

| Capability | V1 | V2 |
|---|---|---|
| Current risk classification | ✅ Fuzzy Tree vs Neural Network | ✅ (unchanged, still the core) |
| **Forecasting** | ❌ | ✅ Predicts risk ~1 hour ahead per room (Gradient Boosting on lag features) |
| **Explainability** | ❌ | ✅ SHAP-based, shows which feature drove the prediction |
| **Root-cause diagnosis** | ❌ | ✅ Labels "Overcrowding" vs "Poor Ventilation Baseline" vs "Combined" |
| **Alerting** | ❌ | ✅ Auto-logs alerts when risk = High, with cooldown to avoid spam |
| **REST API** | ❌ | ✅ FastAPI service (`/predict`, `/health`) with auto-generated docs |
| **Config management** | Hardcoded values | ✅ Single `config.yaml` |
| **Logging** | `print()` | ✅ Proper rotating file + console logging |
| **Tests** | ❌ | ✅ 10 pytest unit tests |
| **Containerization** | ❌ | ✅ Dockerfile (API) + dashboard.Dockerfile + docker-compose.yml |
| **CI/CD** | ❌ | ✅ GitHub Actions: auto-runs full pipeline + tests on every push |

## Folder structure

```
iaq_project/
├── .github/workflows/ci.yml   # GitHub Actions CI pipeline
├── api/
│   └── main.py                 # FastAPI service (V2)
├── dashboard/
│   └── app.py                  # Streamlit dashboard (V2: +forecast +explainability +alerts)
├── data/
│   └── generate_sample_data.py # sample data generator (swap for real sensor CSV)
├── src/
│   ├── wells_riley.py          # risk-scoring formula (V1 core)
│   ├── label_dataset.py        # labels dataset with risk categories
│   ├── fuzzy_model.py          # hand-built fuzzy inference system
│   ├── train_and_compare.py    # trains + compares Fuzzy Tree vs Neural Network
│   ├── forecast_model.py       # V2: 1-hour-ahead risk forecasting
│   ├── explainability.py       # V2: SHAP explanations + root-cause diagnosis
│   └── alerts.py               # V2: alert logging with cooldown
├── tests/
│   ├── test_wells_riley.py     # V2: unit tests for the risk formula
│   └── test_models.py          # V2: unit tests for trained models
├── reports/                     # trained models + accuracy reports + plots
├── config.yaml                  # V2: centralized configuration
├── config_loader.py              # V2: config + path utilities
├── logging_setup.py               # V2: logging setup
├── Dockerfile                      # V2: API container
├── dashboard.Dockerfile            # V2: dashboard container
├── docker-compose.yml              # V2: run both together
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

# 4. Train and compare the two classification models
python src/train_and_compare.py

# 5. Train the V2 forecasting model
python src/forecast_model.py

# 6. Run the test suite
pytest tests/ -v

# 7. Launch the dashboard
streamlit run dashboard/app.py

# 8. (Separately) launch the API
uvicorn api.main:app --reload
# then visit http://127.0.0.1:8000/docs for interactive API docs
```

## Using YOUR real data instead of the sample data
Replace `data/sensor_data.csv` with your real logged data, keeping these exact column names:
`timestamp, room_id, co2_ppm, temperature_c, humidity_pct, occupancy, room_capacity`

Then re-run steps 3–7 above.

## Running with Docker (when you're ready — not required now)
```bash
docker-compose up --build
```
This starts both the API (port 8000) and dashboard (port 8501) as separate containers.
Train the models locally first (steps 2–5 above) so `reports/*.joblib` exist before building.

## Deploying later (not done yet, by design)
Some realistic, low-effort options when you're ready:
- **Dashboard only:** Streamlit Community Cloud (free, connects directly to your GitHub repo)
- **API only:** Render or Railway (free tier, deploys straight from a Dockerfile)
- **Both together:** any VM/cloud instance running `docker-compose up`

## License
MIT — see [LICENSE](LICENSE).
