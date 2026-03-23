import EmptyState from "./EmptyState";
import { formatDateTime, formatProbability, getSeverityTone } from "../utils/formatters";

function PredictionsTable({ predictions }) {
  if (predictions.length === 0) {
    return (
      <EmptyState
        title="No predictions to display"
        message="Change the time range, submit a reading, or load demo data to populate the table."
      />
    );
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Machine</th>
            <th>Probability</th>
            <th>Threshold</th>
            <th>Risk</th>
            <th>Decision</th>
          </tr>
        </thead>
        <tbody>
          {predictions.map((prediction) => (
            <tr key={prediction.id}>
              <td>{formatDateTime(prediction.created_at)}</td>
              <td>{prediction.machine_code}</td>
              <td>{formatProbability(prediction.failure_probability)}</td>
              <td>{formatProbability(prediction.threshold_used)}</td>
              <td>
                <span className={`badge ${getSeverityTone(prediction.risk_level)}`}>
                  {prediction.risk_level}
                </span>
              </td>
              <td>{prediction.predicted_failure ? "Flagged" : "Normal"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PredictionsTable;
