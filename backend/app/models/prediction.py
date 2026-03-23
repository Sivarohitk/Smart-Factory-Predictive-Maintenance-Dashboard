from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Prediction(TimestampMixin, Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"), index=True)
    sensor_reading_id: Mapped[int] = mapped_column(
        ForeignKey("sensor_readings.id"),
        unique=True,
        index=True,
    )
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_used: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_failure: Mapped[bool] = mapped_column(Boolean, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)

    machine = relationship("Machine", back_populates="predictions")
    sensor_reading = relationship("SensorReading", back_populates="prediction")
    alert = relationship("Alert", back_populates="prediction", uselist=False)
