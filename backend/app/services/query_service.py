from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Alert


def list_alerts(session: Session, limit: int) -> list[Alert]:
    statement = (
        select(Alert)
        .options(selectinload(Alert.machine), selectinload(Alert.prediction))
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(limit)
    )
    return list(session.scalars(statement).all())
