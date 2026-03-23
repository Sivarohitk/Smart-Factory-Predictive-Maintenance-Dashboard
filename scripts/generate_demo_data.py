from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
RAW_DATA_PATH = REPO_ROOT / "ml" / "data" / "raw" / "ai4i2020.csv"
QUICK_DEMO_PATH = REPO_ROOT / "infra" / "seed" / "quick_demo_records.json"
MODEL_ARTIFACTS_DIR = REPO_ROOT / "ml" / "artifacts"

MACHINE_SEEDS = [
    {
        "machine_code": "MILL-001",
        "machine_name": "Mill 001",
        "line_name": "Line A",
        "asset_type": "Milling Machine",
        "machine_status": "active",
    },
    {
        "machine_code": "LATHE-002",
        "machine_name": "Lathe 002",
        "line_name": "Line A",
        "asset_type": "CNC Lathe",
        "machine_status": "active",
    },
    {
        "machine_code": "PRESS-003",
        "machine_name": "Press 003",
        "line_name": "Line B",
        "asset_type": "Hydraulic Press",
        "machine_status": "active",
    },
    {
        "machine_code": "CNC-004",
        "machine_name": "CNC 004",
        "line_name": "Line B",
        "asset_type": "Machining Center",
        "machine_status": "active",
    },
    {
        "machine_code": "ROBOT-005",
        "machine_name": "Robot 005",
        "line_name": "Line C",
        "asset_type": "Robotic Arm",
        "machine_status": "active",
    },
    {
        "machine_code": "PUMP-006",
        "machine_name": "Pump 006",
        "line_name": "Line C",
        "asset_type": "Coolant Pump",
        "machine_status": "active",
    },
]


def ensure_backend_import_path() -> None:
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))


def configure_backend(database_url: str | None) -> tuple[object, object]:
    ensure_backend_import_path()

    if database_url:
        os.environ["DATABASE_URL"] = database_url
    os.environ.setdefault("MODEL_ARTIFACTS_DIR", str(MODEL_ARTIFACTS_DIR))
    os.environ.setdefault("AUTO_CREATE_TABLES", "true")

    from app.core.config import get_settings
    from app.db.session import get_engine, get_session_factory

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    settings = get_settings()
    return settings, get_session_factory()


def load_source_rows() -> tuple[dict[int, dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing raw dataset at {RAW_DATA_PATH}. "
            "Run `python ml/scripts/download_data.py` first."
        )

    rows_by_udi: dict[int, dict[str, object]] = {}
    positive_rows: list[dict[str, object]] = []
    negative_rows: list[dict[str, object]] = []

    with RAW_DATA_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized = {
                "source_udi": int(row["UDI"]),
                "product_id": row["Product ID"],
                "product_type": row["Type"],
                "air_temperature_k": float(row["Air temperature [K]"]),
                "process_temperature_k": float(row["Process temperature [K]"]),
                "rotational_speed_rpm": float(row["Rotational speed [rpm]"]),
                "torque_nm": float(row["Torque [Nm]"]),
                "tool_wear_min": float(row["Tool wear [min]"]),
                "machine_failure": int(row["Machine failure"]),
            }
            rows_by_udi[normalized["source_udi"]] = normalized
            if normalized["machine_failure"] == 1:
                positive_rows.append(normalized)
            else:
                negative_rows.append(normalized)

    return rows_by_udi, positive_rows, negative_rows


def build_payload(seed: dict[str, object], source_row: dict[str, object]) -> dict[str, object]:
    return {
        "machine_code": seed["machine_code"],
        "machine_name": seed.get("machine_name"),
        "line_name": seed.get("line_name"),
        "asset_type": seed.get("asset_type"),
        "machine_status": seed.get("machine_status", "active"),
        "source_udi": source_row["source_udi"],
        "product_id": source_row["product_id"],
        "product_type": source_row["product_type"],
        "captured_at": seed["captured_at"],
        "air_temperature_k": source_row["air_temperature_k"],
        "process_temperature_k": source_row["process_temperature_k"],
        "rotational_speed_rpm": source_row["rotational_speed_rpm"],
        "torque_nm": source_row["torque_nm"],
        "tool_wear_min": source_row["tool_wear_min"],
    }


def summarize_counts(session) -> dict[str, int]:
    from sqlalchemy import func, select

    from app.models import Alert, Machine, Prediction, SensorReading

    return {
        "machines": int(session.scalar(select(func.count()).select_from(Machine)) or 0),
        "sensor_readings": int(session.scalar(select(func.count()).select_from(SensorReading)) or 0),
        "predictions": int(session.scalar(select(func.count()).select_from(Prediction)) or 0),
        "alerts": int(session.scalar(select(func.count()).select_from(Alert)) or 0),
    }


def load_quick_demo_records() -> list[dict[str, object]]:
    return json.loads(QUICK_DEMO_PATH.read_text(encoding="utf-8"))


def build_large_demo_records(records_per_machine: int) -> list[dict[str, object]]:
    _, positive_rows, negative_rows = load_source_rows()
    base_timestamp = datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc)
    seeds: list[dict[str, object]] = []

    for machine_index, machine in enumerate(MACHINE_SEEDS):
        for reading_index in range(records_per_machine):
            is_risk_spike = reading_index % 10 in {7, 8}
            source_pool = positive_rows if is_risk_spike else negative_rows
            source_index = (
                machine_index * 97 + reading_index * (5 if is_risk_spike else 17)
            ) % len(source_pool)
            source_row = source_pool[source_index]
            captured_at = base_timestamp + timedelta(
                minutes=(reading_index * 20) + (machine_index * 4)
            )
            seeds.append(
                {
                    **machine,
                    "source_udi": source_row["source_udi"],
                    "captured_at": captured_at.isoformat(),
                }
            )
    return seeds


def run_demo(mode: str, records_per_machine: int, database_url: str | None) -> None:
    settings, session_factory = configure_backend(database_url)

    from app.core.config import get_settings
    from app.db.session import init_db
    from app.ml.runtime import OnnxInferenceRuntime
    from app.schemas.sensor_reading import SensorReadingCreate
    from app.services.ingestion_service import ingest_and_predict

    init_db()

    runtime = OnnxInferenceRuntime(
        model_path=settings.onnx_model_path,
        model_metadata_path=settings.model_metadata_path,
        preprocessing_config_path=settings.preprocessing_config_path,
    )
    alert_threshold = settings.alert_probability_threshold or runtime.decision_threshold
    rows_by_udi, _, _ = load_source_rows()

    if mode == "quick":
        seeds = load_quick_demo_records()
    else:
        seeds = build_large_demo_records(records_per_machine)

    with session_factory() as session:
        for seed in seeds:
            source_udi = int(seed["source_udi"])
            source_row = rows_by_udi[source_udi]
            payload = SensorReadingCreate.model_validate(build_payload(seed, source_row))
            ingest_and_predict(
                session=session,
                runtime=runtime,
                payload=payload,
                alert_threshold=alert_threshold,
            )

        session.commit()
        counts = summarize_counts(session)

    print(f"Demo data generation complete for mode: {mode}")
    print(f"Database URL: {get_settings().database_url}")
    print(f"Records inserted this run: {len(seeds)}")
    if mode == "large":
        print(f"Records per machine: {records_per_machine}")
    print("Current table counts:")
    for table_name, count in counts.items():
        print(f"  {table_name}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate deterministic quick or large demo data for the backend database."
    )
    parser.add_argument(
        "--mode",
        choices=["quick", "large"],
        default="quick",
        help="Quick mode loads a tiny deterministic dataset. Large mode generates more readings.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Optional DB URL override. Defaults to the backend settings value.",
    )
    parser.add_argument(
        "--records-per-machine",
        type=int,
        default=48,
        help="Only used in large mode. Number of generated readings per machine.",
    )
    args = parser.parse_args()

    run_demo(
        mode=args.mode,
        records_per_machine=args.records_per_machine,
        database_url=args.database_url,
    )


if __name__ == "__main__":
    main()
