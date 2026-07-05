"""
monitor_loop.py -- Continuous Autonomous Monitoring (V4)
--------------------------------------------------------------
Runs the orchestrator across every room, repeatedly, on a fixed
interval -- turning the project from "a script you run manually" into
"a service that watches the building continuously," which is what a
real deployment actually needs.

In a real deployment, replace `_get_latest_reading_for_room()` with a
call to your actual live sensor feed (MQTT, a REST endpoint, a database
table your IoT gateway writes to, etc). It currently reads the most
recent row per room from the sample/real CSV, so this is runnable and
testable right now without any live sensors connected.

RUN WITH:
    python src/monitor_loop.py --interval 15 --iterations 3

(iterations defaults to run forever; a finite number is used here for
safe demonstration/testing purposes.)
"""

import os
import sys
import time
import argparse
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import load_config, resolve_path
from logging_setup import get_logger
from orchestrator import process_reading
from building_health import compute_building_health

logger = get_logger("monitor_loop")


def _get_latest_reading_for_room(df: pd.DataFrame, room_id: str) -> dict:
    room_df = df[df["room_id"] == room_id].sort_values("timestamp")
    latest = room_df.iloc[-1]
    return {
        "co2_ppm": float(latest.co2_ppm), "temperature_c": float(latest.temperature_c),
        "humidity_pct": float(latest.humidity_pct), "occupancy": int(latest.occupancy),
    }


def run_monitoring_cycle(df: pd.DataFrame) -> dict:
    """Runs one full pass across all rooms, returns the building health summary."""
    rooms = sorted(df["room_id"].unique())
    room_predictions = {}

    for room_id in rooms:
        reading = _get_latest_reading_for_room(df, room_id)
        result = process_reading(room_id=room_id, **reading)
        if result["risk_category"] is not None:
            room_predictions[room_id] = result["risk_category"]
        if result.get("alert_fired"):
            logger.warning(f"Cycle alert: {result['advisory']}")

    health = compute_building_health(room_predictions)
    logger.info(f"Cycle complete. Building Health Score: {health['score']}/100 "
                f"(Grade {health['grade']}), {health['rooms_at_risk']}/{health['total_rooms']} rooms need attention")
    return health


def main():
    parser = argparse.ArgumentParser(description="Run continuous autonomous IAQ monitoring.")
    parser.add_argument("--interval", type=int, default=15, help="Seconds between cycles")
    parser.add_argument("--iterations", type=int, default=3,
                        help="Number of cycles to run (use a large number or a loop wrapper for 'forever' in real deployment)")
    args = parser.parse_args()

    cfg = load_config()
    data_path = resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["labeled_data_file"])
    df = pd.read_csv(data_path, parse_dates=["timestamp"])

    logger.info(f"Starting monitoring loop: {args.iterations} cycles, {args.interval}s apart.")
    for i in range(args.iterations):
        logger.info(f"--- Cycle {i + 1}/{args.iterations} ---")
        run_monitoring_cycle(df)
        if i < args.iterations - 1:
            time.sleep(args.interval)

    logger.info("Monitoring loop finished (reached configured iteration limit).")


if __name__ == "__main__":
    main()
