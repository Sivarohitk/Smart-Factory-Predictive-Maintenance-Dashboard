from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import check_database_connection, get_db
from app.ml.runtime import OnnxInferenceRuntime
from app.schemas.alert import AlertRead
from app.schemas.health import HealthResponse
from app.schemas.machine import MachineRead
from app.schemas.prediction import (
    PredictionRead,
    PredictionResultRead,
    SensorReadingBatchResponse,
)
from app.schemas.sensor_reading import (
    SensorReadingBatchCreate,
    SensorReadingCreate,
    SensorReadingRead,
)
from app.services.ingestion_service import IngestionResult, ingest_and_predict
from app.services.machine_service import list_machines
from app.services.prediction_service import list_predictions
from app.services.query_service import list_alerts

router = APIRouter()


def get_runtime(request: Request) -> OnnxInferenceRuntime:
    runtime = getattr(request.app.state, "model_runtime", None)
    if runtime is None:
        raise HTTPException(status_code=503, detail="Model runtime is not available.")
    return runtime


def get_app_settings(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        return get_settings()
    return settings


def serialize_sensor_reading(result: IngestionResult) -> SensorReadingRead:
    reading = result.sensor_reading
    return SensorReadingRead(
        id=reading.id,
        machine_id=result.machine.id,
        machine_code=result.machine.machine_code,
        captured_at=reading.captured_at,
        source_udi=reading.source_udi,
        product_id=reading.product_id,
        product_type=reading.product_type,
        air_temperature_k=float(reading.air_temperature_k),
        process_temperature_k=float(reading.process_temperature_k),
        rotational_speed_rpm=float(reading.rotational_speed_rpm),
        torque_nm=float(reading.torque_nm),
        tool_wear_min=float(reading.tool_wear_min),
    )


def serialize_prediction(result: IngestionResult) -> PredictionRead:
    prediction = result.prediction
    return PredictionRead(
        id=prediction.id,
        machine_id=result.machine.id,
        machine_code=result.machine.machine_code,
        sensor_reading_id=prediction.sensor_reading_id,
        model_name=prediction.model_name,
        failure_probability=prediction.failure_probability,
        threshold_used=prediction.threshold_used,
        predicted_failure=prediction.predicted_failure,
        risk_level=prediction.risk_level,
        created_at=prediction.created_at,
    )


def serialize_prediction_row(prediction) -> PredictionRead:
    return PredictionRead(
        id=prediction.id,
        machine_id=prediction.machine_id,
        machine_code=prediction.machine.machine_code,
        sensor_reading_id=prediction.sensor_reading_id,
        model_name=prediction.model_name,
        failure_probability=prediction.failure_probability,
        threshold_used=prediction.threshold_used,
        predicted_failure=prediction.predicted_failure,
        risk_level=prediction.risk_level,
        created_at=prediction.created_at,
    )


def serialize_alert_row(alert) -> AlertRead:
    return AlertRead(
        id=alert.id,
        machine_id=alert.machine_id,
        machine_code=alert.machine.machine_code,
        prediction_id=alert.prediction_id,
        severity=alert.severity,
        status=alert.status,
        message=alert.message,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
    )


@router.get("/", tags=["meta"], summary="Backend service metadata")
def root(settings: Annotated[Settings, Depends(get_app_settings)]) -> dict[str, str]:
    return {
        "app": settings.app_name,
        "status": "ready",
        "message": "Predictive maintenance backend is available."
    }


@router.get("/health", response_model=HealthResponse, tags=["meta"], summary="Backend health")
def health(
    runtime: Annotated[OnnxInferenceRuntime, Depends(get_runtime)],
) -> HealthResponse:
    database_connected = check_database_connection()
    status = "ok" if database_connected else "degraded"
    return HealthResponse(
        status=status,
        service="backend",
        database_connected=database_connected,
        model_loaded=True,
        model_name=runtime.model_name,
        decision_threshold=runtime.decision_threshold,
    )


@router.post(
    "/predict",
    response_model=PredictionResultRead,
    status_code=201,
    tags=["predictions"],
    summary="Ingest one sensor reading and store a prediction",
)
def predict(
    payload: SensorReadingCreate,
    db: Annotated[Session, Depends(get_db)],
    runtime: Annotated[OnnxInferenceRuntime, Depends(get_runtime)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> PredictionResultRead:
    alert_threshold = settings.alert_probability_threshold or runtime.decision_threshold
    result = ingest_and_predict(db, runtime, payload, alert_threshold=alert_threshold)
    db.commit()
    return PredictionResultRead(
        sensor_reading=serialize_sensor_reading(result),
        prediction=serialize_prediction(result),
        alert_id=result.alert.id if result.alert else None,
    )


@router.post(
    "/sensor-readings/batch",
    response_model=SensorReadingBatchResponse,
    status_code=201,
    tags=["sensor-readings"],
    summary="Ingest a batch of sensor readings and store predictions",
)
def ingest_sensor_readings_batch(
    payload: SensorReadingBatchCreate,
    db: Annotated[Session, Depends(get_db)],
    runtime: Annotated[OnnxInferenceRuntime, Depends(get_runtime)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> SensorReadingBatchResponse:
    alert_threshold = settings.alert_probability_threshold or runtime.decision_threshold
    results: list[PredictionResultRead] = []
    created_alerts = 0

    for record in payload.records:
        result = ingest_and_predict(db, runtime, record, alert_threshold=alert_threshold)
        if result.alert is not None:
            created_alerts += 1
        results.append(
            PredictionResultRead(
                sensor_reading=serialize_sensor_reading(result),
                prediction=serialize_prediction(result),
                alert_id=result.alert.id if result.alert else None,
            )
        )

    db.commit()
    return SensorReadingBatchResponse(
        processed_records=len(payload.records),
        created_predictions=len(results),
        created_alerts=created_alerts,
        results=results,
    )


@router.get(
    "/machines",
    response_model=list[MachineRead],
    tags=["machines"],
    summary="List machines",
)
def get_machines(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[MachineRead]:
    machines = list_machines(db, limit=limit)
    return [MachineRead.model_validate(machine) for machine in machines]


@router.get(
    "/predictions",
    response_model=list[PredictionRead],
    tags=["predictions"],
    summary="List stored predictions",
)
def get_predictions(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[PredictionRead]:
    predictions = list_predictions(db, limit=limit)
    return [serialize_prediction_row(prediction) for prediction in predictions]


@router.get(
    "/alerts",
    response_model=list[AlertRead],
    tags=["alerts"],
    summary="List alerts",
)
def get_alerts(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AlertRead]:
    alerts = list_alerts(db, limit=limit)
    return [serialize_alert_row(alert) for alert in alerts]
