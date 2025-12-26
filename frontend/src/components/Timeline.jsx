export default function Timeline({ events = [], duration = 0, onSegmentClick }) {
    if (!events || events.length === 0) {
        return (
            <div className="timeline">
                <p className="timeline__empty">No timeline events</p>
            </div>
        );
    }

    // separate segment events from pause events
    const segments = events.filter(e => e.dominant_issues || e.highlights);
    const pauses = events.filter(e => e.type === "pause");

    // calculate position percentage
    const getPosition = (timeSec) => {
        if (!duration || duration === 0) return 0;
        return (timeSec / duration) * 100;
    };

    // get segment type for styling
    const getSegmentType = (segment) => {
        if (segment.dominant_issues?.length > 0) return "issues";
        if (segment.highlights?.length > 0) return "highlights";
        return "neutral";
    };

    return (
        <div className="timeline">
            <h3 className="timeline__title">Timeline</h3>

            {/* visual timeline bar */}
            <div className="timeline__container">
                <div className="timeline__bar">
                    {/* render segments */}
                    {segments.map((segment, i) => {
                        const left = getPosition(segment.start_sec);
                        const width = getPosition(segment.end_sec) - left;
                        const type = getSegmentType(segment);

                        return (
                            <div
                                key={`seg-${i}`}
                                className={`timeline__segment timeline__segment--${type}`}
                                style={{ left: `${left}%`, width: `${width}%` }}
                                onClick={() => onSegmentClick?.(segment)}
                                title={`${segment.start_sec}s-${segment.end_sec}s`}
                            />
                        );
                    })}

                    {/* render pause markers */}
                    {pauses.map((pause, i) => {
                        const position = getPosition(pause.start_sec);
                        return (
                            <div
                                key={`pause-${i}`}
                                className={`timeline__pause timeline__pause--${pause.quality}`}
                                style={{ left: `${position}%` }}
                                title={`${pause.quality} pause at ${pause.start_sec}s`}
                            />
                        );
                    })}
                </div>

                {/* time labels */}
                <div className="timeline__time-labels">
                    <span>0s</span>
                    <span>{duration}s</span>
                </div>
            </div>

            {/* event list */}
            <div className="timeline__events">
                {segments.map((segment, i) => (
                    <div key={i} className="timeline__event">
                        <div className="timeline__event-time">
                            {segment.start_sec.toFixed(1)}s - {segment.end_sec.toFixed(1)}s
                        </div>
                        {segment.dominant_issues?.length > 0 && (
                            <div className="timeline__event-issues">
                                Issues: {segment.dominant_issues.join(", ")}
                            </div>
                        )}
                        {segment.highlights?.length > 0 && (
                            <div className="timeline__event-highlights">
                                Highlights: {segment.highlights.join(", ")}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
