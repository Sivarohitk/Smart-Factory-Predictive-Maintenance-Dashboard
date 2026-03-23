export function formatProbability(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return "--";
  }

  return `${Math.round(Number(value) * 100)}%`;
}

export function formatDateTime(value) {
  if (!value) {
    return "--";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatRelativeWindowLabel(value) {
  const labels = {
    "24h": "the last 24 hours",
    "7d": "the last 7 days",
    "30d": "the last 30 days",
    all: "all available history",
  };

  return labels[value] || "the selected range";
}

export function getSeverityTone(value) {
  const tone = {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "low",
    open: "open",
    acknowledged: "muted",
    active: "open",
    maintenance: "medium",
    offline: "critical",
  };

  return tone[value] || "default";
}

export function toDatetimeLocalValue(value) {
  const date = value ? new Date(value) : new Date();
  const offset = date.getTimezoneOffset();
  const localTime = new Date(date.getTime() - offset * 60000);
  return localTime.toISOString().slice(0, 16);
}
