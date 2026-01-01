import MetricCard from "../MetricCard/MetricCard";
import "./MetricsGrid.css";

export default function MetricsGrid({ metrics, onMetricClick }) {
    return (
        <div className="metrics-grid">
            {metrics.map((m) => (
                <MetricCard
                    key={m.id}
                    title={m.label}
                    value={m.value}
                    subtext={m.subtext}
                    onClick={() => onMetricClick?.(m)}
                />
            ))}
        </div>
    );
}