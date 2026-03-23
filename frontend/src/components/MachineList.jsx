import EmptyState from "./EmptyState";
import { formatDateTime, formatProbability, getSeverityTone } from "../utils/formatters";

function MachineList({ machines, selectedMachineCode, onSelectMachine }) {
  if (machines.length === 0) {
    return (
      <EmptyState
        title="No machines available"
        message="Machine records will appear here once data is ingested or demo data is loaded."
      />
    );
  }

  return (
    <div className="machine-list">
      {machines.map((machine) => (
        <button
          className={`machine-row ${
            selectedMachineCode === machine.machine_code ? "selected" : ""
          }`}
          type="button"
          key={machine.machine_code}
          onClick={() =>
            onSelectMachine(
              selectedMachineCode === machine.machine_code ? "all" : machine.machine_code
            )
          }
        >
          <div className="machine-row-main">
            <div>
              <strong>{machine.machine_code}</strong>
              <p>{machine.machine_name || machine.asset_type || "Unnamed machine"}</p>
            </div>
            <span className={`badge ${getSeverityTone(machine.status)}`}>
              {machine.status}
            </span>
          </div>
          <div className="machine-row-stats">
            <span>{machine.line_name || "No line assigned"}</span>
            <span>{machine.predictionCount} predictions</span>
            <span>{machine.openAlertCount} open alerts</span>
            <span>Avg risk {formatProbability(machine.averageRisk)}</span>
            <span>
              {machine.lastPredictionAt
                ? formatDateTime(machine.lastPredictionAt)
                : "No predictions yet"}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}

export default MachineList;
