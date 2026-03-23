from __future__ import annotations

from functools import lru_cache
import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
    connect_args: dict[str, object] = {}

    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(settings.database_url, connect_args=connect_args, **engine_kwargs)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_db():
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from app.models import Base  # noqa: F401
    settings = get_settings()
    last_error: Exception | None = None

    for attempt in range(1, settings.database_connect_max_attempts + 1):
        try:
            with get_engine().connect() as connection:
                connection.execute(text("SELECT 1"))
            break
        except Exception as exc:
            last_error = exc
            if attempt >= settings.database_connect_max_attempts:
                raise
            time.sleep(settings.database_connect_retry_seconds)
    else:
        if last_error is not None:
            raise last_error

    Base.metadata.create_all(bind=get_engine())


def check_database_connection() -> bool:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
