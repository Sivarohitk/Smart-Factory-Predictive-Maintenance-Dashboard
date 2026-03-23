# Backend

FastAPI backend for the Smart Factory Predictive Maintenance Dashboard.

## What It Does

- stores `machines`
- ingests `sensor_readings`
- runs ONNX Runtime inference against the exported model in `../ml/artifacts/`
- stores `predictions`
- creates `alerts` when probability crosses the configured threshold

## Local Run

Run from the `backend/` directory:

```bash
python -m pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Notes

- The primary database target is MySQL.
- For local tests, SQLite is used only as a lightweight test database.
- The backend loads `failure_model.onnx`, `model_metadata.json`, and `preprocessing_config.json` from `../ml/artifacts/`.
