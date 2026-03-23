function StatusBanner({ title, message, tone = "info", actionLabel, onAction }) {
  return (
    <div className={`status-banner ${tone}`}>
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
      </div>
      {actionLabel && onAction ? (
        <button className="button secondary" type="button" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}

export default StatusBanner;
