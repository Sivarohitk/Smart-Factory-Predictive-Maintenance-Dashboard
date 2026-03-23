# ML Pipeline

This directory contains a CLI-only machine-learning pipeline for the Smart Factory Predictive Maintenance Dashboard.

## Dataset

- Source: UCI Machine Learning Repository, AI4I 2020 Predictive Maintenance Dataset
- Dataset page: https://archive.ics.uci.edu/dataset/601/ai4i
- Direct download used by the CLI: https://archive.ics.uci.edu/static/public/601/ai4i%2B2020%2Bpredictive%2Bmaintenance%2Bdataset.zip
- DOI: `10.24432/C5HS5C`
- License: `CC BY 4.0`
- Important note: this dataset is synthetic. That should be stated clearly anywhere the project describes the training source.

## Modeling Approach

- Task: binary classification of `machine_failure`
- Input features:
  - `type_L`
  - `type_M`
  - `type_H`
  - `air_temperature_k`
  - `process_temperature_k`
  - `rotational_speed_rpm`
  - `torque_nm`
  - `tool_wear_min`
- Model: `RandomForestClassifier`
- Why this model:
  - lightweight and fast for local CPU execution
  - works well on small tabular data
  - exportable to ONNX with `skl2onnx`

## Scripts

- `ml/scripts/download_data.py`: downloads the official UCI zip and extracts the raw CSV
- `ml/scripts/preprocess.py`: normalizes columns, one-hot encodes `type`, creates train/validation/test splits, and writes preprocessing metadata
- `ml/scripts/train.py`: trains the classifier, evaluates on imbalanced metrics, and saves training metadata
- `ml/scripts/export_onnx.py`: exports the trained sklearn model to `ONNX`
- `ml/scripts/test_onnx_inference.py`: runs a small ONNX Runtime smoke test against processed test rows

## Run From CLI

Install dependencies:

```bash
python -m pip install -r ml/requirements.txt
```

Download raw data:

```bash
python ml/scripts/download_data.py
```

Preprocess into train/validation/test splits:

```bash
python ml/scripts/preprocess.py
```

Train the sklearn model and save metrics:

```bash
python ml/scripts/train.py
```

Export the trained model to ONNX:

```bash
python ml/scripts/export_onnx.py
```

Run the ONNX Runtime smoke test:

```bash
python ml/scripts/test_onnx_inference.py
```

## Produced Artifacts

- `ml/artifacts/preprocessing_config.json`
- `ml/artifacts/failure_model.joblib`
- `ml/artifacts/training_metrics.json`
- `ml/artifacts/model_metadata.json`
- `ml/artifacts/failure_model.onnx`

The backend should later feed ONNX inputs using the exact feature order listed above.

