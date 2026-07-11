# 🏫 Classroom Air Quality & Infection Risk Monitor — V5

**The USP in one sentence:** send one sensor reading in, get back a complete,
explained, actioned, plain-English decision out — sensor trust check, risk level,
root cause, what-if simulation of every possible action, the best action, and a
one-sentence recommendation anyone can act on immediately.

Software-only. No new hardware, ever.

![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)

## What's new in V5 (vs V4)

| Capability | V4 | V5 |
|---|---|---|
| RL Advisor | Single-step (bandit-style) training | ✅ Genuine multi-step episodic training with discounted returns |
| **Cross-room modeling** | Every room predicted independently | ✅ Graph-based propagation — a risky room can pull a safe neighbor's risk up |
| **Building health over time** | Snapshot only | ✅ Full history logged + a Trends dashboard page |
| **Public transparency** | Everything behind an API key | ✅ `/public/status` — one deliberately open endpoint for external viewers |
| **Testing** | 31 tests | ✅ 39 tests, including the project's first true end-to-end integration test |

## How to run it — step by step

```bash
# 1. Install everything
pip install -r requirements.txt

# 2. Generate sample sensor data (replace with your real CSV later, same columns)
python data/generate_sample_data.py

# 3. Label every reading with a risk score/category
python src/label_dataset.py

# 4. Train the risk-classification models
python src/train_and_compare.py

# 5. Train the forecasting model
python src/forecast_model.py

# 6. Train the sensor-fault anomaly detector
python src/anomaly_detection.py

# 7. Train the (now multi-step) RL ventilation advisor
python src/rl_advisor.py

# 8. Backfill Building Health history so the Trends page has data immediately
python src/backfill_health_history.py

# 9. Run all 39 tests
pytest tests/ -v

# 10. Try the centerpiece directly
python src/orchestrator.py

# 11. Launch the dashboard (11 pages now)
streamlit run dashboard/Home.py

# 12. (Separately) launch the API
uvicorn api.main:app --reload
# visit http://127.0.0.1:8000/docs
# most endpoints need header: X-API-Key: changeme-iaq-v3-key
# EXCEPT /public/status -- that one is deliberately open, no key needed

# 13. (Optional) run continuous monitoring for a few cycles
python src/monitor_loop.py --interval 10 --iterations 3
```

**Change the placeholder API key and email credentials in `config.yaml` before any
real deployment.**

**Important:** the room-adjacency graph used for cross-room risk propagation
(`src/graph_propagation.py`) is a placeholder 3x3 grid guess, not a real floor plan —
update it with your actual building layout before trusting that page's output.

## Folder structure (new in V5 marked)

```
iaq_project/
├── api/main.py                        # V5: + /public/status, /building_graph
├── dashboard/
│   ├── Home.py
│   └── pages/
│       ├── 1_Room_Detail.py .. 8_Building_Health.py   (V2-V4)
│       ├── 9_Trends.py                 # V5
│       └── 10_Cross_Room_Risk.py       # V5
├── src/
│   ├── ... (V1-V4 modules unchanged)
│   ├── graph_propagation.py            # V5: cross-room risk propagation
│   └── backfill_health_history.py      # V5: populate historical trends
├── tests/                               # 39 tests total
├── db.py                                # V5: + BuildingHealthLog table
├── config.yaml / config_loader.py / logging_setup.py
├── Dockerfile / dashboard.Dockerfile / docker-compose.yml
├── requirements.txt
└── README.md
```

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
