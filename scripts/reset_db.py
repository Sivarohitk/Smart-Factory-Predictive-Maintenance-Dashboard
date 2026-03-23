from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
SCHEMA_SQL_PATH = REPO_ROOT / "infra" / "mysql" / "schema.sql"
MODEL_ARTIFACTS_DIR = REPO_ROOT / "ml" / "artifacts"


def ensure_backend_import_path() -> None:
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))


def clear_backend_caches() -> None:
    ensure_backend_import_path()
    from app.core.config import get_settings
    from app.db.session import get_engine, get_session_factory

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def configure_backend(database_url: str) -> None:
    os.environ["DATABASE_URL"] = database_url
    os.environ.setdefault("MODEL_ARTIFACTS_DIR", str(MODEL_ARTIFACTS_DIR))
    clear_backend_caches()


def init_sqlite_schema(database_url: str) -> None:
    configure_backend(database_url)
    from app.db.session import init_db

    init_db()


def execute_schema_sql(database_url: str, schema_sql_path: Path) -> None:
    engine = create_engine(database_url, pool_pre_ping=True)
    raw_sql = schema_sql_path.read_text(encoding="utf-8")
    statements = []
    current_lines: list[str] = []

    for line in raw_sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current_lines.append(line)

    normalized_sql = "\n".join(current_lines)
    for statement in normalized_sql.split(";"):
        statement = statement.strip()
        if statement:
            statements.append(statement)

    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)

    engine.dispose()


def reset_sqlite_database(database_url: str, recreate_schema: bool) -> None:
    url = make_url(database_url)
    database = url.database

    if database and database != ":memory:":
        database_path = Path(database)
        if not database_path.is_absolute():
            database_path = (Path.cwd() / database_path).resolve()
        if database_path.exists():
            database_path.unlink()

    if recreate_schema:
        init_sqlite_schema(database_url)


def reset_mysql_database(database_url: str, recreate_schema: bool, schema_sql_path: Path) -> None:
    engine = create_engine(database_url, pool_pre_ping=True)

    with engine.begin() as connection:
        connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0")
        for table_name in ["alerts", "predictions", "sensor_readings", "machines"]:
            connection.exec_driver_sql(f"DROP TABLE IF EXISTS {table_name}")
        connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1")

    engine.dispose()

    if recreate_schema:
        execute_schema_sql(database_url, schema_sql_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reset the Smart Factory demo database for SQLite or MySQL."
    )
    parser.add_argument(
        "--database-url",
        required=True,
        help="Target database URL, for example sqlite:///./smart_factory.db or mysql+pymysql://user:pass@localhost:3306/smart_factory",
    )
    parser.add_argument(
        "--schema-sql",
        type=Path,
        default=SCHEMA_SQL_PATH,
        help="MySQL schema SQL file used when recreating a MySQL database.",
    )
    parser.add_argument(
        "--skip-recreate",
        action="store_true",
        help="Drop or delete database contents without recreating the schema.",
    )
    args = parser.parse_args()

    backend_name = make_url(args.database_url).get_backend_name()
    recreate_schema = not args.skip_recreate

    if backend_name == "sqlite":
        reset_sqlite_database(args.database_url, recreate_schema=recreate_schema)
    elif backend_name in {"mysql", "mariadb"}:
        reset_mysql_database(
            args.database_url,
            recreate_schema=recreate_schema,
            schema_sql_path=args.schema_sql,
        )
    else:
        raise ValueError(
            f"Unsupported backend '{backend_name}'. This reset script supports SQLite and MySQL."
        )

    print(f"Database reset complete for backend: {backend_name}")
    print(f"Recreated schema: {recreate_schema}")


if __name__ == "__main__":
    main()
