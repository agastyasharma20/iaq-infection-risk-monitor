"""
backfill_health_history.py -- Populate Historical Trends (V5)
--------------------------------------------------------------------
The monitoring loop (monitor_loop.py) logs a Building Health snapshot
every time it runs live -- but that only builds history going FORWARD
from when you start running it. This script backfills the database
with one Building Health snapshot per timestamp already present in
your historical sensor data, so the Trends dashboard page has
something meaningful to show immediately, without needing days of
live monitoring first.

Run this once after training your models (it needs the trained Fuzzy
Tree model + labeled_data.csv):
    python src/backfill_health_history.py
"""

import os
import sys
import pandas as pd
import joblib
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import load_config, resolve_path
from logging_setup import get_logger
from building_health import compute_building_health
from db import log_building_health

logger = get_logger("backfill_health_history")


def backfill():
    cfg = load_config()
    model_path = resolve_path(cfg["paths"]["reports_dir"], "fuzzy_tree_model.joblib")
    data_path = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])

    model = joblib.load(model_path)
    df = pd.read_csv(data_path, parse_dates=["timestamp"])

    timestamps = sorted(df["timestamp"].unique())
    logged = 0

    for ts in timestamps:
        snapshot = df[df["timestamp"] == ts]
        room_predictions = {}
        for _, row in snapshot.iterrows():
            input_df = pd.DataFrame([{
                "co2_ppm": row.co2_ppm, "temperature_c": row.temperature_c,
                "humidity_pct": row.humidity_pct, "occupancy": row.occupancy,
            }])
            room_predictions[row.room_id] = model.predict(input_df)[0]

        health = compute_building_health(room_predictions)
        log_building_health(
            timestamp=pd.Timestamp(ts).to_pydatetime(), score=health["score"],
            grade=health["grade"], rooms_at_risk=health["rooms_at_risk"],
            total_rooms=health["total_rooms"],
        )
        logged += 1

    logger.info(f"Backfilled {logged} historical Building Health snapshots.")
    return logged


if __name__ == "__main__":
    n = backfill()
    print(f"Backfilled {n} Building Health snapshots into the database.")
