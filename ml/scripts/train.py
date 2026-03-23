from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from common import (
    ARTIFACTS_DIR,
    DATASET_DOI,
    DATASET_NAME,
    DATASET_PAGE_URL,
    DEFAULT_RANDOM_STATE,
    MODEL_FEATURE_COLUMNS,
    PROCESSED_DATA_DIR,
    TARGET_COLUMN,
    ensure_directories,
    read_json,
    to_repo_relative,
    write_json,
)


def load_split(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def find_best_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    f1_scores = (
        2 * precision[:-1] * recall[:-1] / np.clip(precision[:-1] + recall[:-1], 1e-12, None)
    )
    best_index = int(np.nanargmax(f1_scores))
    return {
        "threshold": float(thresholds[best_index]),
        "precision": float(precision[best_index]),
        "recall": float(recall[best_index]),
        "f1": float(f1_scores[best_index]),
    }


def evaluate_split(
    split_name: str,
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> dict[str, float | int | list[list[int]]]:
    predictions = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(y_true, predictions, labels=[0, 1])
    return {
        "split": split_name,
        "rows": int(y_true.shape[0]),
        "positive_rate": float(y_true.mean()),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "average_precision": float(average_precision_score(y_true, probabilities)),
        "precision_at_threshold": float(precision_score(y_true, predictions, zero_division=0)),
        "recall_at_threshold": float(recall_score(y_true, predictions, zero_division=0)),
        "f1_at_threshold": float(f1_score(y_true, predictions, zero_division=0)),
        "balanced_accuracy_at_threshold": float(balanced_accuracy_score(y_true, predictions)),
        "confusion_matrix": matrix.astype(int).tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a lightweight predictive maintenance classifier."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROCESSED_DATA_DIR,
        help="Directory containing processed train/validation/test CSV files.",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=ARTIFACTS_DIR,
        help="Directory for trained model and metrics artifacts.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=DEFAULT_RANDOM_STATE,
        help="Random seed for reproducible model training.",
    )
    args = parser.parse_args()

    ensure_directories()
    args.artifacts_dir.mkdir(parents=True, exist_ok=True)

    preprocessing_config = read_json(args.artifacts_dir / "preprocessing_config.json")
    feature_columns = preprocessing_config["model_feature_columns"]
    target_column = preprocessing_config["target_column"]

    train_frame = load_split(args.input_dir / "train.csv")
    validation_frame = load_split(args.input_dir / "validation.csv")
    test_frame = load_split(args.input_dir / "test.csv")

    train_x = train_frame[feature_columns]
    train_y = train_frame[target_column].to_numpy()
    validation_x = validation_frame[feature_columns]
    validation_y = validation_frame[target_column].to_numpy()
    test_x = test_frame[feature_columns]
    test_y = test_frame[target_column].to_numpy()

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced_subsample",
        random_state=args.random_state,
        n_jobs=-1,
    )
    model.fit(train_x, train_y)

    validation_probabilities = model.predict_proba(validation_x)[:, 1]
    threshold_info = find_best_threshold(validation_y, validation_probabilities)
    threshold = threshold_info["threshold"]

    train_probabilities = model.predict_proba(train_x)[:, 1]
    test_probabilities = model.predict_proba(test_x)[:, 1]

    metrics_payload = {
        "dataset": {
            "name": DATASET_NAME,
            "page_url": DATASET_PAGE_URL,
            "doi": DATASET_DOI,
            "is_synthetic": True,
        },
        "model": {
            "family": "RandomForestClassifier",
            "hyperparameters": {
                "n_estimators": 150,
                "max_depth": 10,
                "min_samples_leaf": 5,
                "class_weight": "balanced_subsample",
                "random_state": args.random_state,
            },
            "feature_columns": feature_columns,
            "target_column": target_column,
        },
        "threshold_selection": {
            "strategy": "max_f1_on_validation",
            **threshold_info,
        },
        "metrics": {
            "train": evaluate_split("train", train_y, train_probabilities, threshold),
            "validation": evaluate_split(
                "validation", validation_y, validation_probabilities, threshold
            ),
            "test": evaluate_split("test", test_y, test_probabilities, threshold),
        },
    }

    model_path = args.artifacts_dir / "failure_model.joblib"
    metrics_path = args.artifacts_dir / "training_metrics.json"
    metadata_path = args.artifacts_dir / "model_metadata.json"

    joblib.dump(model, model_path)
    write_json(metrics_path, metrics_payload)
    write_json(
        metadata_path,
        {
            "model_name": "smart_factory_failure_model",
            "task": "binary_classification",
            "framework": "scikit-learn",
            "estimator": "RandomForestClassifier",
            "dataset_name": DATASET_NAME,
            "dataset_page_url": DATASET_PAGE_URL,
            "dataset_is_synthetic": True,
            "feature_columns": feature_columns,
            "feature_count": len(feature_columns),
            "target_column": target_column,
            "positive_class_label": 1,
            "input_tensor_name": "features",
            "probability_output_name": "probabilities",
            "label_output_name": "label",
            "decision_threshold": threshold,
            "hyperparameters": metrics_payload["model"]["hyperparameters"],
            "training_metrics_path": to_repo_relative(metrics_path),
            "sklearn_model_path": to_repo_relative(model_path),
            "onnx_model_path": to_repo_relative(args.artifacts_dir / "failure_model.onnx"),
        },
    )

    print(f"Trained model: {model_path}")
    print(f"Metrics: {metrics_path}")
    print(f"Metadata: {metadata_path}")
    print(f"Validation-selected threshold: {threshold:.6f}")
    print(
        "Test average precision: "
        f"{metrics_payload['metrics']['test']['average_precision']:.4f}"
    )
    print(f"Test F1 at threshold: {metrics_payload['metrics']['test']['f1_at_threshold']:.4f}")


if __name__ == "__main__":
    main()
