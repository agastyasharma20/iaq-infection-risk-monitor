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
    Sends a real notification if configured to (channel="email", dry_run=false),
    otherwise safely logs what WOULD be sent. Defaults to the safe logging
    path so this never accidentally emails anyone until you deliberately
    configure it in config.yaml.
    """
    cfg = load_config()
    alert_cfg = cfg["alerting"]
    message = f"ALERT: {room_id} is at {risk_category} risk at {timestamp}. Cause: {root_cause}"

    if alert_cfg["notification_channel"] != "email" or alert_cfg["dry_run"]:
        logger.warning(f"[DRY RUN / LOG ONLY] {message}")
        return

    try:
        _send_email(alert_cfg["email"], subject=f"IAQ Alert: {room_id} - {risk_category} Risk",
                    body=message)
        logger.warning(f"[EMAIL SENT] {message}")
    except Exception as e:
        # Never let a notification failure crash the pipeline -- log it
        # and fall back to the safe logging path.
        logger.error(f"Email notification failed ({e}). Falling back to log-only. {message}")


def _send_email(email_cfg: dict, subject: str, body: str):
    """Real SMTP send. Only called when channel='email' and dry_run=false."""
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_cfg["sender_address"]
    msg["To"] = ", ".join(email_cfg["recipient_addresses"])

    with smtplib.SMTP(email_cfg["smtp_host"], email_cfg["smtp_port"]) as server:
        server.starttls()
        server.login(email_cfg["sender_address"], email_cfg["sender_password"])
        server.sendmail(email_cfg["sender_address"], email_cfg["recipient_addresses"], msg.as_string())


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
