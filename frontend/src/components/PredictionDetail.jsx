import EmptyState from "./EmptyState";
import { formatDateTime, formatProbability, getSeverityTone } from "../utils/formatters";

function PredictionDetail({ prediction }) {
  if (!prediction) {
    return (
      <EmptyState
        title="No prediction selected"
        message="Prediction details will appear here once data is available."
      />
    );
  }

  return (
    <div className="detail-stack">
      <div className="detail-header">
        <div>
          <strong>{prediction.machine_code}</strong>
          <p>Prediction #{prediction.id}</p>
        </div>
        <span className={`badge ${getSeverityTone(prediction.risk_level)}`}>
          {prediction.risk_level}
        </span>
      </div>

      <div className="detail-grid">
        <div>
          <span className="detail-label">Failure probability</span>
          <strong>{formatProbability(prediction.failure_probability)}</strong>
        </div>
        <div>
          <span className="detail-label">Threshold used</span>
          <strong>{formatProbability(prediction.threshold_used)}</strong>
        </div>
        <div>
          <span className="detail-label">Decision</span>
          <strong>{prediction.predicted_failure ? "Flagged" : "Normal"}</strong>
        </div>
        <div>
          <span className="detail-label">Model</span>
          <strong>{prediction.model_name}</strong>
        </div>
      </div>

      <div className="detail-footer">
        <span>Recorded {formatDateTime(prediction.created_at)}</span>
      </div>
    </div>
  );
}

export default PredictionDetail;
