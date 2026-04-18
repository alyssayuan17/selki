import { useState, useEffect } from "react";
import "./MetricCard.css";

export default function MetricCard({
    title,
    value,
    subtext,
    performanceMessage,
    onClick,
    active = false,
}) {
    const [displayValue, setDisplayValue] = useState(value);

    useEffect(() => {
        // Extract numeric value for animation
        const match = value?.toString().match(/^(\d+)%?$/);
        if (match) {
            const targetValue = parseInt(match[1], 10);
            const duration = 1500;
            const steps = 60;
            const increment = targetValue / steps;
            const stepDuration = duration / steps;
            let current = 0;

            const timer = setInterval(() => {
                current += increment;
                if (current >= targetValue) {
                    setDisplayValue(value);
                    clearInterval(timer);
                } else {
                    setDisplayValue(`${Math.round(current)}%`);
                }
            }, stepDuration);

            return () => clearInterval(timer);
        } else {
            setDisplayValue(value);
        }
    }, [value]);

    return (
        <button
            type="button"
            className={`mcard ${active ? "mcard--active" : ""}`}
            onClick={onClick}
        >
            <div className="mcard__title">{title}</div>
            <div className="mcard__value gradient-title">{displayValue}</div>
            {subtext && <div className="mcard__sub">{subtext}</div>}
            {performanceMessage && (
                <div className="mcard__performance">{performanceMessage}</div>
            )}
        </button>
    );
}