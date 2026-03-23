from __future__ import annotations

from app.models import Alert, Machine, Prediction
from app.schemas.common import RiskLevel


def derive_risk_level(probability: float, decision_threshold: float) -> RiskLevel:
    if probability >= 0.85:
        return RiskLevel.critical
    if probability >= 0.70:
        return RiskLevel.high
    if probability >= decision_threshold:
        return RiskLevel.medium
    return RiskLevel.low


def build_alert(
    machine: Machine,
    prediction: Prediction,
    probability: float,
    alert_threshold: float,
    decision_threshold: float,
) -> Alert | None:
    if probability < alert_threshold:
        return None

    severity = derive_risk_level(probability, decision_threshold)
    message = (
        f"Machine {machine.machine_code} exceeded the failure-risk alert threshold "
        f"with probability {probability:.2%}."
    )
    return Alert(
        machine_id=machine.id,
        prediction_id=prediction.id,
        severity=severity.value,
        status="open",
        message=message,
    )
