# 🏫 Classroom Air Quality & Infection Risk Monitor — V6

**The USP in one sentence:** send one sensor reading in, get back a complete,
explained, actioned, plain-English decision out — sensor trust check, risk level,
root cause, what-if simulation of every possible action, the best action, and a
one-sentence recommendation anyone can act on immediately.

Software-only. No new hardware, ever.

![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)

## What's new in V6 (vs V5)

| Capability | V5 | V6 |
|---|---|---|
| Room adjacency (cross-room risk) | Hardcoded 3x3 grid guess | ✅ Configurable in `config.yaml` — edit to match your real floor plan |
| **API authentication** | One shared key for everyone | ✅ Real per-user keys with roles (`admin` / `viewer`), tested live |
| **Federated Learning** | Not built | ✅ Working simulation across synthetic institutions — the last untouched idea from the original brainstorm |
| **Testing** | 39 tests | ✅ 48 tests |

## The project, in one sentence

A software-only system that turns existing classroom air sensors into an autonomous
decision-support system — it detects infection risk, explains the cause, simulates
fixes, recommends the best action in plain English, watches for broken sensors,
tracks trends over time, accounts for how neighboring rooms affect each other, and
can even train collaboratively across institutions without sharing raw data — all
with zero new hardware.

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

# 7. Train the multi-step RL ventilation advisor
python src/rl_advisor.py

# 8. Backfill Building Health history for the Trends page
python src/backfill_health_history.py

# 9. Run all 48 tests
pytest tests/ -v

# 10. Try the centerpiece directly
python src/orchestrator.py

# 11. Try the federated learning simulation directly
python src/federated_learning.py

# 12. Launch the dashboard (12 pages now)
streamlit run dashboard/Home.py

# 13. (Separately) launch the API
uvicorn api.main:app --reload
# visit http://127.0.0.1:8000/docs
# admin key:  admin-changeme-key-please-replace   (full access)
# viewer key: viewer-changeme-key-please-replace  (read-only endpoints)
# /public/status needs no key at all -- deliberately open

# 14. (Optional) run continuous monitoring for a few cycles
python src/monitor_loop.py --interval 10 --iterations 3
```

**Before any real deployment, change:**
1. The API keys in `config.yaml`'s `api.users` list (the shipped ones are placeholders)
2. The `building_layout.adjacency` list to match your real floor plan
3. The email credentials in `config.yaml`'s `alerting.email` section, if you want real notifications

## Folder structure (V6 additions marked)

```
iaq_project/
├── api/main.py                        # V6: real per-user roles (admin/viewer)
├── dashboard/pages/
│   ├── ... (V2-V5 pages)
│   └── 11_Federated_Learning.py        # V6
├── src/
│   ├── ... (V1-V5 modules)
│   └── federated_learning.py           # V6
├── tests/                               # 48 tests total
├── config.yaml                          # V6: + building_layout, api.users
├── db.py
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
