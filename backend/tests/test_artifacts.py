from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = REPO_ROOT / "ml" / "artifacts"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_ml_artifact_paths_are_repo_relative():
    metadata = load_json(ARTIFACTS_DIR / "model_metadata.json")
    preprocessing = load_json(ARTIFACTS_DIR / "preprocessing_config.json")

    for key in ("training_metrics_path", "sklearn_model_path", "onnx_model_path"):
        assert not Path(str(metadata[key])).is_absolute()

    output_files = preprocessing["output_files"]
    assert isinstance(output_files, dict)
    for value in output_files.values():
        assert not Path(str(value)).is_absolute()


def test_model_feature_contract_matches_preprocessing_metadata():
    metadata = load_json(ARTIFACTS_DIR / "model_metadata.json")
    preprocessing = load_json(ARTIFACTS_DIR / "preprocessing_config.json")

    assert metadata["feature_columns"] == preprocessing["model_feature_columns"]
