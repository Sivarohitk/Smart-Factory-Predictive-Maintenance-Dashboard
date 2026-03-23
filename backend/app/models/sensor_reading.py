from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, utc_now


class SensorReading(TimestampMixin, Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True)
    source_udi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    product_type: Mapped[str] = mapped_column(String(8), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    air_temperature_k: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    process_temperature_k: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    rotational_speed_rpm: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    torque_nm: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    tool_wear_min: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)

    machine = relationship("Machine", back_populates="sensor_readings")
    prediction = relationship(
        "Prediction",
        back_populates="sensor_reading",
        uselist=False,
    )
