# API Documentation

Base URL in local development:

- Backend: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`

The frontend currently integrates with the list endpoints plus batch ingestion. The simulator also uses the batch ingestion endpoint.

## Endpoint Summary

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Simple backend metadata response |
| `GET` | `/health` | Service health, DB connectivity, model name, decision threshold |
| `POST` | `/predict` | Ingest one sensor record and store the prediction |
| `POST` | `/sensor-readings/batch` | Ingest a batch of sensor records and store predictions |
| `GET` | `/machines` | List stored machines |
| `GET` | `/predictions` | List stored predictions |
| `GET` | `/alerts` | List stored alerts |

## Common Request Fields

The ingestion endpoints use the same sensor payload shape:

```json
{
  "machine_code": "MILL-001",
  "machine_name": "Mill 001",
  "line_name": "Line A",
  "asset_type": "Milling Machine",
  "machine_status": "active",
  "source_udi": 70,
  "product_id": "L47249",
  "product_type": "L",
  "captured_at": "2026-03-22T16:00:00Z",
  "air_temperature_k": 298.9,
  "process_temperature_k": 309.0,
  "rotational_speed_rpm": 1410.0,
  "torque_nm": 65.7,
  "tool_wear_min": 191.0
}
```

Notes:

- `product_type` must be one of `L`, `M`, or `H`
- `machine_status` must be one of `active`, `maintenance`, or `offline`
- the backend stores metadata fields but only passes the sensor/model fields into ONNX Runtime

## `GET /`

Returns a simple metadata response.

Example response:

```json
{
  "app": "Smart Factory Predictive Maintenance Dashboard",
  "status": "ready",
  "message": "Predictive maintenance backend is available."
}
```

## `GET /health`

Returns backend health and model metadata.

Example response:

```json
{
  "status": "ok",
  "service": "backend",
  "database_connected": true,
  "model_loaded": true,
  "model_name": "smart_factory_failure_model",
  "decision_threshold": 0.5382328037713715
}
```

## `POST /predict`

Stores one sensor reading, runs ONNX inference, stores one prediction, and optionally creates one alert.

Example request:

```json
{
  "machine_code": "MILL-001",
  "machine_name": "Mill 001",
  "line_name": "Line A",
  "asset_type": "Milling Machine",
  "machine_status": "active",
  "source_udi": 70,
  "product_id": "L47249",
  "product_type": "L",
  "captured_at": "2026-03-22T16:00:00Z",
  "air_temperature_k": 298.9,
  "process_temperature_k": 309.0,
  "rotational_speed_rpm": 1410.0,
  "torque_nm": 65.7,
  "tool_wear_min": 191.0
}
```

Example response:

```json
{
  "sensor_reading": {
    "id": 1,
    "machine_id": 1,
    "machine_code": "MILL-001",
    "captured_at": "2026-03-22T16:00:00Z",
    "source_udi": 70,
    "product_id": "L47249",
    "product_type": "L",
    "air_temperature_k": 298.9,
    "process_temperature_k": 309.0,
    "rotational_speed_rpm": 1410.0,
    "torque_nm": 65.7,
    "tool_wear_min": 191.0
  },
  "prediction": {
    "id": 1,
    "machine_id": 1,
    "machine_code": "MILL-001",
    "sensor_reading_id": 1,
    "model_name": "smart_factory_failure_model",
    "failure_probability": 0.8723042011260986,
    "threshold_used": 0.5382328037713715,
    "predicted_failure": true,
    "risk_level": "critical",
    "created_at": "2026-03-22T16:00:01Z"
  },
  "alert_id": 1
}
```

## `POST /sensor-readings/batch`

Primary live ingestion endpoint for the frontend and simulator. Each record is validated, stored, scored, and optionally converted into an alert.

Example request:

```json
{
  "records": [
    {
      "machine_code": "MILL-001",
      "machine_name": "Mill 001",
      "line_name": "Line A",
      "asset_type": "Milling Machine",
      "machine_status": "active",
      "source_udi": 70,
      "product_id": "L47249",
      "product_type": "L",
      "captured_at": "2026-03-22T16:00:00Z",
      "air_temperature_k": 298.9,
      "process_temperature_k": 309.0,
      "rotational_speed_rpm": 1410.0,
      "torque_nm": 65.7,
      "tool_wear_min": 191.0
    },
    {
      "machine_code": "LATHE-002",
      "machine_name": "Lathe 002",
      "line_name": "Line A",
      "asset_type": "CNC Lathe",
      "machine_status": "active",
      "source_udi": 1,
      "product_id": "M14860",
      "product_type": "M",
      "captured_at": "2026-03-22T16:05:00Z",
      "air_temperature_k": 298.1,
      "process_temperature_k": 308.6,
      "rotational_speed_rpm": 1551.0,
      "torque_nm": 42.8,
      "tool_wear_min": 0.0
    }
  ]
}
```

Example response:

```json
{
  "processed_records": 2,
  "created_predictions": 2,
  "created_alerts": 1,
  "results": [
    {
      "sensor_reading": {
        "id": 1,
        "machine_id": 1,
        "machine_code": "MILL-001",
        "captured_at": "2026-03-22T16:00:00Z",
        "source_udi": 70,
        "product_id": "L47249",
        "product_type": "L",
        "air_temperature_k": 298.9,
        "process_temperature_k": 309.0,
        "rotational_speed_rpm": 1410.0,
        "torque_nm": 65.7,
        "tool_wear_min": 191.0
      },
      "prediction": {
        "id": 1,
        "machine_id": 1,
        "machine_code": "MILL-001",
        "sensor_reading_id": 1,
        "model_name": "smart_factory_failure_model",
        "failure_probability": 0.8723042011260986,
        "threshold_used": 0.5382328037713715,
        "predicted_failure": true,
        "risk_level": "critical",
        "created_at": "2026-03-22T16:00:01Z"
      },
      "alert_id": 1
    },
    {
      "sensor_reading": {
        "id": 2,
        "machine_id": 2,
        "machine_code": "LATHE-002",
        "captured_at": "2026-03-22T16:05:00Z",
        "source_udi": 1,
        "product_id": "M14860",
        "product_type": "M",
        "air_temperature_k": 298.1,
        "process_temperature_k": 308.6,
        "rotational_speed_rpm": 1551.0,
        "torque_nm": 42.8,
        "tool_wear_min": 0.0
      },
      "prediction": {
        "id": 2,
        "machine_id": 2,
        "machine_code": "LATHE-002",
        "sensor_reading_id": 2,
        "model_name": "smart_factory_failure_model",
        "failure_probability": 0.0002222681068815291,
        "threshold_used": 0.5382328037713715,
        "predicted_failure": false,
        "risk_level": "low",
        "created_at": "2026-03-22T16:05:01Z"
      },
      "alert_id": null
    }
  ]
}
```

## `GET /machines`

Lists stored machines. Supports `?limit=<n>`.

Example response:

```json
[
  {
    "id": 1,
    "machine_code": "MILL-001",
    "machine_name": "Mill 001",
    "line_name": "Line A",
    "asset_type": "Milling Machine",
    "status": "active",
    "created_at": "2026-03-22T16:00:00Z"
  }
]
```

## `GET /predictions`

Lists stored predictions sorted newest first. Supports `?limit=<n>`.

Example response:

```json
[
  {
    "id": 2,
    "machine_id": 2,
    "machine_code": "LATHE-002",
    "sensor_reading_id": 2,
    "model_name": "smart_factory_failure_model",
    "failure_probability": 0.0002222681068815291,
    "threshold_used": 0.5382328037713715,
    "predicted_failure": false,
    "risk_level": "low",
    "created_at": "2026-03-22T16:05:01Z"
  },
  {
    "id": 1,
    "machine_id": 1,
    "machine_code": "MILL-001",
    "sensor_reading_id": 1,
    "model_name": "smart_factory_failure_model",
    "failure_probability": 0.8723042011260986,
    "threshold_used": 0.5382328037713715,
    "predicted_failure": true,
    "risk_level": "critical",
    "created_at": "2026-03-22T16:00:01Z"
  }
]
```

## `GET /alerts`

Lists stored alerts sorted newest first. Supports `?limit=<n>`.

Example response:

```json
[
  {
    "id": 1,
    "machine_id": 1,
    "machine_code": "MILL-001",
    "prediction_id": 1,
    "severity": "critical",
    "status": "open",
    "message": "Machine MILL-001 exceeded the failure-risk alert threshold with probability 87.23%.",
    "created_at": "2026-03-22T16:00:01Z",
    "acknowledged_at": null
  }
]
```

## Live Flow Notes

- `POST /sensor-readings/batch` is the main path used by the frontend ingestion panel and `scripts/simulate_sensor_stream.py`
- the frontend refreshes `GET /machines`, `GET /predictions`, and `GET /alerts` after a successful batch ingest
- the dashboard filters high-risk alerts client-side for the alert panel, but `GET /alerts` itself returns all stored alerts

## Alert Generation Notes

- the backend creates an alert when `failure_probability >= alert_threshold`
- `alert_threshold` comes from `ALERT_PROBABILITY_THRESHOLD` if configured, otherwise it falls back to the model decision threshold from `model_metadata.json`
- risk level and alert severity are based on the probability bands used in the backend service layer:
  - `critical` for `>= 0.85`
  - `high` for `>= 0.70`
  - `medium` for `>= model decision threshold`
  - `low` otherwise

## Validation Notes

If request validation fails, FastAPI returns a `422` with a structured `detail` array. The frontend client flattens those validation messages into a readable error string for the UI.
