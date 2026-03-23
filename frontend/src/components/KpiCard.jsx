function KpiCard({ title, value, caption, tone = "default" }) {
  return (
    <article className={`kpi-card ${tone}`}>
      <p className="kpi-label">{title}</p>
      <strong className="kpi-value">{value}</strong>
      <span className="kpi-caption">{caption}</span>
    </article>
  );
}

export default KpiCard;
