from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import onnxruntime as ort


@dataclass
class InferenceResult:
    failure_probability: float
    predicted_failure: bool
    decision_threshold: float
    raw_model_label: int
    feature_vector: list[float]
    feature_mapping: dict[str, float]


class OnnxInferenceRuntime:
    def __init__(
        self,
        model_path: Path,
        model_metadata_path: Path,
        preprocessing_config_path: Path,
    ) -> None:
        self.model_path = model_path
        self.model_metadata_path = model_metadata_path
        self.preprocessing_config_path = preprocessing_config_path

        if not self.model_path.exists():
            raise FileNotFoundError(f"Missing ONNX model artifact: {self.model_path}")
        if not self.model_metadata_path.exists():
            raise FileNotFoundError(f"Missing model metadata artifact: {self.model_metadata_path}")
        if not self.preprocessing_config_path.exists():
            raise FileNotFoundError(
                f"Missing preprocessing config artifact: {self.preprocessing_config_path}"
            )

        self.model_metadata = json.loads(self.model_metadata_path.read_text(encoding="utf-8"))
        self.preprocessing_config = json.loads(
            self.preprocessing_config_path.read_text(encoding="utf-8")
        )

        self.feature_columns = list(self.model_metadata["feature_columns"])
        self.numeric_feature_columns = list(self.preprocessing_config["numeric_feature_columns"])
        self.one_hot_feature_columns = list(self.preprocessing_config["one_hot_feature_columns"])
        self.type_categories = list(
            self.preprocessing_config["categorical_categories"][
                self.preprocessing_config["categorical_column"]
            ]
        )
        self.input_tensor_name = str(self.model_metadata["input_tensor_name"])
        self.probability_output_name = str(self.model_metadata["probability_output_name"])
        self.label_output_name = str(self.model_metadata["label_output_name"])
        self.positive_class_label = int(self.model_metadata["positive_class_label"])
        self.decision_threshold = float(self.model_metadata["decision_threshold"])
        self.model_name = str(self.model_metadata["model_name"])

        expected_feature_columns = list(self.preprocessing_config["model_feature_columns"])
        if self.feature_columns != expected_feature_columns:
            raise ValueError(
                "Model metadata feature order does not match preprocessing_config.json."
            )

        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )

    def _build_feature_mapping(self, payload: Mapping[str, Any]) -> dict[str, float]:
        product_type = str(payload.get("product_type") or payload.get("type") or "").upper()
        if product_type not in self.type_categories:
            raise ValueError(
                f"Unsupported product type '{product_type}'. Expected one of {self.type_categories}."
            )

        feature_mapping: dict[str, float] = {}
        for feature_name in self.feature_columns:
            if feature_name in self.one_hot_feature_columns:
                feature_mapping[feature_name] = (
                    1.0 if feature_name == f"type_{product_type}" else 0.0
                )
            elif feature_name in self.numeric_feature_columns:
                feature_mapping[feature_name] = float(payload[feature_name])
            else:
                raise ValueError(f"Unexpected feature in contract: {feature_name}")
        return feature_mapping

    def predict(self, payload: Mapping[str, Any]) -> InferenceResult:
        feature_mapping = self._build_feature_mapping(payload)
        feature_vector = [feature_mapping[name] for name in self.feature_columns]
        inputs = {self.input_tensor_name: np.asarray([feature_vector], dtype=np.float32)}
        raw_label, raw_probabilities = self.session.run(
            [self.label_output_name, self.probability_output_name],
            inputs,
        )
        positive_probability = float(np.asarray(raw_probabilities)[0][self.positive_class_label])
        predicted_failure = positive_probability >= self.decision_threshold

        return InferenceResult(
            failure_probability=positive_probability,
            predicted_failure=predicted_failure,
            decision_threshold=self.decision_threshold,
            raw_model_label=int(np.asarray(raw_label)[0]),
            feature_vector=feature_vector,
            feature_mapping=feature_mapping,
        )

    def describe(self) -> dict[str, object]:
        return {
            "runtime": ort.get_device(),
            "model_name": self.model_name,
            "model_path": str(self.model_path),
            "model_loaded": True,
            "feature_columns": self.feature_columns,
            "decision_threshold": self.decision_threshold,
        }
