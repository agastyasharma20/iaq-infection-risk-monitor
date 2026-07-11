"""
main.py -- FastAPI service (V3)
---------------------------------
V3 additions on top of V2's /predict and /health:
  - API key authentication (all endpoints except /health require it)
  - /simulate     : Digital Twin what-if simulation
  - /recommend    : RL ventilation advisor recommendation
  - /check_anomaly: sensor anomaly detection
  - /alerts       : recent alert history (from the database)
  - /model_history: model registry / versioning history

RUN LOCALLY WITH:
    uvicorn api.main:app --reload

Then visit http://127.0.0.1:8000/docs for interactive Swagger docs.
Include header `X-API-Key: <your key from config.yaml>` on every request
except /health.
"""

import os
import sys
from datetime import datetime
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from config_loader import load_config
from logging_setup import get_logger
from explainability import explain_reading
from alerts import check_and_alert
from digital_twin import simulate, compare_all_actions, ACTIONS
from rl_advisor import recommend_action
from anomaly_detection import check_reading_for_anomaly
from db import get_all_alerts, get_model_history, get_building_health_history
from orchestrator import process_reading
from building_health import compute_building_health
from graph_propagation import propagate_risk, find_escalation_risks

logger = get_logger("api")
cfg = load_config()

app = FastAPI(
    title="Classroom Air Quality & Infection Risk API",
    description="Software-only IAQ + infection risk prediction, forecasting, "
                "simulation, and autonomous decision-support service (V4)",
    version="4.0.0",
)


def require_api_key(x_api_key: Optional[str] = Header(None)):
    expected = cfg["api"]["api_key"]
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")
    return True


# ---------------- Schemas ----------------

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
    anomaly_detected: bool


class SimulateRequest(BaseModel):
    co2_ppm: float = Field(..., example=2800)
    occupancy: int = Field(..., example=50)
    action: str = Field(..., example="open_windows", description=f"One of {ACTIONS}")
    minutes_ahead: int = Field(60, example=60)


class BuildingHealthRequest(BaseModel):
    room_predictions: dict = Field(..., example={"Room_1": "Low", "Room_2": "High"})


# ---------------- Endpoints ----------------

@app.get("/health")
def health():
    return {"status": "ok", "version": "4.0.0"}


@app.get("/public/status")
def public_status():
    """
    Deliberately NOT behind the API key -- this is the one endpoint meant
    to be shown to external stakeholders (a public Smart City dashboard,
    a status page linked from a college website) without exposing any
    sensitive room-level detail, alert history, or model internals.
    Returns only the single aggregate Building Health Score.
    """
    history = get_building_health_history(limit=1)
    if not history:
        return {"status": "no_data", "message": "No building health data logged yet."}

    latest = history[-1]
    return {
        "building_health_score": latest.score,
        "grade": latest.grade,
        "rooms_needing_attention": latest.rooms_at_risk,
        "total_rooms": latest.total_rooms,
        "last_updated": latest.timestamp.isoformat(),
    }


@app.post("/analyze", dependencies=[Depends(require_api_key)])
def analyze_endpoint(reading: SensorReading):
    """
    THE V4 USP ENDPOINT: one call runs the full autonomous pipeline --
    anomaly check, risk classification + explanation, Digital Twin
    simulation, RL recommendation, plain-English advisory, and alerting
    -- and returns everything in one response. This is what a real
    integration (a facilities dashboard, a mobile app, a Smart City
    system) would actually call, instead of orchestrating 5 separate
    endpoints itself.
    """
    result = process_reading(
        room_id=reading.room_id, co2_ppm=reading.co2_ppm,
        temperature_c=reading.temperature_c, humidity_pct=reading.humidity_pct,
        occupancy=reading.occupancy,
    )
    return result


@app.post("/building_health", dependencies=[Depends(require_api_key)])
def building_health_endpoint(req: BuildingHealthRequest):
    return compute_building_health(req.room_predictions)


@app.post("/building_graph", dependencies=[Depends(require_api_key)])
def building_graph_endpoint(req: BuildingHealthRequest):
    """
    Cross-room risk propagation (V5): given each room's independently
    predicted risk, returns each room's neighbor-adjusted risk plus a
    list of rooms whose risk is escalated by a risky neighbor -- signal
    a per-room-only model can't see.
    """
    result = propagate_risk(req.room_predictions)
    escalations = find_escalation_risks(result)
    return {"per_room": result, "escalations": escalations}


@app.post("/predict", response_model=PredictionResponse, dependencies=[Depends(require_api_key)])
def predict(reading: SensorReading):
    try:
        result = explain_reading(
            co2_ppm=reading.co2_ppm, temperature_c=reading.temperature_c,
            humidity_pct=reading.humidity_pct, occupancy=reading.occupancy,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not trained yet. Run src/train_and_compare.py first.")

    anomaly = check_reading_for_anomaly(
        room_id=reading.room_id, co2_ppm=reading.co2_ppm, temperature_c=reading.temperature_c,
        humidity_pct=reading.humidity_pct, occupancy=reading.occupancy,
    )

    fired = check_and_alert(
        room_id=reading.room_id, risk_category=result["prediction"],
        timestamp=datetime.now(), root_cause=result["root_cause"],
    )

    logger.info(f"Prediction for {reading.room_id}: {result['prediction']} "
                f"(alert_fired={fired}, anomaly={anomaly})")

    return PredictionResponse(
        room_id=reading.room_id, risk_category=result["prediction"],
        contributions=result["contributions"], root_cause=result["root_cause"],
        alert_fired=fired, anomaly_detected=anomaly,
    )


@app.post("/simulate", dependencies=[Depends(require_api_key)])
def simulate_endpoint(req: SimulateRequest):
    try:
        df = simulate(req.co2_ppm, req.occupancy, action=req.action, minutes_ahead=req.minutes_ahead)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return df.to_dict(orient="records")


@app.post("/simulate/compare_all", dependencies=[Depends(require_api_key)])
def simulate_compare_endpoint(co2_ppm: float, occupancy: int, minutes_ahead: int = 60):
    results = compare_all_actions(co2_ppm, occupancy, minutes_ahead)
    return {action: df.to_dict(orient="records") for action, df in results.items()}


@app.get("/recommend", dependencies=[Depends(require_api_key)])
def recommend_endpoint(co2_ppm: float, occupancy: int):
    try:
        return recommend_action(co2_ppm, occupancy)
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="RL advisor not trained yet. Run src/rl_advisor.py first.")


@app.get("/alerts", dependencies=[Depends(require_api_key)])
def alerts_endpoint(limit: int = 50):
    alerts = get_all_alerts()[:limit]
    return [
        {"timestamp": a.timestamp.isoformat(), "room_id": a.room_id,
         "risk_category": a.risk_category, "root_cause": a.root_cause}
        for a in alerts
    ]


@app.get("/model_history", dependencies=[Depends(require_api_key)])
def model_history_endpoint(model_name: Optional[str] = None):
    history = get_model_history(model_name)
    return [
        {"trained_at": m.trained_at.isoformat(), "model_name": m.model_name,
         "accuracy": m.accuracy, "is_champion": m.is_champion, "notes": m.notes}
        for m in history
    ]
