import { useEffect, useState } from "react";
import AlertsPanel from "./components/AlertsPanel";
import EmptyState from "./components/EmptyState";
import IngestionPanel from "./components/IngestionPanel";
import KpiCard from "./components/KpiCard";
import MachineList from "./components/MachineList";
import PredictionDetail from "./components/PredictionDetail";
import PredictionsTable from "./components/PredictionsTable";
import SectionCard from "./components/SectionCard";
import StatusBanner from "./components/StatusBanner";
import TrendChart from "./components/TrendChart";
import { fetchDashboardData, submitSensorBatch } from "./api/client";
import { SAMPLE_DASHBOARD_DATA } from "./data/sampleData";
import {
  formatDateTime,
  formatProbability,
  formatRelativeWindowLabel,
} from "./utils/formatters";

const TIME_RANGE_OPTIONS = [
  { value: "24h", label: "Last 24 hours" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "all", label: "All activity" },
];

function getReferenceDate(predictions, alerts) {
  const timestamps = [...predictions, ...alerts]
    .map((item) => item.created_at)
    .filter(Boolean)
    .map((value) => new Date(value).getTime())
    .filter((value) => Number.isFinite(value));

  if (timestamps.length === 0) {
    return new Date();
  }

  return new Date(Math.max(...timestamps));
}

function withinTimeRange(value, range, referenceDate) {
  if (range === "all") {
    return true;
  }

  const ranges = {
    "24h": 24 * 60 * 60 * 1000,
    "7d": 7 * 24 * 60 * 60 * 1000,
    "30d": 30 * 24 * 60 * 60 * 1000,
  };
  const timestamp = new Date(value).getTime();
  const cutoff = referenceDate.getTime() - ranges[range];

  return Number.isFinite(timestamp) && timestamp >= cutoff;
}

function buildMachineRows(machines, predictions, alerts, machineFilter, timeRange, referenceDate) {
  const visibleMachines =
    machineFilter === "all"
      ? machines
      : machines.filter((machine) => machine.machine_code === machineFilter);

  return visibleMachines.map((machine) => {
    const machinePredictions = predictions.filter(
      (prediction) =>
        prediction.machine_code === machine.machine_code &&
        withinTimeRange(prediction.created_at, timeRange, referenceDate)
    );
    const machineAlerts = alerts.filter(
      (alert) =>
        alert.machine_code === machine.machine_code &&
        withinTimeRange(alert.created_at, timeRange, referenceDate)
    );
    const averageRisk =
      machinePredictions.length > 0
        ? machinePredictions.reduce(
            (sum, prediction) => sum + prediction.failure_probability,
            0
          ) / machinePredictions.length
        : 0;

    return {
      ...machine,
      predictionCount: machinePredictions.length,
      openAlertCount: machineAlerts.filter((alert) => alert.status === "open").length,
      averageRisk,
      lastPredictionAt: machinePredictions[0]?.created_at ?? null,
    };
  });
}

function App() {
  const [liveData, setLiveData] = useState({
    health: null,
    machines: [],
    predictions: [],
    alerts: [],
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [dataMode, setDataMode] = useState("live");
  const [machineFilter, setMachineFilter] = useState("all");
  const [timeRange, setTimeRange] = useState("7d");
  const [ingestionState, setIngestionState] = useState({
    busy: false,
    message: "",
    error: "",
  });

  async function loadLiveData(options = {}) {
    const { silent = false } = options;

    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const payload = await fetchDashboardData();
      setLiveData(payload);
      setDataMode("live");
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(error.message || "Unable to reach the backend.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadLiveData();
  }, []);

  async function handleBatchSubmit(records) {
    setIngestionState({ busy: true, message: "", error: "" });

    try {
      const response = await submitSensorBatch(records);
      await loadLiveData({ silent: true });
      setDataMode("live");
      setIngestionState({
        busy: false,
        message: `Stored ${response.created_predictions} predictions and ${response.created_alerts} alerts.`,
        error: "",
      });
      return response;
    } catch (error) {
      const message = error.message || "Unable to submit sensor records.";
      setIngestionState({ busy: false, message: "", error: message });
      throw error;
    }
  }

  const activeData = dataMode === "sample" ? SAMPLE_DASHBOARD_DATA : liveData;
  const health = activeData.health;
  const hasLiveRecords =
    liveData.machines.length > 0 ||
    liveData.predictions.length > 0 ||
    liveData.alerts.length > 0;

  const machinesSource =
    activeData.machines.length > 0
      ? activeData.machines
      : Array.from(
          new Map(
            activeData.predictions.map((prediction) => [
              prediction.machine_code,
              {
                id: prediction.machine_id,
                machine_code: prediction.machine_code,
                machine_name: prediction.machine_code,
                line_name: null,
                asset_type: null,
                status: "active",
                created_at: prediction.created_at,
              },
            ])
          ).values()
        );

  const predictions = [...activeData.predictions].sort(
    (left, right) => new Date(right.created_at) - new Date(left.created_at)
  );
  const alerts = [...activeData.alerts].sort(
    (left, right) => new Date(right.created_at) - new Date(left.created_at)
  );
  const referenceDate = getReferenceDate(predictions, alerts);

  const filteredPredictions = predictions.filter((prediction) => {
    const matchesMachine =
      machineFilter === "all" || prediction.machine_code === machineFilter;
    return (
      matchesMachine &&
      withinTimeRange(prediction.created_at, timeRange, referenceDate)
    );
  });

  const filteredAlerts = alerts.filter((alert) => {
    const matchesMachine =
      machineFilter === "all" || alert.machine_code === machineFilter;
    return matchesMachine && withinTimeRange(alert.created_at, timeRange, referenceDate);
  });
  const highRiskAlerts = filteredAlerts.filter(
    (alert) => alert.severity === "high" || alert.severity === "critical"
  );

  const machineRows = buildMachineRows(
    machinesSource,
    predictions,
    alerts,
    machineFilter,
    timeRange,
    referenceDate
  );
  const latestPrediction = filteredPredictions[0] || null;
  const trendPoints = [...filteredPredictions]
    .slice(0, 12)
    .reverse()
    .map((prediction, index) => ({
      id: prediction.id,
      label: prediction.machine_code,
      value: prediction.failure_probability,
      created_at: prediction.created_at,
      index,
      riskLevel: prediction.risk_level,
    }));

  const totalMachines = machineRows.length;
  const recentPredictionsCount = filteredPredictions.length;
  const activeHighRiskAlerts = filteredAlerts.filter(
    (alert) =>
      alert.status === "open" &&
      (alert.severity === "high" || alert.severity === "critical")
  ).length;
  const averageRiskScore =
    filteredPredictions.length > 0
      ? filteredPredictions.reduce(
          (sum, prediction) => sum + prediction.failure_probability,
          0
        ) / filteredPredictions.length
      : 0;

  return (
    <main className="app-shell">
      <header className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Smart Factory Monitoring</p>
          <h1>Predictive Maintenance Dashboard</h1>
          <p className="subtitle">
            React dashboard connected to the FastAPI service for machine health,
            failure-risk predictions, alert review, and sensor ingestion.
          </p>
          <div className="hero-meta">
            <span className={`status-pill ${dataMode === "sample" ? "sample" : "live"}`}>
              {dataMode === "sample" ? "Sample Preview" : "Live API"}
            </span>
            <span className="hero-detail">
              {health?.model_name ? `Model: ${health.model_name}` : "Model metadata unavailable"}
            </span>
            <span className="hero-detail">
              {health?.decision_threshold != null
                ? `Threshold: ${formatProbability(health.decision_threshold)}`
                : "Threshold unavailable"}
            </span>
          </div>
        </div>

        <div className="hero-actions">
          <button
            className="button secondary"
            type="button"
            onClick={() => loadLiveData({ silent: true })}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "Refresh live data"}
          </button>
          {dataMode === "sample" ? (
            <button
              className="button"
              type="button"
              onClick={() => loadLiveData({ silent: true })}
            >
              Return to live API
            </button>
          ) : (
            <button
              className="button ghost"
              type="button"
              onClick={() => setDataMode("sample")}
            >
              Open sample preview
            </button>
          )}
        </div>
      </header>

      {errorMessage && dataMode === "live" ? (
        <StatusBanner
          tone="error"
          title="Live backend unavailable"
          message={`${errorMessage} You can still explore the sample preview while the API is offline.`}
          actionLabel="Open sample preview"
          onAction={() => setDataMode("sample")}
        />
      ) : null}

      {dataMode === "sample" ? (
        <StatusBanner
          tone="info"
          title="Sample preview mode"
          message="This view uses a static sample dataset. Use Refresh live data to switch back to the backend."
        />
      ) : null}

      {loading ? (
        <StatusBanner
          tone="info"
          title="Loading dashboard data"
          message="Fetching machine inventory, predictions, alerts, and backend health."
        />
      ) : null}

      {!loading && !hasLiveRecords && dataMode === "live" ? (
        <StatusBanner
          tone="warning"
          title="No live records yet"
          message="The backend is healthy, but there is no prediction history yet. Use quick demo data or submit a sensor reading below."
          actionLabel="Preview sample dashboard"
          onAction={() => setDataMode("sample")}
        />
      ) : null}

      <section className="toolbar">
        <label className="field-inline" htmlFor="machine-filter">
          <span>Machine</span>
          <select
            id="machine-filter"
            value={machineFilter}
            onChange={(event) => setMachineFilter(event.target.value)}
          >
            <option value="all">All machines</option>
            {machinesSource.map((machine) => (
              <option key={machine.machine_code} value={machine.machine_code}>
                {machine.machine_code}
              </option>
            ))}
          </select>
        </label>

        <label className="field-inline" htmlFor="time-filter">
          <span>Time range</span>
          <select
            id="time-filter"
            value={timeRange}
            onChange={(event) => setTimeRange(event.target.value)}
          >
            {TIME_RANGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <div className="toolbar-note">
          Showing {formatRelativeWindowLabel(timeRange)} relative to{" "}
          {formatDateTime(referenceDate.toISOString())}
        </div>
      </section>

      <section className="kpi-grid">
        <KpiCard
          title="Total machines"
          value={String(totalMachines)}
          caption="Machines in the current dashboard scope"
        />
        <KpiCard
          title="Recent predictions"
          value={String(recentPredictionsCount)}
          caption="Predictions stored in the selected time window"
        />
        <KpiCard
          title="High-risk alerts"
          value={String(activeHighRiskAlerts)}
          caption="Open alerts with high or critical severity"
          tone={activeHighRiskAlerts > 0 ? "warning" : "default"}
        />
        <KpiCard
          title="Average risk score"
          value={formatProbability(averageRiskScore)}
          caption="Average failure probability across filtered predictions"
          tone={averageRiskScore >= 0.5 ? "danger" : "default"}
        />
      </section>

      <section className="content-grid">
        <SectionCard
          title="High-Risk Alerts"
          subtitle="Recent alert records from the backend"
          className="span-two-thirds"
        >
          <AlertsPanel alerts={highRiskAlerts.slice(0, 6)} />
        </SectionCard>

        <SectionCard
          title="Latest Prediction"
          subtitle="Most recent prediction in the filtered window"
        >
          {latestPrediction ? (
            <PredictionDetail prediction={latestPrediction} />
          ) : (
            <EmptyState
              title="No prediction selected"
              message="Submit a sensor record or load demo data to populate the recent prediction view."
            />
          )}
        </SectionCard>

        <SectionCard
          title="Recent Risk Trend"
          subtitle="Last 12 filtered predictions"
          className="span-two-thirds"
        >
          <TrendChart points={trendPoints} />
        </SectionCard>

        <SectionCard title="Machine List" subtitle="Machine status and recent activity">
          <MachineList
            machines={machineRows}
            selectedMachineCode={machineFilter}
            onSelectMachine={setMachineFilter}
          />
        </SectionCard>
      </section>

      <SectionCard
        title="Recent Predictions"
        subtitle="Stored prediction rows for the selected window"
      >
        <PredictionsTable predictions={filteredPredictions.slice(0, 12)} />
      </SectionCard>

      <SectionCard
        title="Sensor Ingestion"
        subtitle="Submit one reading or a pasted batch to the FastAPI backend"
      >
        <IngestionPanel
          machines={machinesSource}
          onSubmitBatch={handleBatchSubmit}
          busy={ingestionState.busy}
          statusMessage={ingestionState.message}
          errorMessage={ingestionState.error}
        />
      </SectionCard>
    </main>
  );
}

export default App;
