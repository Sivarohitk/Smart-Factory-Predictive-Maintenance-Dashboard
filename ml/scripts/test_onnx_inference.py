from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import onnxruntime as ort
import pandas as pd

from common import ARTIFACTS_DIR, PROCESSED_DATA_DIR, ensure_directories, read_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a smoke test against the exported ONNX model."
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=ARTIFACTS_DIR,
        help="Directory containing the exported ONNX model and metadata.",
    )
    parser.add_argument(
        "--test-split",
        type=Path,
        default=PROCESSED_DATA_DIR / "test.csv",
        help="Path to the processed test split CSV file.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=8,
        help="Number of rows from the test split to compare.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-5,
        help="Maximum allowed absolute probability difference.",
    )
    args = parser.parse_args()

    ensure_directories()

    metadata = read_json(args.artifacts_dir / "model_metadata.json")
    feature_columns = metadata["feature_columns"]
    input_tensor_name = metadata["input_tensor_name"]
    probability_output_name = metadata["probability_output_name"]
    label_output_name = metadata["label_output_name"]

    test_frame = pd.read_csv(args.test_split)
    sample_frame = test_frame.head(args.rows)
    if sample_frame.empty:
        raise ValueError("The test split is empty; cannot run ONNX smoke test.")

    features = sample_frame[feature_columns].to_numpy(dtype=np.float32)

    sklearn_model = joblib.load(args.artifacts_dir / "failure_model.joblib")
    sklearn_probabilities = sklearn_model.predict_proba(sample_frame[feature_columns])[:, 1]
    sklearn_labels = sklearn_model.predict(sample_frame[feature_columns]).astype(np.int64)

    session = ort.InferenceSession(
        str(args.artifacts_dir / "failure_model.onnx"),
        providers=["CPUExecutionProvider"],
    )
    onnx_labels, onnx_probabilities = session.run(
        [label_output_name, probability_output_name],
        {input_tensor_name: features},
    )
    onnx_positive_class = np.asarray(onnx_probabilities)[:, 1]
    label_mismatch_count = int(np.sum(onnx_labels.astype(np.int64) != sklearn_labels))
    max_abs_diff = float(np.max(np.abs(onnx_positive_class - sklearn_probabilities)))

    if label_mismatch_count > 0:
        raise AssertionError(
            f"ONNX label mismatch count {label_mismatch_count} exceeds zero."
        )
    if max_abs_diff > args.tolerance:
        raise AssertionError(
            f"ONNX probability max abs diff {max_abs_diff:.8f} exceeds tolerance {args.tolerance:.8f}."
        )

    print("ONNX inference smoke test passed.")
    print(f"Rows checked: {sample_frame.shape[0]}")
    print(f"Max probability abs diff: {max_abs_diff:.8f}")
    print(f"Sample positive-class probabilities: {onnx_positive_class.tolist()}")


if __name__ == "__main__":
    main()

