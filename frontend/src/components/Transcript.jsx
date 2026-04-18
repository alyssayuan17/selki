export default function Transcript({ transcript, viewMode = "full" }) {
    if (!transcript || !transcript.full_text) {
        return (
            <div className="transcript">
                <p className="transcript__empty">No transcript available</p>
            </div>
        );
    }

    const { full_text, language, segments = [], tokens = [] } = transcript;

    // render full text view
    const renderFullText = () => (
        <div className="transcript__full">
            <p className="transcript__text">{full_text}</p>
        </div>
    );

    // render segmented view (10-second chunks)
    const renderSegments = () => (
        <div className="transcript__segments">
            {segments.map((segment, i) => (
                <div key={i} className="transcript__segment">
                    <div className="transcript__segment-time">
                        {segment.start_sec.toFixed(1)}s - {segment.end_sec.toFixed(1)}s
                        <span className="transcript__segment-confidence">
                            {(segment.avg_confidence * 100).toFixed(0)}% confidence
                        </span>
                    </div>
                    <p className="transcript__segment-text">{segment.text}</p>
                </div>
            ))}
        </div>
    );

    // render word-level tokens with filler highlighting
    const renderTokens = () => (
        <div className="transcript__tokens">
            {tokens.map((token, i) => (
                <span
                    key={i}
                    className={`transcript__token ${token.is_filler ? "transcript__token--filler" : ""}`}
                    title={`${token.start_sec.toFixed(1)}s - ${token.end_sec.toFixed(1)}s${token.is_filler ? " (filler)" : ""}`}
                >
                    {token.text}
                </span>
            ))}
        </div>
    );

    return (
        <div className="transcript">
            <div className="transcript__header">
                <h3 className="transcript__title gradient-title">Transcript</h3>
                {language && (
                    <span className="transcript__language">{language.toUpperCase()}</span>
                )}
            </div>

            {/* view mode switcher placeholder - can be enhanced later */}
            {viewMode === "full" && renderFullText()}
            {viewMode === "segments" && renderSegments()}
            {viewMode === "tokens" && renderTokens()}
        </div>
    );
}
