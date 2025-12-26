export default function MetricDetailCard({ title, children }) {
    return (
        <section className="metric-detail-card">
        <div className="metric-detail-card__header">{title}</div>
        <div className="metric-detail-card__body">{children}</div>
        </section>
    );
}