import { useState, useEffect } from "react";
import "./ScoreBadge.css";

export default function ScoreBadge({score = 0, initial = "R"}) {
    const [displayScore, setDisplayScore] = useState(0);

    useEffect(() => {
        const duration = 1500;
        const steps = 60;
        const increment = score / steps;
        const stepDuration = duration / steps;
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= score) {
                setDisplayScore(Math.round(score));
                clearInterval(timer);
            } else {
                setDisplayScore(Math.round(current));
            }
        }, stepDuration);

        return () => clearInterval(timer);
    }, [score]);

    return (
        <div className="score-badge">
            <div className="score-badge__score">
                <span className="score-badge__eyebrow">your result</span>
                <span className="score-badge__label">Overall score</span>
                <span className="score-badge__number">{displayScore}%</span>
                <div className="score-badge__rule" />
            </div>
        </div>
    );
}
