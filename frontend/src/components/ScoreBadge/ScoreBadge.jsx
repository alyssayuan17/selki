import { useState, useEffect } from "react";
import "./ScoreBadge.css";

function scoreLevel(n) {
    if (n >= 75) return "excellent";
    if (n >= 50) return "good";
    if (n >= 30) return "needs";
    return "poor";
}

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

    const level = scoreLevel(score);

    return (
        <div className="score-badge">
            <div className="score-badge__score">
                <span className="score-badge__eyebrow">your result</span>
                <span className="score-badge__label">Overall score</span>
                <span className={`score-badge__number score-badge__number--${level}`}>{displayScore}%</span>
                <div className={`score-badge__rule score-badge__rule--${level}`} />
            </div>
        </div>
    );
}
