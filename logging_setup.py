"""
logging_setup.py
-----------------
Consistent logging across the whole project. Logs to both console and a
rotating file under logs/, so you have a persistent record of every
training run, alert, and API request -- useful for your report and for
debugging on a real deployment.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from config_loader import resolve_path, load_config


def get_logger(name: str) -> logging.Logger:
    cfg = load_config()
    log_dir = resolve_path(cfg["paths"]["logs_dir"])
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid duplicate handlers if called multiple times

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "project.log"), maxBytes=1_000_000, backupCount=3
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
