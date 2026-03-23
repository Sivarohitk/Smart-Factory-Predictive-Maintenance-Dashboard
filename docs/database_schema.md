# Database Schema

## Overview

The application persists four core entities:

- `machines`
- `sensor_readings`
- `predictions`
- `alerts`

The schema is implemented in two ways:

- MySQL bootstrap DDL in [infra/mysql/schema.sql](../infra/mysql/schema.sql)
- SQLAlchemy ORM models in `backend/app/models/`

SQLite local development uses the same ORM models to create equivalent tables.

## Relationship Summary

```text
machines 1 --- * sensor_readings
machines 1 --- * predictions
machines 1 --- * alerts
sensor_readings 1 --- 1 predictions
predictions 1 --- 0..1 alerts
```

## Table Details

### `machines`

Purpose:

- stores machine-level metadata used by the dashboard and attached to incoming readings

Key columns:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `machine_code` | string | Unique business identifier |
| `machine_name` | string nullable | Human-readable label |
| `line_name` | string nullable | Production line grouping |
| `asset_type` | string nullable | Machine category |
| `status` | string | `active`, `maintenance`, or `offline` |
| `created_at` | timestamp | Row creation time |

Behavior notes:

- created automatically on first ingest if the machine does not exist
- updated on later ingests when metadata fields are supplied again

### `sensor_readings`

Purpose:

- stores the raw sensor payload that was ingested for inference

Key columns:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `machine_id` | foreign key | References `machines.id` |
| `source_udi` | integer nullable | Dataset/source identifier |
| `product_id` | string nullable | Original product identifier |
| `product_type` | string | `L`, `M`, or `H` |
| `captured_at` | datetime | Event timestamp from the payload |
| `air_temperature_k` | numeric | Sensor feature |
| `process_temperature_k` | numeric | Sensor feature |
| `rotational_speed_rpm` | numeric | Sensor feature |
| `torque_nm` | numeric | Sensor feature |
| `tool_wear_min` | numeric | Sensor feature |
| `created_at` | timestamp | Row creation time |

Behavior notes:

- every ingested payload becomes one `sensor_readings` row
- the backend stores these values before creating the matching prediction row

### `predictions`

Purpose:

- stores the output of ONNX Runtime inference for a single sensor reading

Key columns:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `machine_id` | foreign key | References `machines.id` |
| `sensor_reading_id` | foreign key | Unique reference to `sensor_readings.id` |
| `model_name` | string | Comes from `model_metadata.json` |
| `failure_probability` | float | Positive-class probability |
| `threshold_used` | float | Decision threshold stored with the prediction |
| `predicted_failure` | boolean | True when probability crosses the model threshold |
| `risk_level` | string | `low`, `medium`, `high`, or `critical` |
| `created_at` | timestamp | Row creation time |

Behavior notes:

- one prediction is created for each sensor reading
- `risk_level` is derived in the backend service layer
- predictions are returned newest-first by the API

### `alerts`

Purpose:

- stores alert records for predictions that cross the configured alert threshold

Key columns:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `machine_id` | foreign key | References `machines.id` |
| `prediction_id` | foreign key | Unique reference to `predictions.id` |
| `severity` | string | `medium`, `high`, or `critical` in current practice |
| `status` | string | `open` or `acknowledged` |
| `message` | string | Human-readable alert message |
| `acknowledged_at` | datetime nullable | Set when acknowledged |
| `created_at` | timestamp | Row creation time |

Behavior notes:

- an alert is created only when the probability crosses the configured alert threshold
- the current frontend reads alert data but does not yet implement alert acknowledgment
- the dashboard alert panel filters for high/critical alerts client-side

## Inference And Schema Alignment

The fields used for model inference are stored in `sensor_readings` and mapped into the ONNX input contract:

- `product_type` -> one-hot encoded into `type_L`, `type_M`, `type_H`
- `air_temperature_k`
- `process_temperature_k`
- `rotational_speed_rpm`
- `torque_nm`
- `tool_wear_min`

The exact feature order is defined in:

- `ml/artifacts/model_metadata.json`
- `ml/artifacts/preprocessing_config.json`

This keeps the persisted raw reading aligned with the runtime model contract.

## Indexing And Constraints

The MySQL schema includes the following practical constraints:

- unique `machine_code` on `machines`
- unique `sensor_reading_id` on `predictions`
- unique `prediction_id` on `alerts`
- indexes on machine/time combinations for readings, predictions, and alerts

These are sufficient for the current MVP list views and recent-history queries.

## Init And Reset Notes

Fresh MySQL initialization:

- `infra/mysql/schema.sql` creates the schema
- `infra/seed/seed_machines.sql` inserts deterministic machine metadata

Reset scripts:

- `scripts/reset_db.py` drops and recreates the schema through the backend model layer
- `scripts/generate_demo_data.py` populates deterministic quick or large demo datasets

This keeps the schema reproducible across SQLite local development and MySQL runtime demos.
