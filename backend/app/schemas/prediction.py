from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import RiskLevel
from app.schemas.sensor_reading import SensorReadingRead


class PredictionRead(BaseModel):
    id: int
    machine_id: int
    machine_code: str
    sensor_reading_id: int
    model_name: str
    failure_probability: float
    threshold_used: float
    predicted_failure: bool
    risk_level: RiskLevel
    created_at: datetime


class PredictionResultRead(BaseModel):
    sensor_reading: SensorReadingRead
    prediction: PredictionRead
    alert_id: int | None = None


class SensorReadingBatchResponse(BaseModel):
    processed_records: int
    created_predictions: int
    created_alerts: int
    results: list[PredictionResultRead]
