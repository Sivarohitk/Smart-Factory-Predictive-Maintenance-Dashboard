function SectionCard({ title, subtitle, children, className = "" }) {
  return (
    <section className={`section-card ${className}`.trim()}>
      <header className="section-header">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </header>
      <div className="section-body">{children}</div>
    </section>
  );
}

export default SectionCard;
