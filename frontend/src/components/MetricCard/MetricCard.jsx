import "./MetricCard.css";

export default function MetricCard({
    title,
    value,
    subtext,
    onClick,
    active = false,
}) {
    return (
        <button
            type="button"
            className={`mcard ${active ? "mcard--active" : ""}`}
            onClick={onClick}
        >
            <div className="mcard__title">{title}</div>
            <div className="mcard__value">{value}</div>
            {subtext && <div className="mcard__sub">{subtext}</div>}
        </button>
    );
}