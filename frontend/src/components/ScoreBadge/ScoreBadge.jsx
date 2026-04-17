import { useState, useEffect } from "react";
import "./ScoreBadge.css";

export default function ScoreBadge({score = 0, initial = "R"}) {
    const [displayScore, setDisplayScore] = useState(0);

    useEffect(() => {
        const duration = 1500; // 1.5 seconds
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
                Your score is<br />
                <span className="score-badge__number gradient-title">{displayScore}%</span>
            </div>
        </div>
    );
}