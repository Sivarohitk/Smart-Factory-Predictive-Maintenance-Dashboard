from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AlertStatus, RiskLevel


class AlertRead(BaseModel):
    id: int
    machine_id: int
    machine_code: str
    prediction_id: int
    severity: RiskLevel
    status: AlertStatus
    message: str
    created_at: datetime
    acknowledged_at: datetime | None = None
