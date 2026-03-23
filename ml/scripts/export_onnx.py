from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import onnx
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

from common import ARTIFACTS_DIR, ensure_directories, read_json


def add_onnx_metadata(onnx_path: Path, metadata: dict[str, object]) -> None:
    model = onnx.load_model(onnx_path)
    del model.metadata_props[:]
    for key, value in metadata.items():
        entry = model.metadata_props.add()
        entry.key = key
        entry.value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
    onnx.save_model(model, onnx_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the trained scikit-learn model to ONNX format."
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=ARTIFACTS_DIR,
        help="Directory containing the trained sklearn model and metadata.",
    )
    args = parser.parse_args()

    ensure_directories()

    model_path = args.artifacts_dir / "failure_model.joblib"
    metadata_path = args.artifacts_dir / "model_metadata.json"
    onnx_path = args.artifacts_dir / "failure_model.onnx"

    model = joblib.load(model_path)
    metadata = read_json(metadata_path)
    feature_count = int(metadata["feature_count"])
    input_tensor_name = str(metadata["input_tensor_name"])

    onnx_model = convert_sklearn(
        model,
        initial_types=[(input_tensor_name, FloatTensorType([None, feature_count]))],
        options={id(model): {"zipmap": False}},
        target_opset=17,
    )
    onnx_model.graph.output[0].name = str(metadata["label_output_name"])
    onnx_model.graph.output[1].name = str(metadata["probability_output_name"])
    onnx_path.write_bytes(onnx_model.SerializeToString())

    add_onnx_metadata(
        onnx_path,
        {
            "model_name": metadata["model_name"],
            "feature_columns": metadata["feature_columns"],
            "feature_count": metadata["feature_count"],
            "target_column": metadata["target_column"],
            "positive_class_label": metadata["positive_class_label"],
            "decision_threshold": metadata["decision_threshold"],
            "dataset_name": metadata["dataset_name"],
            "dataset_is_synthetic": metadata["dataset_is_synthetic"],
        },
    )

    print(f"Exported ONNX model: {onnx_path}")


if __name__ == "__main__":
    main()

