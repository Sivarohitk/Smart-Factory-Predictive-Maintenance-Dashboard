from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Alert(TimestampMixin, Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True)
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("predictions.id"),
        unique=True,
        index=True,
    )
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    machine = relationship("Machine", back_populates="alerts")
    prediction = relationship("Prediction", back_populates="alert")
