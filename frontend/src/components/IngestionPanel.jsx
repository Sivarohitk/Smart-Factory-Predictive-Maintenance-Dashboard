import { useState } from "react";
import { toDatetimeLocalValue } from "../utils/formatters";

const SAFE_EXAMPLE = {
  machine_code: "LATHE-002",
  machine_name: "Lathe 002",
  line_name: "Line A",
  asset_type: "CNC Lathe",
  machine_status: "active",
  source_udi: 1,
  product_id: "M14860",
  product_type: "M",
  captured_at: toDatetimeLocalValue(),
  air_temperature_k: "298.1",
  process_temperature_k: "308.6",
  rotational_speed_rpm: "1551",
  torque_nm: "42.8",
  tool_wear_min: "0",
};

const HIGH_RISK_EXAMPLE = {
  machine_code: "MILL-001",
  machine_name: "Mill 001",
  line_name: "Line A",
  asset_type: "Milling Machine",
  machine_status: "active",
  source_udi: 70,
  product_id: "L47249",
  product_type: "L",
  captured_at: toDatetimeLocalValue(),
  air_temperature_k: "298.9",
  process_temperature_k: "309.0",
  rotational_speed_rpm: "1410",
  torque_nm: "65.7",
  tool_wear_min: "191",
};

function buildRecordFromForm(formState) {
  return {
    machine_code: formState.machine_code.trim(),
    machine_name: formState.machine_name.trim() || null,
    line_name: formState.line_name.trim() || null,
    asset_type: formState.asset_type.trim() || null,
    machine_status: formState.machine_status,
    source_udi: formState.source_udi ? Number(formState.source_udi) : null,
    product_id: formState.product_id.trim() || null,
    product_type: formState.product_type,
    captured_at: new Date(formState.captured_at).toISOString(),
    air_temperature_k: Number(formState.air_temperature_k),
    process_temperature_k: Number(formState.process_temperature_k),
    rotational_speed_rpm: Number(formState.rotational_speed_rpm),
    torque_nm: Number(formState.torque_nm),
    tool_wear_min: Number(formState.tool_wear_min),
  };
}

function IngestionPanel({
  machines,
  onSubmitBatch,
  busy,
  statusMessage,
  errorMessage,
}) {
  const [formState, setFormState] = useState(HIGH_RISK_EXAMPLE);
  const [batchJson, setBatchJson] = useState("");
  const [localError, setLocalError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setFormState((current) => ({ ...current, [name]: value }));
  }

  async function handleSingleSubmit(event) {
    event.preventDefault();
    setLocalError("");

    try {
      await onSubmitBatch([buildRecordFromForm(formState)]);
    } catch (error) {
      setLocalError(error.message || "Unable to submit the form payload.");
    }
  }

  async function handleBatchSubmit() {
    setLocalError("");

    try {
      const parsed = JSON.parse(batchJson);
      const records = Array.isArray(parsed) ? parsed : parsed.records;

      if (!Array.isArray(records) || records.length === 0) {
        throw new Error("Batch JSON must be an array or an object with a records array.");
      }

      await onSubmitBatch(records);
      setBatchJson("");
    } catch (error) {
      setLocalError(error.message || "Unable to submit the JSON batch payload.");
    }
  }

  return (
    <div className="ingestion-grid">
      <form className="form-grid" onSubmit={handleSingleSubmit}>
        <div className="form-toolbar">
          <strong>Single reading</strong>
          <div className="button-row">
            <button
              className="button secondary"
              type="button"
              onClick={() => setFormState(SAFE_EXAMPLE)}
            >
              Load safe example
            </button>
            <button
              className="button secondary"
              type="button"
              onClick={() => setFormState(HIGH_RISK_EXAMPLE)}
            >
              Load high-risk example
            </button>
          </div>
        </div>

        <label>
          <span>Machine code</span>
          <input
            list="machine-codes"
            name="machine_code"
            value={formState.machine_code}
            onChange={handleChange}
            required
          />
          <datalist id="machine-codes">
            {machines.map((machine) => (
              <option key={machine.machine_code} value={machine.machine_code} />
            ))}
          </datalist>
        </label>
        <label>
          <span>Machine name</span>
          <input name="machine_name" value={formState.machine_name} onChange={handleChange} />
        </label>
        <label>
          <span>Line name</span>
          <input name="line_name" value={formState.line_name} onChange={handleChange} />
        </label>
        <label>
          <span>Asset type</span>
          <input name="asset_type" value={formState.asset_type} onChange={handleChange} />
        </label>
        <label>
          <span>Machine status</span>
          <select
            name="machine_status"
            value={formState.machine_status}
            onChange={handleChange}
          >
            <option value="active">active</option>
            <option value="maintenance">maintenance</option>
            <option value="offline">offline</option>
          </select>
        </label>
        <label>
          <span>Product type</span>
          <select
            name="product_type"
            value={formState.product_type}
            onChange={handleChange}
          >
            <option value="L">L</option>
            <option value="M">M</option>
            <option value="H">H</option>
          </select>
        </label>
        <label>
          <span>Captured at</span>
          <input
            type="datetime-local"
            name="captured_at"
            value={formState.captured_at}
            onChange={handleChange}
            required
          />
        </label>
        <label>
          <span>Source UDI</span>
          <input name="source_udi" value={formState.source_udi} onChange={handleChange} />
        </label>
        <label>
          <span>Product ID</span>
          <input name="product_id" value={formState.product_id} onChange={handleChange} />
        </label>
        <label>
          <span>Air temperature (K)</span>
          <input
            type="number"
            step="0.1"
            name="air_temperature_k"
            value={formState.air_temperature_k}
            onChange={handleChange}
            required
          />
        </label>
        <label>
          <span>Process temperature (K)</span>
          <input
            type="number"
            step="0.1"
            name="process_temperature_k"
            value={formState.process_temperature_k}
            onChange={handleChange}
            required
          />
        </label>
        <label>
          <span>Rotational speed (rpm)</span>
          <input
            type="number"
            step="0.1"
            name="rotational_speed_rpm"
            value={formState.rotational_speed_rpm}
            onChange={handleChange}
            required
          />
        </label>
        <label>
          <span>Torque (Nm)</span>
          <input
            type="number"
            step="0.1"
            name="torque_nm"
            value={formState.torque_nm}
            onChange={handleChange}
            required
          />
        </label>
        <label>
          <span>Tool wear (min)</span>
          <input
            type="number"
            step="1"
            name="tool_wear_min"
            value={formState.tool_wear_min}
            onChange={handleChange}
            required
          />
        </label>

        <div className="form-actions">
          <button className="button" type="submit" disabled={busy}>
            {busy ? "Submitting..." : "Submit single reading"}
          </button>
        </div>
      </form>

      <div className="batch-panel">
        <div className="form-toolbar">
          <strong>Batch JSON upload</strong>
          <p>
            Paste an array of sensor reading objects or{" "}
            <code>{'{ "records": [...] }'}</code>.
          </p>
        </div>
        <textarea
          value={batchJson}
          onChange={(event) => setBatchJson(event.target.value)}
          placeholder='[{"machine_code":"MILL-001","product_type":"L","captured_at":"2026-03-22T16:00:00Z","air_temperature_k":298.9,"process_temperature_k":309.0,"rotational_speed_rpm":1410,"torque_nm":65.7,"tool_wear_min":191}]'
          rows={12}
        />
        <div className="form-actions">
          <button
            className="button secondary"
            type="button"
            onClick={handleBatchSubmit}
            disabled={busy || !batchJson.trim()}
          >
            {busy ? "Submitting..." : "Submit JSON batch"}
          </button>
        </div>
        <div className="ingestion-notes">
          <p>Live API only: this panel posts to `/sensor-readings/batch`.</p>
          {statusMessage ? <p className="feedback success">{statusMessage}</p> : null}
          {errorMessage || localError ? (
            <p className="feedback error">{localError || errorMessage}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default IngestionPanel;
