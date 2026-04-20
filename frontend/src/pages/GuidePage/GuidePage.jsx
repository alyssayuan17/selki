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
                    <p className="guide-section-sub">You upload, we handle the rest.</p>
                    <div className="guide-cards">
                        <div className="guide-card">
                            <span className="guide-card-num">1</span>
                            <strong>Supported formats</strong>
                            <p>MP3, WAV, M4A, FLAC, OGG, WebM</p>
                        </div>
                        <div className="guide-card">
                            <span className="guide-card-num">2</span>
                            <strong>Max file size</strong>
                            <p>100 MB per upload</p>
                        </div>
                        <div className="guide-card">
                            <span className="guide-card-num">3</span>
                            <strong>Audio URL</strong>
                            <p>Paste a direct link to an audio file instead of uploading</p>
                        </div>
                        <div className="guide-card">
                            <span className="guide-card-num">4</span>
                            <strong>Talk type & audience</strong>
                            <p>Set the talk type and audience for context-aware feedback</p>
                        </div>
                    </div>
                </div>

                <div className="guide-section">
                    <div className="guide-tips-card">
                        <div className="guide-tips-left">
                            <h2>Recording tips for best results</h2>
                            <p>A better recording means better feedback.</p>
                        </div>
                        <ul className="guide-tips-list">
                            <li><span className="guide-tip-check">✓</span>Use a headset or external microphone — laptop mics pick up too much room noise</li>
                            <li><span className="guide-tip-check">✓</span>Record in a quiet space; Selki will warn you if background noise is high</li>
                            <li><span className="guide-tip-check">✓</span>Aim for at least 60 seconds of speech — very short clips produce less reliable scores</li>
                            <li><span className="guide-tip-check">✓</span>Avoid recordings with multiple overlapping speakers</li>
                        </ul>
                    </div>
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
                    <div className="guide-transcript-cards">
                        <div className="guide-transcript-card">
                            <strong>Full Text</strong>
                            <p>Plain transcript of everything said</p>
                        </div>
                        <div className="guide-transcript-card">
                            <strong>Segments</strong>
                            <p>Transcript split by timed speech segments</p>
                        </div>
                        <div className="guide-transcript-card">
                            <strong>Words</strong>
                            <p>Word-level view with filler words highlighted</p>
                        </div>
                    </div>
                </div>

                <div className="guide-section guide-section--note">
                    <p>
                        <strong>Quality warnings: </strong>
                        If your recording has poor audio quality, low speech content, or excessive background noise,
                        Selki will display a warning panel. Some metrics may be abstained (N/A) in these cases.
                        Re-recording in a better environment will improve accuracy.
                    </p>
                </div>
            </div>
        </>
    );
}
