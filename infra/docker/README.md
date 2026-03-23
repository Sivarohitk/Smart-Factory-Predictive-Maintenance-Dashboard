# Docker Notes

The active container workflow is defined in [docker-compose.yml](../../docker-compose.yml).

Current runtime:

- `db`: MySQL 8 on port `3306` with persistent storage in the `mysql_data` volume
- `backend`: FastAPI on port `8000`, loading ONNX artifacts from `/app/model-artifacts`
- `frontend`: Vite React dev server on port `5173`

MySQL bootstrap:

- [schema.sql](../mysql/schema.sql) creates the schema on first boot of a fresh volume
- [seed_machines.sql](../seed/seed_machines.sql) inserts deterministic base machine metadata on first boot of a fresh volume
