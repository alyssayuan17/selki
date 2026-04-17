import { useState, useRef, useEffect } from "react";
import "./Timeline.css";

export default function Timeline({ events = [], duration = 0, selectedMetric = null, onSegmentClick }) {
    const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: null });
    const tooltipRef = useRef(null);

    if (!events || events.length === 0) {
        return (
            <div className="timeline">
                <p className="timeline__empty">No timeline events</p>
            </div>
        );
    }

    // Filter events based on selected metric
    const filteredEvents = selectedMetric 
        ? events.filter(e => {
            // Show all pauses for pause_quality metric
            if (e.type === "pause" && selectedMetric === "pause_quality") return true;
            // Show feedback items for the selected metric
            if (e.type === "feedback" && e.metric === selectedMetric) return true;
            // Show segments (items without type field) if they mention the selected metric in issues/highlights
            if (!e.type && (e.dominant_issues || e.highlights) && selectedMetric) {
                const metricName = selectedMetric.replace(/_/g, ' ');
                const issues = (e.dominant_issues || []).join(' ').toLowerCase();
                const highlights = (e.highlights || []).join(' ').toLowerCase();
                return issues.includes(metricName) || highlights.includes(metricName);
            }
            return false;
        })
        : events;

    console.log('Selected metric:', selectedMetric);
    console.log('Total events:', events.length);
    console.log('All events:', events);
    console.log('Feedback events:', events.filter(e => e.type === 'feedback'));
    console.log('Filtered events:', filteredEvents.length);
    console.log('Feedback items in filtered:', filteredEvents.filter(e => e.type === 'feedback').length);

    // separate segment events from pause events and feedback events
    const segments = filteredEvents.filter(e => !e.type && (e.dominant_issues || e.highlights));
    const pauses = filteredEvents.filter(e => e.type === "pause");
    const feedbackItems = filteredEvents.filter(e => e.type === "feedback");

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

    // handle mouse enter on segment
    const handleSegmentMouseEnter = (e, segment) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const content = {
            type: 'segment',
            startSec: segment.start_sec,
            endSec: segment.end_sec,
            issues: segment.dominant_issues || [],
            highlights: segment.highlights || []
        };

        setTooltip({
            visible: true,
            x: rect.left + rect.width / 2,
            y: rect.top - 10,
            content
        });
    };

    // handle mouse enter on pause
    const handlePauseMouseEnter = (e, pause) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const duration = pause.end_sec - pause.start_sec;
        const content = {
            type: 'pause',
            startSec: pause.start_sec,
            endSec: pause.end_sec,
            duration: duration,
            quality: pause.quality,
            source: pause.source,
            context: pause.context // helpful or awkward
        };

        setTooltip({
            visible: true,
            x: rect.left + rect.width / 2,
            y: rect.top - 10,
            content
        });
    };

    // handle mouse enter on feedback
    const handleFeedbackMouseEnter = (e, feedback) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const content = {
            type: 'feedback',
            startSec: feedback.start_sec,
            endSec: feedback.end_sec,
            metric: feedback.metric,
            message: feedback.message,
            tipType: feedback.tip_type
        };

        setTooltip({
            visible: true,
            x: rect.left + rect.width / 2,
            y: rect.top - 10,
            content
        });
    };

    // handle mouse leave
    const handleMouseLeave = () => {
        setTooltip({ visible: false, x: 0, y: 0, content: null });
    };

    // adjust tooltip position to prevent overflow
    useEffect(() => {
        if (tooltip.visible && tooltipRef.current) {
            const tooltipRect = tooltipRef.current.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;

            let adjustedX = tooltip.x;
            let adjustedY = tooltip.y;

            // adjust horizontal position
            if (adjustedX + tooltipRect.width / 2 > viewportWidth - 20) {
                adjustedX = viewportWidth - tooltipRect.width / 2 - 20;
            } else if (adjustedX - tooltipRect.width / 2 < 20) {
                adjustedX = tooltipRect.width / 2 + 20;
            }

            // adjust vertical position
            if (adjustedY - tooltipRect.height < 20) {
                adjustedY = tooltip.y + 80; // position below if too close to top
            }

            if (adjustedX !== tooltip.x || adjustedY !== tooltip.y) {
                setTooltip(prev => ({ ...prev, x: adjustedX, y: adjustedY }));
            }
        }
    }, [tooltip.visible, tooltip.x, tooltip.y]);

    return (
        <div className="timeline">
            <h2 className="timeline__title gradient-title">
                Timeline
                {selectedMetric && (
                    <span className="timeline__filter-badge">
                        {selectedMetric.replace(/_/g, ' ')}
                    </span>
                )}
            </h2>

            {selectedMetric && (segments.length === 0 && pauses.length === 0 && feedbackItems.length === 0) ? (
                <p className="timeline__empty">No timeline events for this metric</p>
            ) : (
                <>
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
                                onMouseEnter={(e) => handleSegmentMouseEnter(e, segment)}
                                onMouseLeave={handleMouseLeave}
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
                                onMouseEnter={(e) => handlePauseMouseEnter(e, pause)}
                                onMouseLeave={handleMouseLeave}
                            />
                        );
                    })}

                    {/* render feedback markers */}
                    {feedbackItems.map((feedback, i) => {
                        const left = getPosition(feedback.start_sec);
                        const width = getPosition(feedback.end_sec) - left;
                        
                        return (
                            <div
                                key={`feedback-${i}`}
                                className={`timeline__feedback timeline__feedback--${feedback.metric}`}
                                style={{ left: `${left}%`, width: `${width}%` }}
                                onMouseEnter={(e) => handleFeedbackMouseEnter(e, feedback)}
                                onMouseLeave={handleMouseLeave}
                            />
                        );
                    })}
                </div>

                {/* time labels */}
                <div className="timeline__time-labels">
                    <span>0s</span>
                    <span>{duration.toFixed(1)}s</span>
                </div>

                {/* legend */}
                <div className="timeline__legend">
                    {segments.some(s => s.dominant_issues?.length > 0) && (
                        <div className="timeline__legend-item">
                            <div className="timeline__legend-color timeline__legend-color--issues"></div>
                            <span>Issues</span>
                        </div>
                    )}
                    {segments.some(s => s.highlights?.length > 0) && (
                        <div className="timeline__legend-item">
                            <div className="timeline__legend-color timeline__legend-color--highlights"></div>
                            <span>Highlights</span>
                        </div>
                    )}
                    {pauses.some(p => p.quality === 'short') && (
                        <div className="timeline__legend-item">
                            <div className="timeline__legend-color timeline__legend-color--short"></div>
                            <span>Short Pause</span>
                        </div>
                    )}
                    {pauses.some(p => p.quality === 'medium') && (
                        <div className="timeline__legend-item">
                            <div className="timeline__legend-color timeline__legend-color--medium"></div>
                            <span>Medium Pause</span>
                        </div>
                    )}
                    {pauses.some(p => p.quality === 'long') && (
                        <div className="timeline__legend-item">
                            <div className="timeline__legend-color timeline__legend-color--long"></div>
                            <span>Long Pause</span>
                        </div>
                    )}
                </div>
            </div>

            {/* tooltip */}
            {tooltip.visible && tooltip.content && (
                <div
                    ref={tooltipRef}
                    className={`timeline__tooltip ${tooltip.visible ? 'timeline__tooltip--visible' : ''}`}
                    style={{
                        left: `${tooltip.x}px`,
                        top: `${tooltip.y}px`,
                        transform: 'translate(-50%, -100%)'
                    }}
                >
                    {tooltip.content.type === 'segment' ? (
                        <>
                            <div className="timeline__tooltip-time">
                                {tooltip.content.startSec.toFixed(1)}s - {tooltip.content.endSec.toFixed(1)}s
                            </div>
                            {tooltip.content.issues.length > 0 && (
                                <div className="timeline__tooltip-section">
                                    <div className="timeline__tooltip-label">Issues</div>
                                    <ul className="timeline__tooltip-list timeline__tooltip-list--issues">
                                        {tooltip.content.issues.map((issue, i) => (
                                            <li key={i}>{issue.replace(/_/g, ' ')}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            {tooltip.content.highlights.length > 0 && (
                                <div className="timeline__tooltip-section">
                                    <div className="timeline__tooltip-label">Highlights</div>
                                    <ul className="timeline__tooltip-list timeline__tooltip-list--highlights">
                                        {tooltip.content.highlights.map((highlight, i) => (
                                            <li key={i}>{highlight.replace(/_/g, ' ')}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </>
                    ) : tooltip.content.type === 'feedback' ? (
                        <>
                            <div className="timeline__tooltip-time">
                                {tooltip.content.startSec.toFixed(1)}s - {tooltip.content.endSec?.toFixed(1)}s
                            </div>
                            <div className="timeline__tooltip-section">
                                <div className="timeline__tooltip-label">
                                    {tooltip.content.metric?.replace(/_/g, ' ').toUpperCase()}
                                </div>
                                <div className="timeline__tooltip-quality">
                                    {tooltip.content.message}
                                </div>
                            </div>
                        </>
                    ) : (
                        <>
                            <div className="timeline__tooltip-time">
                                {tooltip.content.startSec.toFixed(1)}s - {tooltip.content.endSec?.toFixed(1) || tooltip.content.startSec.toFixed(1)}s
                            </div>
                            <div className="timeline__tooltip-section">
                                <div className="timeline__tooltip-quality">
                                    <strong>Type:</strong> Pause
                                </div>
                                <div className="timeline__tooltip-quality">
                                    <strong>Duration:</strong> {tooltip.content.duration?.toFixed(2)}s
                                </div>
                                <div className="timeline__tooltip-quality">
                                    <strong>Quality:</strong> {tooltip.content.quality} pause
                                </div>
                                {tooltip.content.context && (
                                    <div className="timeline__tooltip-quality">
                                        <strong>Context:</strong> {tooltip.content.context} pause
                                    </div>
                                )}
                                {tooltip.content.source && (
                                    <div className="timeline__tooltip-quality">
                                        <strong>Source:</strong> {tooltip.content.source.toUpperCase()}
                                    </div>
                                )}
                            </div>
                        </>
                    )}
                </div>
            )}
            </>
            )}
        </div>
    );
}
