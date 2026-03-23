from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from common import (
    ARTIFACTS_DIR,
    DATASET_DOI,
    DATASET_LICENSE,
    DATASET_NAME,
    DATASET_PAGE_URL,
    DATASET_URL,
    DEFAULT_RANDOM_STATE,
    DEFAULT_TEST_SIZE,
    DEFAULT_VAL_SIZE,
    IDENTIFIER_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    ONE_HOT_FEATURE_COLUMNS,
    PROCESSED_DATA_DIR,
    RAW_CSV_NAME,
    RAW_DATA_DIR,
    RAW_TO_CANONICAL_COLUMNS,
    TARGET_COLUMN,
    TYPE_CATEGORIES,
    ensure_directories,
    to_repo_relative,
    write_json,
)


def load_raw_dataframe(csv_path: Path) -> pd.DataFrame:
    dataframe = pd.read_csv(csv_path)
    missing_columns = [column for column in RAW_TO_CANONICAL_COLUMNS if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"Missing expected raw columns: {missing_columns}")

    dataframe = dataframe.rename(columns=RAW_TO_CANONICAL_COLUMNS)
    return dataframe[list(RAW_TO_CANONICAL_COLUMNS.values())]


def build_feature_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    working = dataframe.copy()
    working["type"] = pd.Categorical(working["type"], categories=TYPE_CATEGORIES)
    type_dummies = pd.get_dummies(working["type"], prefix="type")
    type_dummies = type_dummies.reindex(columns=ONE_HOT_FEATURE_COLUMNS, fill_value=0)
    type_dummies = type_dummies.astype("int64")

    model_frame = pd.concat(
        [
            working[IDENTIFIER_COLUMNS],
            type_dummies,
            working[NUMERIC_FEATURE_COLUMNS],
            working[[TARGET_COLUMN]],
        ],
        axis=1,
    )
    return model_frame


def save_split(dataframe: pd.DataFrame, output_path: Path) -> None:
    dataframe.to_csv(output_path, index=False)


def class_distribution(series: pd.Series) -> dict[str, float | int]:
    positive_count = int(series.sum())
    total_count = int(series.shape[0])
    return {
        "rows": total_count,
        "positive_count": positive_count,
        "positive_rate": round(positive_count / total_count, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preprocess the AI4I dataset into train/validation/test CSV files."
    )
    parser.add_argument(
        "--raw-csv",
        type=Path,
        default=RAW_DATA_DIR / RAW_CSV_NAME,
        help="Path to the downloaded raw CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROCESSED_DATA_DIR,
        help="Directory for processed train/validation/test CSV files.",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=ARTIFACTS_DIR,
        help="Directory for preprocessing metadata artifacts.",
    )
    parser.add_argument(
        "--val-size",
        type=float,
        default=DEFAULT_VAL_SIZE,
        help="Fraction of full dataset reserved for validation.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=DEFAULT_TEST_SIZE,
        help="Fraction of full dataset reserved for testing.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=DEFAULT_RANDOM_STATE,
        help="Random seed for reproducible splits.",
    )
    args = parser.parse_args()

    if args.val_size + args.test_size >= 1.0:
        raise ValueError("Validation size plus test size must be less than 1.0.")

    ensure_directories()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.artifacts_dir.mkdir(parents=True, exist_ok=True)

    raw_dataframe = load_raw_dataframe(args.raw_csv)
    model_frame = build_feature_frame(raw_dataframe)

    train_frame, temp_frame = train_test_split(
        model_frame,
        test_size=args.val_size + args.test_size,
        stratify=model_frame[TARGET_COLUMN],
        random_state=args.random_state,
    )
    validation_fraction_of_temp = args.val_size / (args.val_size + args.test_size)
    validation_frame, test_frame = train_test_split(
        temp_frame,
        test_size=1.0 - validation_fraction_of_temp,
        stratify=temp_frame[TARGET_COLUMN],
        random_state=args.random_state,
    )

    split_paths = {
        "train": args.output_dir / "train.csv",
        "validation": args.output_dir / "validation.csv",
        "test": args.output_dir / "test.csv",
    }
    save_split(train_frame, split_paths["train"])
    save_split(validation_frame, split_paths["validation"])
    save_split(test_frame, split_paths["test"])

    preprocessing_payload = {
        "dataset": {
            "name": DATASET_NAME,
            "download_url": DATASET_URL,
            "page_url": DATASET_PAGE_URL,
            "doi": DATASET_DOI,
            "license": DATASET_LICENSE,
            "is_synthetic": True,
        },
        "source_columns": RAW_TO_CANONICAL_COLUMNS,
        "categorical_column": "type",
        "categorical_categories": {"type": TYPE_CATEGORIES},
        "identifier_columns": IDENTIFIER_COLUMNS,
        "numeric_feature_columns": NUMERIC_FEATURE_COLUMNS,
        "one_hot_feature_columns": ONE_HOT_FEATURE_COLUMNS,
        "model_feature_columns": MODEL_FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "split_config": {
            "validation_size": args.val_size,
            "test_size": args.test_size,
            "random_state": args.random_state,
        },
        "class_balance": {
            "full": class_distribution(model_frame[TARGET_COLUMN]),
            "train": class_distribution(train_frame[TARGET_COLUMN]),
            "validation": class_distribution(validation_frame[TARGET_COLUMN]),
            "test": class_distribution(test_frame[TARGET_COLUMN]),
        },
        "output_files": {name: to_repo_relative(path) for name, path in split_paths.items()},
    }
    metadata_path = args.artifacts_dir / "preprocessing_config.json"
    write_json(metadata_path, preprocessing_payload)

    print("Preprocessing complete.")
    for split_name, split_path in split_paths.items():
        print(f"{split_name}: {split_path}")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    main()
