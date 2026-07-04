"""
forecast_model.py
-------------------
V2 addition: instead of only classifying CURRENT risk, this predicts risk
~1 hour AHEAD per room, using recent lag features (last 4 readings of
CO2/temp/humidity/occupancy). This turns the system from reactive
("risk is high right now") into proactive ("risk will likely become
high in the next hour -- ventilate now").

Approach: Gradient Boosting Regressor predicting the numeric risk_score
`horizon_steps` intervals ahead, trained per-room-agnostic (room_id is
not used as a feature so the model generalizes across rooms).
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config, resolve_path
from logging_setup import get_logger

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

logger = get_logger("forecast_model")


def build_lag_features(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    For each room, builds lag features (previous N readings) and a target
    column = risk_score `horizon_steps` intervals in the future.
    """
    lag_steps = cfg["forecasting"]["lag_steps"]
    horizon = cfg["forecasting"]["horizon_steps"]
    features = cfg["features"]

    all_rows = []
    for room_id, room_df in df.groupby("room_id"):
        room_df = room_df.sort_values("timestamp").reset_index(drop=True)

        for lag in range(1, lag_steps + 1):
            for feat in features:
                room_df[f"{feat}_lag{lag}"] = room_df[feat].shift(lag)

        room_df["target_risk_score"] = room_df["risk_score"].shift(-horizon)
        all_rows.append(room_df)

    combined = pd.concat(all_rows, ignore_index=True)
    combined = combined.dropna().reset_index(drop=True)
    return combined


def train_forecast_model():
    cfg = load_config()
    data_path = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])
    df = pd.read_csv(data_path, parse_dates=["timestamp"])

    featured = build_lag_features(df, cfg)

    feature_cols = [c for c in featured.columns if "_lag" in c]
    X = featured[feature_cols]
    y = featured["target_risk_score"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=cfg["model"]["test_size"], random_state=cfg["model"]["random_state"]
    )

    model = GradientBoostingRegressor(random_state=cfg["model"]["random_state"])
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    logger.info(f"Forecast model trained. MAE on held-out test set: {mae:.4f} (risk score is 0-1 scale)")

    out_path = resolve_path(cfg["paths"]["reports_dir"], "forecast_model.joblib")
    joblib.dump({"model": model, "feature_cols": feature_cols, "mae": mae}, out_path)
    logger.info(f"Saved forecast model to {out_path}")
    return mae


def forecast_for_room(room_history: pd.DataFrame) -> float:
    """
    Given the most recent readings for a single room (sorted by time,
    at least lag_steps+1 rows), returns a forecasted risk score for
    `horizon_steps` intervals ahead.
    """
    cfg = load_config()
    lag_steps = cfg["forecasting"]["lag_steps"]
    features = cfg["features"]

    bundle_path = resolve_path(cfg["paths"]["reports_dir"], "forecast_model.joblib")
    bundle = joblib.load(bundle_path)
    model, feature_cols = bundle["model"], bundle["feature_cols"]

    recent = room_history.sort_values("timestamp").tail(lag_steps + 1).reset_index(drop=True)
    if len(recent) < lag_steps + 1:
        return None  # not enough history yet

    row = {}
    for lag in range(1, lag_steps + 1):
        source_row = recent.iloc[-(lag + 1)]
        for feat in features:
            row[f"{feat}_lag{lag}"] = source_row[feat]

    X = pd.DataFrame([row])[feature_cols]
    return float(np.clip(model.predict(X)[0], 0, 1))


if __name__ == "__main__":
    train_forecast_model()
