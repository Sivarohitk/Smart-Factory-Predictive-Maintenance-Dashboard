from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Prediction


def list_predictions(session: Session, limit: int) -> list[Prediction]:
    statement = (
        select(Prediction)
        .options(selectinload(Prediction.machine), selectinload(Prediction.sensor_reading))
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .limit(limit)
    )
    return list(session.scalars(statement).all())
