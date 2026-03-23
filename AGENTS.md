# AGENTS.md

## Repo Rules

- Keep this project as an MVP only. Do not overengineer it.
- Keep the project portfolio-grade and locally runnable by one person.
- Use a clean monorepo structure with `frontend/`, `backend/`, `ml/`, and `infra/`.
- Use React + Vite for the frontend.
- Use FastAPI for the backend.
- Use MySQL for the database.
- Use consistent naming from the start:
  - `machines`
  - `sensor_readings`
  - `predictions`
  - `alerts`
- Inference in the backend must use ONNX Runtime only.
- Do not use raw training code for in-app inference.
- Keep all ML code CLI-runnable only.
- Do not rely on notebooks. If `notebooks/` is ever added, keep it empty or optional.
- Keep Alembic optional only if migrations stay simple. Do not add unnecessary migration complexity.
- The whole project must run locally with Docker Compose.
- Keep Dockerfiles only where they are actually used.
- Use a public predictive-maintenance dataset or other reproducible open source.
- The planned dataset is public and synthetic, so document that clearly in the README and docs.
- Include REST API docs, database schema docs, seed/demo data, and clear setup steps as the project is implemented.
- Do not start feature implementation before the current scope is approved.

