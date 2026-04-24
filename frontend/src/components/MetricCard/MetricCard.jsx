import { useState, useEffect } from "react";
import "./MetricCard.css";

function scoreLevel(value) {
    const n = parseInt(value);
    if (isNaN(n)) return "na";
    if (n >= 75) return "excellent";
    if (n >= 50) return "good";
    if (n >= 30) return "needs";
    return "poor";
}

export default function MetricCard({
    title,
    value,
    subtext,
    performanceMessage,
    onClick,
    active = false,
}) {
    const [displayValue, setDisplayValue] = useState(value);
    const [barWidth, setBarWidth] = useState(0);

    const level = scoreLevel(value);

    useEffect(() => {
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
                    setBarWidth(targetValue);
                    clearInterval(timer);
                } else {
                    setDisplayValue(`${Math.round(current)}%`);
                    setBarWidth(Math.round(current));
                }
            }, stepDuration);

            return () => clearInterval(timer);
        } else {
            setDisplayValue(value);
            setBarWidth(0);
        }
    }, [value]);

    return (
        <button
            type="button"
            className={`mcard mcard--${level} ${active ? "mcard--active" : ""}`}
            data-score={isNaN(parseInt(value)) ? "" : parseInt(value)}
            onClick={onClick}
        >
            <div className="mcard__macbar">
                <span className="mcard__dot mcard__dot--red" />
                <span className="mcard__dot mcard__dot--yellow" />
                <span className="mcard__dot mcard__dot--green" />
            </div>
            <div className="mcard__title">{title}</div>
            <div className="mcard__value">{displayValue}</div>
            {subtext && <div className="mcard__sub">{subtext}</div>}
            {performanceMessage && (
                <div className="mcard__performance">{performanceMessage}</div>
            )}
            <div className="mcard__bar-track">
                <div className="mcard__bar" style={{ width: `${barWidth}%` }} />
            </div>
        </button>
    );
}
