"""
main.py -- FastAPI service (V2)
---------------------------------
Exposes the trained models as a real web API, independent of the
Streamlit dashboard. This is what you'd actually deploy behind a domain
later -- the dashboard can call this API instead of loading models
directly, and so could a mobile app, another dashboard, or a college
IT system.

RUN LOCALLY WITH:
    uvicorn api.main:app --reload

Then visit http://127.0.0.1:8000/docs for interactive Swagger docs
(FastAPI generates this automatically).
"""

import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config_loader import load_config
from logging_setup import get_logger
from explainability import explain_reading
from alerts import check_and_alert

logger = get_logger("api")
cfg = load_config()

app = FastAPI(
    title="Classroom Air Quality & Infection Risk API",
    description="Software-only IAQ + infection risk prediction service (V2)",
    version="2.0.0",
)


class SensorReading(BaseModel):
    room_id: str = Field(..., example="Room_1")
    co2_ppm: float = Field(..., example=2500)
    temperature_c: float = Field(..., example=26.5)
    humidity_pct: float = Field(..., example=55.0)
    occupancy: int = Field(..., example=45)


class PredictionResponse(BaseModel):
    room_id: str
    risk_category: str
    contributions: dict
    root_cause: str
    alert_fired: bool


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/predict", response_model=PredictionResponse)
def predict(reading: SensorReading):
    try:
        result = explain_reading(
            co2_ppm=reading.co2_ppm,
            temperature_c=reading.temperature_c,
            humidity_pct=reading.humidity_pct,
            occupancy=reading.occupancy,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Model not trained yet. Run src/train_and_compare.py first.",
        )

    fired = check_and_alert(
        room_id=reading.room_id,
        risk_category=result["prediction"],
        timestamp=datetime.now(),
        root_cause=result["root_cause"],
    )

    logger.info(f"Prediction for {reading.room_id}: {result['prediction']} (alert_fired={fired})")

    return PredictionResponse(
        room_id=reading.room_id,
        risk_category=result["prediction"],
        contributions=result["contributions"],
        root_cause=result["root_cause"],
        alert_fired=fired,
    )
