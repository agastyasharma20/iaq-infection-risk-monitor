"""
db.py -- Persistence Layer (V3)
----------------------------------
V1/V2 used flat CSV files for alerts. V3 replaces that with a real SQLite
database (via SQLAlchemy), giving you:
  - Proper querying (e.g. "all High alerts for Room_3 in the last week")
  - A model registry table (tracks every trained model version + its
    accuracy, so you can see improvement over time and know which
    model is currently "champion")
  - A foundation that scales to Postgres/MySQL later just by changing
    the connection string -- no other code changes needed.

SQLite file lives at data/iaq.db (gitignored, like all generated data).
"""

import os
import sys
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Boolean
)
from sqlalchemy.orm import declarative_base, sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config_loader import load_config, resolve_path

Base = declarative_base()


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    room_id = Column(String, nullable=False)
    risk_category = Column(String, nullable=False)
    root_cause = Column(String, default="")


class ModelRegistry(Base):
    __tablename__ = "model_registry"
    id = Column(Integer, primary_key=True, autoincrement=True)
    trained_at = Column(DateTime, nullable=False)
    model_name = Column(String, nullable=False)      # e.g. "Fuzzy Decision Tree"
    accuracy = Column(Float, nullable=False)
    is_champion = Column(Boolean, default=False)
    notes = Column(String, default="")


class SensorAnomaly(Base):
    __tablename__ = "sensor_anomalies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    room_id = Column(String, nullable=False)
    reason = Column(String, default="")


def get_engine():
    cfg = load_config()
    db_path = resolve_path(cfg["paths"]["data_dir"], "iaq.db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


# ---------------- Convenience functions used by other modules ----------------

def log_alert(room_id: str, risk_category: str, timestamp: datetime, root_cause: str = ""):
    session = get_session()
    try:
        session.add(Alert(timestamp=timestamp, room_id=room_id,
                           risk_category=risk_category, root_cause=root_cause))
        session.commit()
    finally:
        session.close()


def get_recent_alert(room_id: str):
    """Returns the most recent Alert row for a room, or None."""
    session = get_session()
    try:
        return (session.query(Alert)
                .filter(Alert.room_id == room_id)
                .order_by(Alert.timestamp.desc())
                .first())
    finally:
        session.close()


def get_all_alerts():
    session = get_session()
    try:
        return session.query(Alert).order_by(Alert.timestamp.desc()).all()
    finally:
        session.close()


def register_model(model_name: str, accuracy: float, notes: str = ""):
    """
    Logs a newly trained model's accuracy. If it beats the current
    champion for that model_name, promotes it (simple champion/challenger
    MLOps pattern).
    """
    session = get_session()
    try:
        current_champion = (session.query(ModelRegistry)
                             .filter(ModelRegistry.model_name == model_name,
                                     ModelRegistry.is_champion == True)  # noqa: E712
                             .first())

        promote = current_champion is None or accuracy > current_champion.accuracy

        if promote and current_champion is not None:
            current_champion.is_champion = False

        entry = ModelRegistry(
            trained_at=datetime.now(), model_name=model_name,
            accuracy=accuracy, is_champion=promote, notes=notes,
        )
        session.add(entry)
        session.commit()
        return promote
    finally:
        session.close()


def get_model_history(model_name: str = None):
    session = get_session()
    try:
        q = session.query(ModelRegistry)
        if model_name:
            q = q.filter(ModelRegistry.model_name == model_name)
        return q.order_by(ModelRegistry.trained_at.desc()).all()
    finally:
        session.close()


def log_anomaly(room_id: str, timestamp: datetime, reason: str):
    session = get_session()
    try:
        session.add(SensorAnomaly(timestamp=timestamp, room_id=room_id, reason=reason))
        session.commit()
    finally:
        session.close()


def get_all_anomalies():
    session = get_session()
    try:
        return session.query(SensorAnomaly).order_by(SensorAnomaly.timestamp.desc()).all()
    finally:
        session.close()


if __name__ == "__main__":
    # Quick sanity check
    promoted = register_model("Fuzzy Decision Tree", 0.9926, notes="V3 test run")
    print("Promoted to champion:", promoted)
    log_alert("Room_1", "High", datetime.now(), "Overcrowding")
    print("Alerts in DB:", len(get_all_alerts()))
    print("Model history:", [(m.model_name, m.accuracy, m.is_champion) for m in get_model_history()])
