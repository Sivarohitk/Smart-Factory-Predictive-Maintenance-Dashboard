from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import MachineStatus, ORMModel


class MachineRead(ORMModel):
    id: int
    machine_code: str
    machine_name: str | None = None
    line_name: str | None = None
    asset_type: str | None = None
    status: MachineStatus
    created_at: datetime


class MachinePayload(ORMModel):
    machine_code: str = Field(min_length=1, max_length=64)
    machine_name: str | None = Field(default=None, max_length=120)
    line_name: str | None = Field(default=None, max_length=120)
    asset_type: str | None = Field(default=None, max_length=120)
    status: MachineStatus = MachineStatus.active
