import Navbar from "../../components/Navbar/Navbar";
import "./GuidePage.css";

export default function GuidePage() {
    return (
        <>
            <Navbar />
            <div className="page guide-page">
                <h1 className="gradient-title">How to Use Selki</h1>
                <p className="subtitle-text">Get the most out of your analysis.</p>

                <div className="guide-section">
                    <h2>Uploading a recording</h2>
                    <ul className="guide-list">
                        <li><strong>Supported formats:</strong> MP3, WAV, M4A, FLAC, OGG, WebM</li>
                        <li><strong>Max file size:</strong> 100 MB</li>
                        <li>You can also paste a direct URL to an audio file instead of uploading</li>
                        <li>Set the <strong>talk type</strong> (lecture, pitch, interview, etc.) and <strong>audience</strong> for context-aware feedback</li>
                    </ul>
                </div>

                <div className="guide-section">
                    <h2>Recording tips for best results</h2>
                    <ul className="guide-list">
                        <li>Use a headset or external microphone — laptop mics pick up too much room noise</li>
                        <li>Record in a quiet space; Selki will warn you if background noise is high</li>
                        <li>Aim for at least 60 seconds of speech — very short clips produce less reliable scores</li>
                        <li>Avoid recordings with multiple overlapping speakers</li>
                    </ul>
                </div>

                <div className="guide-section">
                    <h2>Understanding your scores</h2>
                    <div className="guide-score-key">
                        <div className="guide-score-row">
                            <span className="guide-score-badge guide-score-badge--excellent">75–100</span>
                            <span>Excellent — performing well in this area</span>
                        </div>
                        <div className="guide-score-row">
                            <span className="guide-score-badge guide-score-badge--good">50–74</span>
                            <span>Good — solid, with room to improve</span>
                        </div>
                        <div className="guide-score-row">
                            <span className="guide-score-badge guide-score-badge--needs-improvement">30–49</span>
                            <span>Needs improvement — focus here first</span>
                        </div>
                        <div className="guide-score-row">
                            <span className="guide-score-badge guide-score-badge--poor">0–29</span>
                            <span>Poor — significant delivery issues detected</span>
                        </div>
                    </div>
                    <p className="guide-note">
                        Scores marked <strong>N/A</strong> mean there wasn't enough data to compute that metric reliably.
                    </p>
                </div>

                <div className="guide-section">
                    <h2>Using the timeline</h2>
                    <p>
                        The timeline below your scores shows key moments in your recording: pauses, filler clusters,
                        and metric-specific events. Click a metric card to highlight its events on the timeline.
                    </p>
                </div>

                <div className="guide-section">
                    <h2>Transcript views</h2>
                    <ul className="guide-list">
                        <li><strong>Full Text</strong> — plain transcript of everything said</li>
                        <li><strong>Segments</strong> — transcript split by timed speech segments</li>
                        <li><strong>Words</strong> — word-level view with filler words highlighted</li>
                    </ul>
                </div>

                <div className="guide-section">
                    <h2>Quality warnings</h2>
                    <p>
                        If your recording has poor audio quality, low speech content, or excessive background noise,
                        Selki will display a warning panel. Some metrics may be abstained (N/A) in these cases.
                        Re-recording in a better environment will improve accuracy.
                    </p>
                </div>
            </div>
        </>
    );
}
