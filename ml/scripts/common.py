from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ML_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ML_ROOT.parent
DATA_DIR = ML_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = ML_ROOT / "artifacts"

DATASET_NAME = "AI4I 2020 Predictive Maintenance Dataset"
DATASET_URL = (
    "https://archive.ics.uci.edu/static/public/601/"
    "ai4i%2B2020%2Bpredictive%2Bmaintenance%2Bdataset.zip"
)
DATASET_PAGE_URL = "https://archive.ics.uci.edu/dataset/601/ai4i"
DATASET_DOI = "10.24432/C5HS5C"
DATASET_LICENSE = "CC BY 4.0"
RAW_ARCHIVE_NAME = "ai4i2020.zip"
RAW_CSV_NAME = "ai4i2020.csv"

RAW_TO_CANONICAL_COLUMNS = {
    "UDI": "source_udi",
    "Product ID": "product_id",
    "Type": "type",
    "Air temperature [K]": "air_temperature_k",
    "Process temperature [K]": "process_temperature_k",
    "Rotational speed [rpm]": "rotational_speed_rpm",
    "Torque [Nm]": "torque_nm",
    "Tool wear [min]": "tool_wear_min",
    "Machine failure": "machine_failure",
}

TYPE_CATEGORIES = ["L", "M", "H"]
NUMERIC_FEATURE_COLUMNS = [
    "air_temperature_k",
    "process_temperature_k",
    "rotational_speed_rpm",
    "torque_nm",
    "tool_wear_min",
]
ONE_HOT_FEATURE_COLUMNS = [f"type_{category}" for category in TYPE_CATEGORIES]
MODEL_FEATURE_COLUMNS = ONE_HOT_FEATURE_COLUMNS + NUMERIC_FEATURE_COLUMNS
TARGET_COLUMN = "machine_failure"
IDENTIFIER_COLUMNS = ["source_udi", "product_id", "type"]

DEFAULT_RANDOM_STATE = 42
DEFAULT_VAL_SIZE = 0.15
DEFAULT_TEST_SIZE = 0.15


def ensure_directories() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def to_repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()
