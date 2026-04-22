import { useState, useEffect } from "react";
import Navbar from "../../components/Navbar/Navbar";
import "./GuidePage.css";

const TRANSCRIPT_VIEWS = [
    { title: "Full Text",  description: "Plain transcript of everything said",          image: "/transcript-full.png" },
    { title: "Segments",   description: "Transcript split by timed speech segments",    image: "/transcript-segments.png" },
    { title: "Words",      description: "Word-level view with filler words highlighted", image: "/transcript-words.png" },
];

export default function GuidePage() {
    const [tcIdx, setTcIdx] = useState(0);
    const [tcDir, setTcDir] = useState("forward");

    const tcNext = () => { setTcDir("forward"); setTcIdx(i => (i + 1) % TRANSCRIPT_VIEWS.length); };
    const tcBack = () => { setTcDir("back");    setTcIdx(i => (i - 1 + TRANSCRIPT_VIEWS.length) % TRANSCRIPT_VIEWS.length); };

    useEffect(() => {
        const sections = document.querySelectorAll(".guide-section");
        const observer = new IntersectionObserver(
            (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("revealed"); }),
            { threshold: 0.1 }
        );
        sections.forEach(s => observer.observe(s));
        return () => observer.disconnect();
    }, []);

    return (
        <>
            <Navbar />
            <div className="page guide-page">
                <h1 className="gradient-title">How to Use Selki</h1>
                <p className="subtitle-text">Get the most out of your analysis.</p>

                <div className="guide-section">
                    <h2 className="guide-tc-heading">Uploading a recording</h2>
                    <p className="guide-section-sub guide-tc-sub">You upload, we handle the rest.</p>
                    <div className="guide-cards">
                        <div className="guide-card">
                            <svg className="guide-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>
                            </svg>
                            <strong>Supported formats</strong>
                            <p>MP3, WAV, M4A, FLAC, OGG, WebM</p>
                        </div>
                        <div className="guide-card">
                            <svg className="guide-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                            </svg>
                            <strong>Max file size</strong>
                            <p>100 MB per upload</p>
                        </div>
                        <div className="guide-card">
                            <svg className="guide-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                            </svg>
                            <strong>Audio URL</strong>
                            <p>Paste a direct link to an audio file instead of uploading</p>
                        </div>
                        <div className="guide-card">
                            <svg className="guide-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                            </svg>
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

                <div className="guide-section guide-scores-section">
                    <div className="guide-macwindow">
                        <div className="guide-macwindow__bar">
                            <span className="guide-macwindow__dot guide-macwindow__dot--red"/>
                            <span className="guide-macwindow__dot guide-macwindow__dot--yellow"/>
                            <span className="guide-macwindow__dot guide-macwindow__dot--green"/>
                        </div>
                        <div className="guide-macwindow__content">
                            {/* image goes here */}
                        </div>
                    </div>
                    <div className="guide-scores-content">
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
                </div>

                <div className="guide-section">
                    <div className="guide-timeline-card">
                        <div className="guide-timeline-card__text">
                            <h2>Using the timeline</h2>
                            <p>
                                The timeline below your scores shows key moments in your recording: pauses, filler clusters,
                                and metric-specific events. Click a metric card to highlight its events on the timeline.
                            </p>
                        </div>
                        <div className="guide-macwindow">
                            <div className="guide-macwindow__bar">
                                <span className="guide-macwindow__dot guide-macwindow__dot--red"/>
                                <span className="guide-macwindow__dot guide-macwindow__dot--yellow"/>
                                <span className="guide-macwindow__dot guide-macwindow__dot--green"/>
                            </div>
                            <div className="guide-macwindow__content">
                                {/* image goes here */}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="guide-section">
                    <h2 className="guide-tc-heading">Transcript views</h2>
                    <p className="guide-section-sub guide-tc-sub">Three ways to explore what you said.</p>
                    <div className="guide-tc-carousel">
                        <div className="guide-tc-carousel__top">
                            <div className="guide-tc-dots">
                                {TRANSCRIPT_VIEWS.map((_, i) => (
                                    <button
                                        key={i}
                                        className={`guide-tc-dot${i === tcIdx ? " guide-tc-dot--active" : ""}`}
                                        onClick={() => { setTcDir(i > tcIdx ? "forward" : "back"); setTcIdx(i); }}
                                        aria-label={TRANSCRIPT_VIEWS[i].title}
                                    />
                                ))}
                            </div>
                            <span className="guide-tc-counter">{tcIdx + 1} / {TRANSCRIPT_VIEWS.length}</span>
                        </div>

                        <div className="guide-tc-body">
                            <button onClick={tcBack} className="guide-tc-arrow" aria-label="Previous">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="15 18 9 12 15 6" />
                                </svg>
                            </button>

                            <div className={`guide-tc-content guide-tc-content--${tcDir}`} key={`${tcIdx}-${tcDir}`}>
                                <div className="guide-transcript-card">
                                    <img src={TRANSCRIPT_VIEWS[tcIdx].image} alt={TRANSCRIPT_VIEWS[tcIdx].title} className="guide-tc-card-img" />
                                    <div className="guide-tc-card-overlay" />
                                    <div className="guide-tc-card-text">
                                        <strong>{TRANSCRIPT_VIEWS[tcIdx].title}</strong>
                                        <p>{TRANSCRIPT_VIEWS[tcIdx].description}</p>
                                    </div>
                                </div>
                            </div>

                            <button onClick={tcNext} className="guide-tc-arrow" aria-label="Next">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="9 18 15 12 9 6" />
                                </svg>
                            </button>
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
