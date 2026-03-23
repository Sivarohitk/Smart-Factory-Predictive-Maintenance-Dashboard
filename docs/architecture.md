# Architecture

## System Overview

This project is a monorepo MVP with four core parts:

- `frontend/`: React + Vite dashboard for machine inventory, predictions, alerts, trend view, and sensor ingestion
- `backend/`: FastAPI service for request validation, persistence, ONNX Runtime inference, and API docs
- `ml/`: CLI-only training, preprocessing, evaluation, ONNX export, and ONNX smoke testing
- `infra/`: MySQL schema bootstrap, seed SQL, and Docker Compose infrastructure files

The runtime path is intentionally simple:

- the frontend talks to FastAPI over REST
- FastAPI stores application data in MySQL for the main runtime path
- FastAPI loads the exported ONNX model and metadata from `ml/artifacts/`
- SQLite remains available for local development and automated tests

## Runtime Diagram

```text
React + Vite UI
      |
      v
FastAPI REST API
      |
      +--> SQLAlchemy ORM --> MySQL or SQLite
      |
      +--> ONNX Runtime --> failure_model.onnx
                            model_metadata.json
                            preprocessing_config.json
```

## Monorepo Structure

```text
frontend/
  src/
    api/
    components/
    data/
    utils/

backend/
  app/
    api/
    core/
    db/
    ml/
    models/
    schemas/
    services/
  tests/

ml/
  scripts/
  artifacts/
  data/

infra/
  mysql/
  seed/
  docker/

scripts/
  reset_db.py
  generate_demo_data.py
  simulate_sensor_stream.py
```

## Request And Data Flow

### Live Dashboard Flow

1. The frontend requests `/health`, `/machines`, `/predictions`, and `/alerts`.
2. FastAPI queries the database and returns the latest rows.
3. The frontend renders KPI cards, alert cards, the predictions table, a machine list, and a recent trend view.

### Ingestion Flow

1. A user submits a single sensor record from the form, or a batch through the JSON upload panel.
2. The frontend sends the payload to `POST /sensor-readings/batch`.
3. FastAPI validates the request with Pydantic.
4. The backend creates or updates the `machines` row.
5. The backend stores the raw sensor reading in `sensor_readings`.
6. The backend maps the request fields to the ONNX input contract and runs inference with ONNX Runtime.
7. The backend stores the model output in `predictions`.
8. If the probability crosses the configured alert threshold, the backend creates an `alerts` row.
9. The frontend refreshes the list endpoints and shows the new prediction and alert records.

### Demo Flow

1. `scripts/generate_demo_data.py` writes deterministic records directly to the database using the backend service layer.
2. `scripts/simulate_sensor_stream.py` posts deterministic batches to the live HTTP API.
3. Both paths use the same ONNX Runtime inference contract and persistence model.

## Model Input Contract

The backend does not infer feature order heuristically. It reads:

- `ml/artifacts/model_metadata.json`
- `ml/artifacts/preprocessing_config.json`

The explicit feature order is:

1. `type_L`
2. `type_M`
3. `type_H`
4. `air_temperature_k`
5. `process_temperature_k`
6. `rotational_speed_rpm`
7. `torque_nm`
8. `tool_wear_min`

Request payload fields are mapped as follows:

- `product_type` -> one-hot encoded into `type_L`, `type_M`, `type_H`
- numeric sensor inputs map directly to the five numeric features
- metadata fields such as `machine_code`, `machine_name`, `line_name`, `asset_type`, `source_udi`, and `product_id` are stored in the database but are not passed into the model

This keeps training and inference separated while making the runtime contract explicit and reproducible.

## Database Design Summary

The main entities are:

- `machines`
- `sensor_readings`
- `predictions`
- `alerts`

Relationship summary:

- one machine has many sensor readings
- one machine has many predictions
- one machine has many alerts
- one sensor reading has one prediction
- one prediction may have one alert

The canonical schema reference is [database_schema.md](database_schema.md).

## Deployment Modes

### Docker Compose

Primary runtime:

- `db`: MySQL 8
- `backend`: FastAPI + ONNX Runtime
- `frontend`: Vite dev server

### Non-Docker Local Development

Fallback runtime:

- SQLite database
- backend started directly with `uvicorn`
- frontend started directly with `npm run dev`

This local fallback is intended for development convenience. The primary end-to-end demo path is MySQL through Docker Compose.

## Scope Boundaries

This project intentionally does not include:

- authentication and user roles
- background job workers
- Kafka, Redis, or message queues
- Kubernetes or cloud deployment infrastructure
- production-grade observability, rate limiting, or secret management

Those omissions are deliberate to keep the project credible as an MVP rather than a fake enterprise platform.
