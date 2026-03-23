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
    "machine_code": "LATHE-002",
    "machine_name": "Lathe 002",
    "line_name": "Line A",
    "asset_type": "CNC Lathe",
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


def test_batch_ingestion_updates_dashboard_endpoints(client_with_runtime_threshold):
    health_response = client_with_runtime_threshold.get("/health")
    assert health_response.status_code == 200

    health_payload = health_response.json()
    assert health_payload["database_connected"] is True
    assert health_payload["model_loaded"] is True
    assert health_payload["decision_threshold"] > 0.5

    ingest_response = client_with_runtime_threshold.post(
        "/sensor-readings/batch",
        json={"records": [HIGH_RISK_RECORD, LOW_RISK_RECORD]},
    )
    assert ingest_response.status_code == 201

    ingest_payload = ingest_response.json()
    assert ingest_payload["processed_records"] == 2
    assert ingest_payload["created_predictions"] == 2
    assert ingest_payload["created_alerts"] == 1
    assert len(ingest_payload["results"]) == 2

    high_risk_result, low_risk_result = ingest_payload["results"]
    assert high_risk_result["prediction"]["machine_code"] == HIGH_RISK_RECORD["machine_code"]
    assert high_risk_result["prediction"]["predicted_failure"] is True
    assert high_risk_result["prediction"]["risk_level"] in {"high", "critical"}
    assert high_risk_result["alert_id"] is not None

    assert low_risk_result["prediction"]["machine_code"] == LOW_RISK_RECORD["machine_code"]
    assert low_risk_result["prediction"]["predicted_failure"] is False
    assert low_risk_result["prediction"]["risk_level"] == "low"
    assert low_risk_result["alert_id"] is None

    machines = client_with_runtime_threshold.get("/machines").json()
    predictions = client_with_runtime_threshold.get("/predictions").json()
    alerts = client_with_runtime_threshold.get("/alerts").json()

    assert {machine["machine_code"] for machine in machines} == {"MILL-001", "LATHE-002"}
    assert len(predictions) == 2
    assert len(alerts) == 1

    prediction = predictions[0]
    assert set(
        [
            "machine_code",
            "failure_probability",
            "threshold_used",
            "predicted_failure",
            "risk_level",
            "created_at",
        ]
    ).issubset(prediction.keys())

    alert = alerts[0]
    assert alert["machine_code"] == HIGH_RISK_RECORD["machine_code"]
    assert alert["status"] == "open"
    assert alert["severity"] in {"high", "critical"}
    assert "exceeded the failure-risk alert threshold" in alert["message"]
