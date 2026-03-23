from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_ARTIFACTS_DIR = REPO_ROOT / "ml" / "artifacts"


class Settings(BaseSettings):
    app_name: str = "Smart Factory Predictive Maintenance Dashboard"
    app_env: str = "development"
    database_url: str = (
        "mysql+pymysql://smart_factory_user:smart_factory_password@localhost:3306/smart_factory"
    )
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    model_artifacts_dir: Path = DEFAULT_MODEL_ARTIFACTS_DIR
    onnx_model_filename: str = "failure_model.onnx"
    model_metadata_filename: str = "model_metadata.json"
    preprocessing_config_filename: str = "preprocessing_config.json"
    alert_probability_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    auto_create_tables: bool = True
    database_connect_max_attempts: int = Field(default=20, ge=1, le=120)
    database_connect_retry_seconds: float = Field(default=2.0, gt=0.0, le=30.0)

    model_config = SettingsConfigDict(
        env_file=(BACKEND_ROOT / ".env", REPO_ROOT / ".env"),
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def onnx_model_path(self) -> Path:
        return self.model_artifacts_dir / self.onnx_model_filename

    @property
    def model_metadata_path(self) -> Path:
        return self.model_artifacts_dir / self.model_metadata_filename

    @property
    def preprocessing_config_path(self) -> Path:
        return self.model_artifacts_dir / self.preprocessing_config_filename


@lru_cache
def get_settings() -> Settings:
    return Settings()
