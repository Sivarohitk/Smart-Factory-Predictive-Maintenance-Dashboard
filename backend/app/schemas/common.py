from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class ProductType(str, Enum):
    L = "L"
    M = "M"
    H = "H"


class MachineStatus(str, Enum):
    active = "active"
    offline = "offline"
    maintenance = "maintenance"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertStatus(str, Enum):
    open = "open"
    acknowledged = "acknowledged"


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
