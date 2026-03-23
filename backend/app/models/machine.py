from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Machine(TimestampMixin, Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    machine_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    line_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    asset_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    sensor_readings = relationship(
        "SensorReading",
        back_populates="machine",
        cascade="all, delete-orphan",
    )
    predictions = relationship(
        "Prediction",
        back_populates="machine",
        cascade="all, delete-orphan",
    )
    alerts = relationship(
        "Alert",
        back_populates="machine",
        cascade="all, delete-orphan",
    )
