from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Alert, Machine, Prediction, SensorReading
from app.ml.runtime import InferenceResult, OnnxInferenceRuntime
from app.schemas.sensor_reading import SensorReadingCreate
from app.services.alert_service import build_alert, derive_risk_level
from app.services.machine_service import get_or_create_machine


@dataclass
class IngestionResult:
    machine: Machine
    machine_created: bool
    sensor_reading: SensorReading
    prediction: Prediction
    alert: Alert | None
    inference: InferenceResult


def ingest_and_predict(
    session: Session,
    runtime: OnnxInferenceRuntime,
    payload: SensorReadingCreate,
    alert_threshold: float,
) -> IngestionResult:
    machine, machine_created = get_or_create_machine(session, payload)

    sensor_reading = SensorReading(
        machine_id=machine.id,
        source_udi=payload.source_udi,
        product_id=payload.product_id,
        product_type=payload.product_type.value,
        captured_at=payload.captured_at,
        air_temperature_k=payload.air_temperature_k,
        process_temperature_k=payload.process_temperature_k,
        rotational_speed_rpm=payload.rotational_speed_rpm,
        torque_nm=payload.torque_nm,
        tool_wear_min=payload.tool_wear_min,
    )
    session.add(sensor_reading)
    session.flush()

    inference = runtime.predict(
        {
            "product_type": payload.product_type.value,
            "air_temperature_k": payload.air_temperature_k,
            "process_temperature_k": payload.process_temperature_k,
            "rotational_speed_rpm": payload.rotational_speed_rpm,
            "torque_nm": payload.torque_nm,
            "tool_wear_min": payload.tool_wear_min,
        }
    )

    prediction = Prediction(
        machine_id=machine.id,
        sensor_reading_id=sensor_reading.id,
        model_name=runtime.model_name,
        failure_probability=inference.failure_probability,
        threshold_used=inference.decision_threshold,
        predicted_failure=inference.predicted_failure,
        risk_level=derive_risk_level(
            inference.failure_probability,
            inference.decision_threshold,
        ).value,
    )
    session.add(prediction)
    session.flush()

    alert = build_alert(
        machine=machine,
        prediction=prediction,
        probability=inference.failure_probability,
        alert_threshold=alert_threshold,
        decision_threshold=inference.decision_threshold,
    )
    if alert is not None:
        session.add(alert)
        session.flush()

    return IngestionResult(
        machine=machine,
        machine_created=machine_created,
        sensor_reading=sensor_reading,
        prediction=prediction,
        alert=alert,
        inference=inference,
    )
