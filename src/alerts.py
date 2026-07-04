"""
alerts.py
----------
V2 addition: when a room's predicted risk is "High", this logs a
timestamped alert to alerts_log.csv and simulates a notification
(printed here -- swap the `send_notification` function body for a real
email/SMS API call, e.g. smtplib or Twilio, when you deploy for real).

Includes a cooldown so the same room doesn't spam an alert every 15
minutes while it stays in the High category.
"""

import os
import sys
import csv
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config, resolve_path
from logging_setup import get_logger

logger = get_logger("alerts")


def _alerts_log_path(cfg):
    return resolve_path(cfg["paths"]["data_dir"], cfg["paths"]["alerts_log_file"])


def _load_recent_alerts(cfg) -> dict:
    """Returns {room_id: last_alert_datetime} from the log file, if it exists."""
    path = _alerts_log_path(cfg)
    last_alerts = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                last_alerts[row["room_id"]] = datetime.fromisoformat(row["timestamp"])
    return last_alerts


def send_notification(room_id: str, risk_category: str, timestamp, root_cause: str = ""):
    """
    Placeholder notification channel. Replace this with a real email/SMS
    call for production use. Kept as a plain function so the rest of the
    system doesn't need to change when you wire up a real channel.
    """
    logger.warning(f"ALERT: {room_id} is at {risk_category} risk at {timestamp}. Cause: {root_cause}")


def check_and_alert(room_id: str, risk_category: str, timestamp, root_cause: str = ""):
    cfg = load_config()
    if not cfg["alerting"]["enabled"]:
        return False
    if risk_category != cfg["alerting"]["trigger_category"]:
        return False

    last_alerts = _load_recent_alerts(cfg)
    cooldown = timedelta(minutes=cfg["alerting"]["cooldown_minutes"])
    last_time = last_alerts.get(room_id)

    ts = timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp))

    if last_time is not None and (ts - last_time) < cooldown:
        return False  # still in cooldown, skip

    send_notification(room_id, risk_category, ts, root_cause)

    path = _alerts_log_path(cfg)
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "room_id", "risk_category", "root_cause"])
        writer.writerow([ts.isoformat(), room_id, risk_category, root_cause])

    return True


if __name__ == "__main__":
    from datetime import datetime
    fired = check_and_alert("Room_1", "High", datetime.now(), "Overcrowding")
    print("Alert fired:", fired)
