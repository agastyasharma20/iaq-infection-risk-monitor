"""
config_loader.py
-----------------
Small utility used by every other module to load config.yaml consistently,
and to resolve paths relative to the project root regardless of which
folder a script is run from.
"""

import os
import yaml

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def load_config(path: str = None) -> dict:
    if path is None:
        path = os.path.join(PROJECT_ROOT, "config.yaml")
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg


def resolve_path(*parts) -> str:
    """Builds an absolute path from the project root, e.g. resolve_path('data', 'sensor_data.csv')."""
    return os.path.join(PROJECT_ROOT, *parts)


def ensure_dirs(cfg: dict):
    for key in ["data_dir", "reports_dir", "logs_dir"]:
        os.makedirs(resolve_path(cfg["paths"][key]), exist_ok=True)
