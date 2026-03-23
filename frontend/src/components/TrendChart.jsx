import EmptyState from "./EmptyState";
import { formatDateTime, formatProbability } from "../utils/formatters";

function TrendChart({ points }) {
  if (points.length === 0) {
    return (
      <EmptyState
        title="No trend data available"
        message="Trend lines will appear when prediction history exists in the selected window."
      />
    );
  }

  const width = 640;
  const height = 220;
  const padding = 24;

  const coordinates = points.map((point, index) => {
    const x =
      points.length === 1
        ? width / 2
        : padding + (index * (width - padding * 2)) / (points.length - 1);
    const y = padding + (1 - point.value) * (height - padding * 2);
    return { ...point, x, y };
  });

  const polyline = coordinates.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <div className="trend-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Recent risk trend chart"
      >
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} />
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
        />
        <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} />
        <polyline points={polyline} fill="none" strokeLinecap="round" strokeWidth="3" />
        {coordinates.map((point) => (
          <circle key={point.id} cx={point.x} cy={point.y} r="4.5" />
        ))}
      </svg>
      <div className="trend-footer">
        <div>
          <strong>{formatProbability(points[0].value)}</strong>
          <span>{formatDateTime(points[0].created_at)}</span>
        </div>
        <div className="trend-center-note">Recent prediction probabilities</div>
        <div>
          <strong>{formatProbability(points[points.length - 1].value)}</strong>
          <span>{formatDateTime(points[points.length - 1].created_at)}</span>
        </div>
      </div>
    </div>
  );
}

export default TrendChart;
