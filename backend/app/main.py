from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.db.session import init_db
from app.ml.runtime import OnnxInferenceRuntime


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.auto_create_tables:
            init_db()
        app.state.settings = settings
        app.state.model_runtime = OnnxInferenceRuntime(
            model_path=settings.onnx_model_path,
            model_metadata_path=settings.model_metadata_path,
            preprocessing_config_path=settings.preprocessing_config_path,
        )
        yield

    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        description=(
            "FastAPI backend for ingesting machine sensor readings, "
            "running ONNX Runtime inference, and storing predictions and alerts."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
