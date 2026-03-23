# Smart Factory Predictive Maintenance Dashboard

Portfolio MVP for predictive maintenance using a React + Vite dashboard, a FastAPI backend, MySQL for the primary runtime database, and ONNX Runtime for model inference.

The project ingests machine sensor readings, runs failure-risk inference against an exported ONNX model, stores predictions and alerts, and displays the results in a locally runnable dashboard. The training dataset is the public UCI AI4I 2020 Predictive Maintenance Dataset, which is synthetic and documented as such throughout the repo.

## Project Overview

This project is designed to match a realistic resume bullet without drifting into unnecessary platform complexity. The implemented scope covers:

- a React dashboard for machines, predictions, alerts, risk trends, and sensor ingestion
- a FastAPI backend for REST endpoints, persistence, and ONNX Runtime inference
- a MySQL-first runtime path through Docker Compose
- a SQLite fallback for local development and tests
- a CLI-only ML pipeline that trains a lightweight model and exports `failure_model.onnx`
- deterministic seed/demo data plus a simulator that drives the live API flow

## Docs

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Deployment](docs/deployment.md)
- [Database Schema](docs/database_schema.md)
- [ML Pipeline](ml/README.md)

## Tech Stack

- Frontend: React 18, Vite
- Backend: FastAPI, SQLAlchemy, Pydantic
- Database: MySQL 8 in Docker Compose, SQLite fallback for local development
- ML: scikit-learn training pipeline, ONNX export, ONNX Runtime inference
- Tooling: Docker Compose, deterministic seed/demo scripts, API simulator script

## Architecture Diagram

```text
UCI AI4I 2020 Dataset (synthetic)
            |
            v
   ml/scripts/*.py
            |
            v
 ml/artifacts/failure_model.onnx
 ml/artifacts/model_metadata.json
 ml/artifacts/preprocessing_config.json
            |
            v
 FastAPI backend + ONNX Runtime  <------>  MySQL
            ^                               ^
            |                               |
            |                               |
 React + Vite dashboard              Seed/demo scripts
            ^                               |
            |                               |
      Manual sensor input         simulate_sensor_stream.py
```

## Key Features

- Batch sensor ingestion through `POST /sensor-readings/batch`
- Single-reading prediction flow through `POST /predict`
- ONNX Runtime inference in the backend only
- Persistent storage for `machines`, `sensor_readings`, `predictions`, and `alerts`
- Configurable alert thresholding with stored alert records for risky cases
- Dashboard views for KPIs, recent predictions, high-risk alerts, machine inventory, and recent risk trend
- Deterministic quick-demo and larger demo data workflows
- End-to-end simulation script for live API demos

## Repository Layout

```text
frontend/   React + Vite dashboard
backend/    FastAPI API, DB models, services, ONNX runtime loader, tests
ml/         CLI-only training, preprocessing, export, and ONNX smoke test
infra/      MySQL init SQL and Docker Compose infrastructure files
scripts/    DB reset, demo data generation, and live API simulation
docs/       Architecture, API, deployment, and database documentation
```

## Local Setup

Prerequisites:

- Python 3.12+
- Node.js 20+
- Docker Desktop with Compose support for the MySQL-first runtime path

### SQLite Local-Dev Quick Start

This is the fastest way to run the app without Docker. SQLite is intended for local development and testing only. The primary runtime path remains MySQL through Docker Compose.

1. Train and export the ONNX artifact if `ml/artifacts/` is missing the model files.
2. Start the backend from the `backend/` directory.
3. Start the frontend from the `frontend/` directory.
4. Seed quick demo data or use the simulator.

Backend, PowerShell example:

```powershell
cd backend
python -m pip install -r requirements.txt
$env:DATABASE_URL="sqlite:///./smart_factory_demo.db"
$env:MODEL_ARTIFACTS_DIR="../ml/artifacts"
$env:AUTO_CREATE_TABLES="true"
uvicorn app.main:app --reload
```

Frontend, PowerShell example:

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL="http://localhost:8000"
npm run dev
```

Quick demo seed against the same SQLite file:

```powershell
python scripts/reset_db.py --database-url sqlite:///./backend/smart_factory_demo.db
python scripts/generate_demo_data.py --mode quick --database-url sqlite:///./backend/smart_factory_demo.db
```

Open:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/health`
- FastAPI docs: `http://localhost:8000/docs`

### Docker Compose Setup

Docker Compose is the primary local deployment path for the full stack.

Optional env override:

```powershell
copy .env.example .env
```

Start the full app:

```powershell
docker compose up --build
```

Detached mode:

```powershell
docker compose up --build -d
```

Open:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Backend health: `http://localhost:8000/health`
- FastAPI docs: `http://localhost:8000/docs`
- MySQL: `localhost:3306`

Compose notes:

- `frontend`, `backend`, and `db` run in separate containers
- MySQL persists data in the `mysql_data` named volume
- the backend loads ONNX artifacts from `/app/model-artifacts`
- `infra/mysql/schema.sql` and `infra/seed/seed_machines.sql` run automatically on first boot of a fresh MySQL volume
- the backend retries database connection during startup to handle MySQL warm-up

## Training And ONNX Export

Run from the repo root:

```powershell
python -m pip install -r ml/requirements.txt
python ml/scripts/download_data.py
python ml/scripts/preprocess.py
python ml/scripts/train.py
python ml/scripts/export_onnx.py
python ml/scripts/test_onnx_inference.py
```

Produced artifacts:

- `ml/artifacts/failure_model.onnx`
- `ml/artifacts/model_metadata.json`
- `ml/artifacts/preprocessing_config.json`
- `ml/artifacts/failure_model.joblib`
- `ml/artifacts/training_metrics.json`

The backend only uses the ONNX artifact and metadata for runtime inference. Training code is not used at inference time.

## Seed And Demo Data Workflow

The repo supports two demo modes:

- Quick demo mode: a small deterministic dataset for six machines
- Larger demo mode: generated records for dashboard tables, trend views, and screenshots

If the raw dataset is missing, download it first:

```powershell
python ml/scripts/download_data.py
```

SQLite quick demo:

```powershell
python scripts/reset_db.py --database-url sqlite:///./backend/smart_factory_demo.db
python scripts/generate_demo_data.py --mode quick --database-url sqlite:///./backend/smart_factory_demo.db
```

MySQL quick demo:

```powershell
python scripts/reset_db.py --database-url mysql+pymysql://smart_factory_user:smart_factory_password@localhost:3306/smart_factory
python scripts/generate_demo_data.py --mode quick --database-url mysql+pymysql://smart_factory_user:smart_factory_password@localhost:3306/smart_factory
```

Larger demo data:

```powershell
python scripts/generate_demo_data.py --mode large --records-per-machine 48 --database-url mysql+pymysql://smart_factory_user:smart_factory_password@localhost:3306/smart_factory
```

Docker Compose quick demo seed from inside the backend container:

```powershell
docker compose exec backend python /workspace/scripts/generate_demo_data.py --mode quick --database-url mysql+pymysql://smart_factory_user:smart_factory_password@db:3306/smart_factory
```

Docker Compose larger demo seed from inside the backend container:

```powershell
docker compose exec backend python /workspace/scripts/generate_demo_data.py --mode large --records-per-machine 48 --database-url mysql+pymysql://smart_factory_user:smart_factory_password@db:3306/smart_factory
```

## Simulator And End-To-End Demo Flow

The simulator posts deterministic sensor batches into the live API, which is useful for demos, screenshots, and quick end-to-end verification.

Quick burst:

```powershell
python scripts/simulate_sensor_stream.py --mode quick --api-base-url http://localhost:8000
```

Larger streamed demo:

```powershell
python scripts/simulate_sensor_stream.py --mode stream --records-per-machine 12 --batch-size 6 --interval-seconds 1 --api-base-url http://localhost:8000
```

Live flow:

1. Start database, backend, and frontend.
2. Seed demo data or post records with the simulator or UI ingestion panel.
3. FastAPI maps payload fields into the explicit ONNX input contract.
4. ONNX Runtime returns a failure probability.
5. The backend stores the sensor reading and prediction.
6. An alert is created when probability crosses the configured threshold.
7. The frontend refreshes `/machines`, `/predictions`, and `/alerts` to show the new records.

## API Overview

Implemented endpoints:

- `GET /`
- `GET /health`
- `POST /predict`
- `POST /sensor-readings/batch`
- `GET /machines`
- `GET /predictions`
- `GET /alerts`

The frontend currently uses:

- `GET /health`
- `GET /machines`
- `GET /predictions`
- `GET /alerts`
- `POST /sensor-readings/batch`

Full payload examples and response shapes are documented in [docs/api.md](docs/api.md). Live OpenAPI docs are exposed by FastAPI at `http://localhost:8000/docs`.

## Screenshots Placeholder

Add screenshots here as the portfolio presentation is finalized:

- Dashboard overview with KPI cards and recent risk trend
- Predictions table and high-risk alerts panel
- Sensor ingestion panel with live API success state
- Docker Compose demo with MySQL-backed data

## Future Improvements

- Add server-side filtering and pagination for predictions and alerts
- Add alert acknowledgment workflow to the frontend
- Replace the Vite dev server container with a production static frontend build
- Add richer historical visualizations and machine detail drill-downs
- Add API-level authentication if the project scope expands beyond a portfolio MVP
- Evaluate against additional maintenance datasets beyond the current synthetic source

## Known Limitations

- The current public training dataset is synthetic, not real plant telemetry
- Docker Compose is configured for local development, not production deployment hardening
- The frontend uses a sample preview fallback mode, but live API mode remains the primary demo path
- The simulator posts deterministic HTTP batches; it is not a streaming broker or event pipeline
- The list endpoints expose a simple `limit` parameter, but not full server-side filtering
