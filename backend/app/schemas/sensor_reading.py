from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.schemas.common import MachineStatus, ProductType


class SensorReadingCreate(BaseModel):
    machine_code: str = Field(min_length=1, max_length=64)
    machine_name: str | None = Field(default=None, max_length=120)
    line_name: str | None = Field(default=None, max_length=120)
    asset_type: str | None = Field(default=None, max_length=120)
    machine_status: MachineStatus = MachineStatus.active
    source_udi: int | None = None
    product_id: str | None = Field(default=None, max_length=64)
    product_type: ProductType
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    air_temperature_k: float = Field(gt=0)
    process_temperature_k: float = Field(gt=0)
    rotational_speed_rpm: float = Field(gt=0)
    torque_nm: float = Field(ge=0)
    tool_wear_min: float = Field(ge=0)


class SensorReadingBatchCreate(BaseModel):
    records: list[SensorReadingCreate] = Field(min_length=1, max_length=500)


class SensorReadingRead(BaseModel):
    id: int
    machine_id: int
    machine_code: str
    captured_at: datetime
    source_udi: int | None = None
    product_id: str | None = None
    product_type: ProductType
    air_temperature_k: float
    process_temperature_k: float
    rotational_speed_rpm: float
    torque_nm: float
    tool_wear_min: float
