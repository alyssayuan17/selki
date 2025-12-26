export default function ScoreBadge({score = 0, initial = "R"}) {
    return (
        <div className="score-badge">
            <div className="score-badge__circle">{initial}</div>
            <div className="score-badge__score">
                Your score is<br />
                <span className="score-badge__number">{score}%</span>
            </div>
        </div>
    );
}