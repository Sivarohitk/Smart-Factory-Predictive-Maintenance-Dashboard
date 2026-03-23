import EmptyState from "./EmptyState";
import { formatDateTime, getSeverityTone } from "../utils/formatters";

function AlertsPanel({ alerts }) {
  if (alerts.length === 0) {
    return (
      <EmptyState
        title="No high-risk alerts in view"
        message="This time range does not contain any high or critical alerts."
      />
    );
  }

  return (
    <div className="alerts-list">
      {alerts.map((alert) => (
        <article className="alert-item" key={alert.id}>
          <div className="alert-heading">
            <div>
              <strong>{alert.machine_code}</strong>
              <p>{alert.message}</p>
            </div>
            <div className="alert-meta">
              <span className={`badge ${getSeverityTone(alert.severity)}`}>
                {alert.severity}
              </span>
              <span className={`badge ${getSeverityTone(alert.status)}`}>
                {alert.status}
              </span>
            </div>
          </div>
          <div className="alert-footer">
            <span>Prediction #{alert.prediction_id}</span>
            <span>{formatDateTime(alert.created_at)}</span>
          </div>
        </article>
      ))}
    </div>
  );
}

export default AlertsPanel;
