from __future__ import annotations


HIGH_RISK_RECORD = {
    "machine_code": "MILL-001",
    "machine_name": "Mill 001",
    "line_name": "Line A",
    "asset_type": "Milling Machine",
    "machine_status": "active",
    "source_udi": 70,
    "product_id": "L47249",
    "product_type": "L",
    "air_temperature_k": 298.9,
    "process_temperature_k": 309.0,
    "rotational_speed_rpm": 1410.0,
    "torque_nm": 65.7,
    "tool_wear_min": 191.0,
}

LOW_RISK_RECORD = {
    "machine_code": "PRESS-002",
    "machine_name": "Press 002",
    "line_name": "Line B",
    "asset_type": "Press",
    "machine_status": "active",
    "source_udi": 1,
    "product_id": "M14860",
    "product_type": "M",
    "air_temperature_k": 298.1,
    "process_temperature_k": 308.6,
    "rotational_speed_rpm": 1551.0,
    "torque_nm": 42.8,
    "tool_wear_min": 0.0,
}


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database_connected"] is True
    assert payload["model_loaded"] is True
    assert payload["model_name"] == "smart_factory_failure_model"


def test_predict_persists_machine_prediction_and_alert(client):
    response = client.post("/predict", json=HIGH_RISK_RECORD)
    assert response.status_code == 201

    payload = response.json()
    assert payload["sensor_reading"]["machine_code"] == HIGH_RISK_RECORD["machine_code"]
    assert payload["prediction"]["machine_code"] == HIGH_RISK_RECORD["machine_code"]
    assert payload["prediction"]["predicted_failure"] is True
    assert payload["prediction"]["failure_probability"] > 0.5
    assert payload["alert_id"] is not None

    machines = client.get("/machines").json()
    predictions = client.get("/predictions").json()
    alerts = client.get("/alerts").json()

    assert len(machines) == 1
    assert len(predictions) == 1
    assert len(alerts) == 1


def test_batch_ingestion_creates_predictions_for_multiple_records(client):
    response = client.post(
        "/sensor-readings/batch",
        json={"records": [HIGH_RISK_RECORD, LOW_RISK_RECORD]},
    )
    assert response.status_code == 201

    payload = response.json()
    assert payload["processed_records"] == 2
    assert payload["created_predictions"] == 2
    assert payload["created_alerts"] == 2
    assert len(payload["results"]) == 2

    predictions = client.get("/predictions").json()
    machine_codes = {item["machine_code"] for item in predictions}

    assert len(predictions) == 2
    assert machine_codes == {"MILL-001", "PRESS-002"}
