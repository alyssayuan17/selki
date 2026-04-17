import MetricCard from "../MetricCard/MetricCard";
import "./MetricsGrid.css";

export default function MetricsGrid({ metrics, selectedMetricId, onMetricClick }) {
    return (
        <div className="metrics-grid">
            {metrics.map((m) => (
                <MetricCard
                    key={m.id}
                    title={m.label}
                    value={m.value}
                    subtext={m.subtext}
                    performanceMessage={m.performanceMessage}
                    active={m.id === selectedMetricId}
                    onClick={() => onMetricClick?.(m)}
                />
            ))}
        </div>
    );
}