from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Machine
from app.schemas.sensor_reading import SensorReadingCreate


def get_or_create_machine(session: Session, payload: SensorReadingCreate) -> tuple[Machine, bool]:
    machine = session.scalar(select(Machine).where(Machine.machine_code == payload.machine_code))
    created = False

    if machine is None:
        machine = Machine(
            machine_code=payload.machine_code,
            machine_name=payload.machine_name,
            line_name=payload.line_name,
            asset_type=payload.asset_type,
            status=payload.machine_status.value,
        )
        session.add(machine)
        session.flush()
        created = True
    else:
        if payload.machine_name:
            machine.machine_name = payload.machine_name
        if payload.line_name:
            machine.line_name = payload.line_name
        if payload.asset_type:
            machine.asset_type = payload.asset_type
        if payload.machine_status:
            machine.status = payload.machine_status.value
        session.flush()

    return machine, created


def list_machines(session: Session, limit: int) -> list[Machine]:
    statement = select(Machine).order_by(Machine.created_at.desc(), Machine.id.desc()).limit(limit)
    return list(session.scalars(statement).all())
