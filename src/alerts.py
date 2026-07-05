"""
alerts.py
----------
V3 update: now backed by the SQLite database (db.py) instead of a flat
CSV file, so alert history can be queried properly (by room, by date
range, by category) instead of just read as a flat table. Cooldown logic
and the notification placeholder are unchanged from V2.
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import load_config
from logging_setup import get_logger
from db import log_alert, get_recent_alert

logger = get_logger("alerts")


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

    cooldown = timedelta(minutes=cfg["alerting"]["cooldown_minutes"])
    ts = timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp))

    last_alert = get_recent_alert(room_id)
    if last_alert is not None and (ts - last_alert.timestamp) < cooldown:
        return False  # still in cooldown, skip

    send_notification(room_id, risk_category, ts, root_cause)
    log_alert(room_id=room_id, risk_category=risk_category, timestamp=ts, root_cause=root_cause)
    return True


if __name__ == "__main__":
    fired = check_and_alert("Room_1", "High", datetime.now(), "Overcrowding")
    print("Alert fired:", fired)
