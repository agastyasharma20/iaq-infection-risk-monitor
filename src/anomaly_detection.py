"""
anomaly_detection.py -- Self-Diagnosing Sensor Layer (V3)
--------------------------------------------------------------
Distributed sensor networks fail in boring, common ways: a stuck sensor
reporting the same value for hours, an impossible jump (CO2 from 500 to
3000 in one reading), or a sensor reporting outside physically plausible
bounds. Left undetected, these poison every model downstream.

This module trains an Isolation Forest (an unsupervised anomaly
detection algorithm) on your sensor readings and flags statistically
unusual rows -- the "Self-Diagnosing Sensor Agent" idea from your
original brainstorm, in its simplest genuinely useful form.

Detected anomalies are logged to the database (db.py) so they show up
in the dashboard's Sensor Health page.
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config, resolve_path
from logging_setup import get_logger
from db import log_anomaly

logger = get_logger("anomaly_detection")

from sklearn.ensemble import IsolationForest


def train_anomaly_detector():
    cfg = load_config()
    data_path = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])
    df = pd.read_csv(data_path)

    features = cfg["features"]
    X = df[features]

    model = IsolationForest(contamination=0.01, random_state=cfg["model"]["random_state"])
    model.fit(X)

    out_path = resolve_path(cfg["paths"]["reports_dir"], "anomaly_model.joblib")
    joblib.dump(model, out_path)
    logger.info(f"Anomaly detector trained on {len(df)} readings, saved to {out_path}")
    return model


def check_reading_for_anomaly(room_id: str, co2_ppm: float, temperature_c: float,
                                humidity_pct: float, occupancy: int, timestamp=None) -> bool:
    """
    Returns True if this reading looks anomalous (likely sensor fault),
    and logs it to the database if so.

    Combines TWO detection layers:
    1. Hard physical bounds check (catches extreme, physically impossible
       values instantly and reliably -- Isolation Forest alone can miss
       single-feature extreme outliers when they fall outside the range
       it was trained on, which is a documented limitation of the
       algorithm, not just a threshold-tuning issue).
    2. Isolation Forest (catches subtler, multi-feature statistical
       outliers that are individually plausible but jointly unusual,
       e.g. very high CO2 with implausibly low occupancy for that level).
    """
    cfg = load_config()
    model_path = resolve_path(cfg["paths"]["reports_dir"], "anomaly_model.joblib")
    model = joblib.load(model_path)

    input_df = pd.DataFrame([{
        "co2_ppm": co2_ppm, "temperature_c": temperature_c,
        "humidity_pct": humidity_pct, "occupancy": occupancy,
    }])[cfg["features"]]

    reason = _diagnose_anomaly_reason(co2_ppm, temperature_c, humidity_pct, occupancy)
    hard_bounds_flagged = reason != "Unusual combination of readings (statistical outlier)"

    ml_prediction = model.predict(input_df)[0]  # -1 = anomaly, 1 = normal
    ml_flagged = ml_prediction == -1

    is_anomaly = bool(hard_bounds_flagged or ml_flagged)

    if is_anomaly:
        from datetime import datetime
        ts = timestamp or datetime.now()
        log_anomaly(room_id=room_id, timestamp=ts, reason=reason)
        logger.warning(f"Sensor anomaly detected in {room_id}: {reason}")

    return is_anomaly


def _diagnose_anomaly_reason(co2_ppm, temperature_c, humidity_pct, occupancy) -> str:
    """Simple, explainable reason-tagging for the flagged anomaly."""
    reasons = []
    if co2_ppm < 400 or co2_ppm > 5000:
        reasons.append("CO2 outside physically plausible range")
    if temperature_c < 10 or temperature_c > 45:
        reasons.append("Temperature outside plausible classroom range")
    if humidity_pct < 10 or humidity_pct > 95:
        reasons.append("Humidity outside plausible range")
    if occupancy < 0 or occupancy > 100:
        reasons.append("Occupancy outside plausible range")
    if not reasons:
        reasons.append("Unusual combination of readings (statistical outlier)")
    return "; ".join(reasons)


if __name__ == "__main__":
    train_anomaly_detector()

    # Demo: one normal reading, one clearly faulty reading
    print("Normal reading flagged as anomaly:",
          check_reading_for_anomaly("Room_1", 1800, 26, 55, 35))
    print("Faulty reading (impossible CO2) flagged as anomaly:",
          check_reading_for_anomaly("Room_2", 9999, 26, 55, 35))
