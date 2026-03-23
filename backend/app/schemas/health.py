from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    database_connected: bool
    model_loaded: bool
    model_name: str | None = None
    decision_threshold: float | None = None
