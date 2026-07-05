# 🏫 Classroom Air Quality & Infection Risk Monitor — V4

**The USP in one sentence:** send one sensor reading in, get back a complete,
explained, actioned, plain-English decision out — sensor trust check, risk level,
root cause, what-if simulation of every possible action, the best action, and a
one-sentence recommendation a non-technical teacher can act on immediately.

Software-only. No new hardware, ever. Built on a distributed sensor-based Fuzzy
Decision Tree IAQ project.

![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)

## What's new in V4 (vs V3)

| Capability | V3 | V4 |
|---|---|---|
| **Unified decision pipeline** | 5 separate tools | ✅ `orchestrator.py` -- one call runs everything and returns one decision |
| **Plain-English advisory** | ❌ (raw numbers/labels only) | ✅ Template-based NLG -- one readable sentence, zero external AI cost |
| **Building Health Score** | ❌ | ✅ One number + letter grade (A-F) for the whole building |
| **Real notifications** | Log placeholder only | ✅ Real email support (safe dry-run default, graceful failure handling) |
| **Continuous monitoring** | Manual, one room at a time | ✅ `monitor_loop.py` -- runs the full pipeline across all rooms on a timer |
| **API** | Feature-specific endpoints | ✅ + `/analyze` (the one-call USP endpoint), `/building_health` |
| **Dashboard** | 7 pages | ✅ 9 pages: + Autonomous Advisor, Building Health |

## The core idea (in plain words)

V1, V2, and V3 built five genuinely good tools: a risk classifier, a forecaster, an
explainer, a what-if simulator, and an action recommender. But using them meant
checking five different things and combining the answers yourself.

**V4's orchestrator does that combining for you.** One sensor reading goes in; one
paragraph of plain English comes out, already reasoned through every stage. That's
the actual product now -- not "a set of AI models," but "a system that tells you what
to do, in your own language, and can also do it continuously, unattended, for an
entire building."

## Folder structure

```
iaq_project/
├── .github/workflows/ci.yml
├── api/main.py                        # V4: + /analyze, /building_health
├── dashboard/
│   ├── Home.py
│   └── pages/
│       ├── 1_Room_Detail.py
│       ├── 2_Digital_Twin.py
│       ├── 3_RL_Advisor.py
│       ├── 4_Sensor_Health.py
│       ├── 5_Alerts_and_Models.py
│       ├── 6_Reports.py
│       ├── 7_Autonomous_Advisor.py     # V4: the USP page
│       └── 8_Building_Health.py        # V4
├── data/generate_sample_data.py
├── src/
│   ├── wells_riley.py                   # V1 core (unchanged)
│   ├── label_dataset.py
│   ├── fuzzy_model.py
│   ├── train_and_compare.py
│   ├── forecast_model.py                # V2
│   ├── explainability.py                # V2
│   ├── alerts.py                        # V3 (DB-backed) + V4 (real email)
│   ├── digital_twin.py                  # V3
│   ├── rl_advisor.py                    # V3
│   ├── anomaly_detection.py             # V3
│   ├── report_generator.py              # V3
│   ├── nlg_advisory.py                  # V4: plain-English advisory
│   ├── orchestrator.py                  # V4: THE USP -- unified pipeline
│   ├── building_health.py               # V4: whole-building score
│   └── monitor_loop.py                  # V4: continuous monitoring service
├── tests/                                # 31 automated tests
├── reports/
├── db.py
├── config.yaml
├── config_loader.py
├── logging_setup.py
├── Dockerfile / dashboard.Dockerfile / docker-compose.yml
├── requirements.txt
├── LICENSE
└── README.md
```

## How to run it — step by step

```bash
# 1. Install everything this project needs
pip install -r requirements.txt

# 2. Create the sample sensor data (replace with your real CSV later, same columns)
python data/generate_sample_data.py

# 3. Label every reading with a risk score/category
python src/label_dataset.py

# 4. Train the two risk-classification models (also registers them in the DB)
python src/train_and_compare.py

# 5. Train the 1-hour-ahead forecasting model
python src/forecast_model.py

# 6. Train the sensor-fault anomaly detector
python src/anomaly_detection.py

# 7. Train the RL ventilation advisor
python src/rl_advisor.py

# 8. Run all 31 tests -- confirms everything actually works
pytest tests/ -v

# 9. Try the new V4 centerpiece directly from the command line
python src/orchestrator.py

# 10. Launch the dashboard (9 pages, including Autonomous Advisor and Building Health)
streamlit run dashboard/Home.py

# 11. (Separately) launch the API
uvicorn api.main:app --reload
# visit http://127.0.0.1:8000/docs -- include header: X-API-Key: changeme-iaq-v3-key
# try POST /analyze -- that's the one-call USP endpoint

# 12. (Optional) run the continuous monitoring loop for a few cycles
python src/monitor_loop.py --interval 10 --iterations 3
```

**Change the placeholder API key and email credentials in `config.yaml` before any
real deployment** -- they are intentionally fake defaults, not secrets.

## Using YOUR real data instead of the sample data
Replace `data/sensor_data.csv` with your real logged data (same columns:
`timestamp, room_id, co2_ppm, temperature_c, humidity_pct, occupancy, room_capacity`),
then re-run steps 3–9 above.

## Docker (ready, not required to run now)
```bash
docker-compose up --build
```

## License
MIT — see [LICENSE](LICENSE).
