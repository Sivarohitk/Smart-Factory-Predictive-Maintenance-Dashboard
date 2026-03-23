# Deployment

## Scope

This document covers local deployment for the current MVP. The implemented deployment target is Docker Compose for a MySQL-backed runtime. A non-Docker local workflow is also documented for development convenience.

## Docker Compose Runtime

The Compose stack lives in [docker-compose.yml](../docker-compose.yml).

Services:

- `db`: MySQL 8
- `backend`: FastAPI service with ONNX Runtime inference
- `frontend`: React + Vite dev server

Start the full stack:

```powershell
docker compose up --build
```

Detached mode:

```powershell
docker compose up --build -d
```

## Ports

- Frontend: `5173`
- Backend: `8000`
- MySQL: `3306`

URLs after startup:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Backend health: `http://localhost:8000/health`
- FastAPI docs: `http://localhost:8000/docs`

## Persistent Storage

MySQL data is persisted in the named Docker volume `mysql_data`.

This means:

- `docker compose down` stops containers but keeps database data
- `docker compose down -v` removes the MySQL data volume and forces a clean init on next boot

## ONNX Artifacts In Containers

The backend container loads model artifacts from:

- `/app/model-artifacts/failure_model.onnx`
- `/app/model-artifacts/model_metadata.json`
- `/app/model-artifacts/preprocessing_config.json`

Those files are mounted read-only from the host path:

- `ml/artifacts/`

The backend does not use the sklearn training artifact at runtime.

## MySQL Init And Seed Flow

On first boot of a fresh `mysql_data` volume, the MySQL container runs:

1. [infra/mysql/schema.sql](../infra/mysql/schema.sql)
2. [infra/seed/seed_machines.sql](../infra/seed/seed_machines.sql)

What that does:

- creates `machines`, `sensor_readings`, `predictions`, and `alerts`
- inserts deterministic base machine metadata for six machines

These files only run automatically when the MySQL data volume is empty.

## Backend Startup Behavior

The backend depends on the MySQL container healthcheck and also retries database connection during startup. This helps avoid race conditions during local Compose boot.

The backend runtime also mounts the repo root to `/workspace` so it can execute the existing seed/demo scripts inside the container when needed.

## Seeding Demo Data After Startup

Quick demo dataset:

```powershell
docker compose exec backend python /workspace/scripts/generate_demo_data.py --mode quick --database-url mysql+pymysql://smart_factory_user:smart_factory_password@db:3306/smart_factory
```

Larger demo dataset:

```powershell
docker compose exec backend python /workspace/scripts/generate_demo_data.py --mode large --records-per-machine 48 --database-url mysql+pymysql://smart_factory_user:smart_factory_password@db:3306/smart_factory
```

Live simulator against the running stack from the host machine:

```powershell
python scripts/simulate_sensor_stream.py --mode quick --api-base-url http://localhost:8000
```

## Reset Commands

Stop containers only:

```powershell
docker compose down
```

Stop containers and remove the MySQL volume:

```powershell
docker compose down -v
```

Stop containers, remove the MySQL volume, and remove orphaned services:

```powershell
docker compose down -v --remove-orphans
```

## Environment Variables

Primary Compose environment defaults are in [.env.example](../.env.example).

Key variables:

- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `DATABASE_URL`
- `APP_ENV`
- `APP_NAME`
- `ALERT_PROBABILITY_THRESHOLD`
- `CORS_ORIGINS`
- `AUTO_CREATE_TABLES`
- `DATABASE_CONNECT_MAX_ATTEMPTS`
- `DATABASE_CONNECT_RETRY_SECONDS`

If needed, copy the example file before startup:

```powershell
copy .env.example .env
```

## Non-Docker Local Workflow

SQLite fallback:

```powershell
cd backend
python -m pip install -r requirements.txt
$env:DATABASE_URL="sqlite:///./smart_factory_demo.db"
$env:MODEL_ARTIFACTS_DIR="../ml/artifacts"
$env:AUTO_CREATE_TABLES="true"
uvicorn app.main:app --reload
```

Local frontend:

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL="http://localhost:8000"
npm run dev
```

SQLite reset/seed:

```powershell
python scripts/reset_db.py --database-url sqlite:///./backend/smart_factory_demo.db
python scripts/generate_demo_data.py --mode quick --database-url sqlite:///./backend/smart_factory_demo.db
```

This local fallback keeps the same API and ONNX inference path, but swaps MySQL for SQLite.
