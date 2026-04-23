import { useState, useEffect } from "react";
import Navbar from "../../components/Navbar/Navbar";
import "./AboutPage.css";

const METRICS = [
    { title: "Pace",             desc: "Words per minute across your full talk and in 30-second segments. Optimal range is 110–170 WPM." },
    { title: "Fillers",          desc: 'Frequency of filler words (\u201Cum\u201D, \u201Cuh\u201D, \u201Clike\u201D, \u201Cyou know\u201D) and where they cluster.' },
    { title: "Pause Quality",    desc: "Distinguishing purposeful pauses (emphasis, transitions) from hesitation gaps." },
    { title: "Intonation",       desc: "Pitch variation, range, and energy — the expressiveness of your voice." },
    { title: "Content Structure",desc: "Sentence clarity, average length, and use of signpost phrases that guide your audience." },
    { title: "Confidence",       desc: "A composite signal of filler rate, pace consistency, vocal variety, and pause behavior." },
];

export default function AboutPage() {
    const [mIdx, setMIdx] = useState(0);
    const [mDir, setMDir] = useState("forward");

    useEffect(() => {
        const sections = document.querySelectorAll(".about-section, .about-banner, .about-seals-row");
        const observer = new IntersectionObserver(
            (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("revealed"); }),
            { threshold: 0.08 }
        );
        sections.forEach(s => observer.observe(s));
        return () => observer.disconnect();
    }, []);

    const mNext = () => { setMDir("forward"); setMIdx(i => (i + 1) % METRICS.length); };
    const mBack = () => { setMDir("back");    setMIdx(i => (i - 1 + METRICS.length) % METRICS.length); };

    return (
        <>
            <Navbar />
            <div className="page about-page">
                <h1 className="gradient-title"><span className="about-title-serif">About</span> Selki</h1>
                <p className="subtitle-text">AI-powered feedback for your presentations and speeches.</p>

                <div className="about-banner">
                    <img src="/about-banner.svg" alt="" aria-hidden="true" />
                </div>

                <div className="about-section about-section--wide">
                    <h2>What is Selki?</h2>
                    <p>
                        Selki analyzes audio recordings of presentations, lectures, and speeches
                        to give you objective, detailed feedback on your delivery. Upload a recording
                        and get scored on five dimensions in seconds.
                    </p>
                </div>

                <div className="about-section about-section--wide">
                    <h2 className="about-section-h2--centered">How it works</h2>
                    <p className="about-section-sub">Three steps to better presentations.</p>
                    <div className="about-steps">
                        <div className="about-step about-step--first">
                            <span className="about-step__label">STEP 1</span>
                            <strong>Upload your recording</strong>
                            <p>Drop an audio file or paste a URL. Supports MP3, WAV, M4A, and more.</p>
                            <span className="about-step__ghost">1</span>
                        </div>
                        <div className="about-step">
                            <span className="about-step__label">STEP 2</span>
                            <strong>Automated analysis</strong>
                            <p>Selki transcribes your speech with Whisper ASR, detects pauses with Silero VAD, and extracts pitch and energy features.</p>
                            <span className="about-step__ghost">2</span>
                        </div>
                        <div className="about-step">
                            <span className="about-step__label">STEP 3</span>
                            <strong>Get your results</strong>
                            <p>View scores, a timeline of key moments, detailed per-metric breakdowns, and actionable feedback.</p>
                            <span className="about-step__ghost">3</span>
                        </div>
                    </div>
                </div>

                <div className="about-section about-section--wide">
                    <h2 className="about-section-h2--centered">What we measure</h2>
                    <p className="about-section-sub">Six dimensions of delivery, scored objectively.</p>

                    <div className="about-metrics-carousel">
                        <div className="about-metrics-carousel__top">
                            <div className="about-metrics-dots">
                                {METRICS.map((_, i) => (
                                    <button
                                        key={i}
                                        className={`about-metrics-dot${i === mIdx ? " about-metrics-dot--active" : ""}`}
                                        onClick={() => { setMDir(i > mIdx ? "forward" : "back"); setMIdx(i); }}
                                        aria-label={METRICS[i].title}
                                    />
                                ))}
                            </div>
                            <span className="about-metrics-counter">{mIdx + 1} / {METRICS.length}</span>
                        </div>

                        <div className="about-metrics-body">
                            <button onClick={mBack} className="about-metrics-arrow" aria-label="Previous">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="15 18 9 12 15 6" />
                                </svg>
                            </button>

                            <div className={`about-metrics-content about-metrics-content--${mDir}`} key={`${mIdx}-${mDir}`}>
                                <div className="about-metric-flashcard">
                                    <strong>{METRICS[mIdx].title}</strong>
                                    <p>{METRICS[mIdx].desc}</p>
                                </div>
                            </div>

                            <button onClick={mNext} className="about-metrics-arrow" aria-label="Next">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="9 18 15 12 9 6" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <div className="about-section about-section--note">
                    <p>
                        Selki uses rule-based analysis — there is no large language model judging your content.
                        Scores reflect observable delivery characteristics, not the quality of your ideas.
                    </p>
                </div>

                <div className="about-seals-row">
                    <div className="about-seal-item">
                        <img src="/seal-glasses.png" alt="seal" />
                        <span>from</span>
                    </div>
                    <div className="about-seal-item">
                        <img src="/seal-flowers.png" alt="seal" />
                        <span>yours</span>
                    </div>
                    <div className="about-seal-item">
                        <img src="/seal-stars.png" alt="seal" />
                        <span>truly</span>
                    </div>
                </div>

            </div>
        </>
    );
}
