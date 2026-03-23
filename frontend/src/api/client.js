const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(
  /\/$/,
  ""
);

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}.`;

    try {
      const payload = await response.json();
      if (Array.isArray(payload.detail)) {
        detail = payload.detail
          .map((item) => item.msg || item.message || JSON.stringify(item))
          .join(" ");
      } else {
        detail = payload.detail || payload.message || detail;
      }
    } catch {
      // Ignore invalid JSON and fall back to a generic message.
    }

    throw new Error(detail);
  }

  return response.json();
}

export async function fetchDashboardData() {
  const limit = 250;
  const [health, machines, predictions, alerts] = await Promise.all([
    request("/health"),
    request(`/machines?limit=${limit}`),
    request(`/predictions?limit=${limit}`),
    request(`/alerts?limit=${limit}`),
  ]);

  return {
    health,
    machines,
    predictions,
    alerts,
  };
}

export async function submitSensorBatch(records) {
  return request("/sensor-readings/batch", {
    method: "POST",
    body: JSON.stringify({ records }),
  });
}

export { API_BASE_URL };
