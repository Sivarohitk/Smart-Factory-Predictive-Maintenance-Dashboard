from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _create_test_client(
    tmp_path: Path,
    monkeypatch,
    *,
    alert_threshold: str | None,
) -> Iterator[TestClient]:
    db_path = tmp_path / "backend-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("MODEL_ARTIFACTS_DIR", str(REPO_ROOT / "ml" / "artifacts"))
    if alert_threshold is None:
        monkeypatch.delenv("ALERT_PROBABILITY_THRESHOLD", raising=False)
    else:
        monkeypatch.setenv("ALERT_PROBABILITY_THRESHOLD", alert_threshold)
    monkeypatch.setenv("AUTO_CREATE_TABLES", "true")
    monkeypatch.setenv("APP_ENV", "test")

    from app.core.config import get_settings
    from app.db.session import get_engine, get_session_factory

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


@pytest.fixture
def client(tmp_path, monkeypatch):
    yield from _create_test_client(tmp_path, monkeypatch, alert_threshold="0.0001")


@pytest.fixture
def client_with_runtime_threshold(tmp_path, monkeypatch):
    yield from _create_test_client(tmp_path, monkeypatch, alert_threshold=None)
