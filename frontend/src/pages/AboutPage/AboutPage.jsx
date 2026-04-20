import Navbar from "../../components/Navbar/Navbar";
import "./AboutPage.css";

export default function AboutPage() {
    return (
        <>
            <Navbar />
            <div className="page about-page">
                <h1 className="gradient-title">About Selki</h1>
                <p className="subtitle-text">AI-powered feedback for your presentations and speeches.</p>

                <div className="about-banner">
                    <img src="/about-banner.svg" alt="" aria-hidden="true" />
                </div>

                <div className="about-section">
                    <h2>What is Selki?</h2>
                    <p>
                        Selki analyzes audio recordings of presentations, lectures, and speeches
                        to give you objective, detailed feedback on your delivery. Upload a recording
                        and get scored on five dimensions in seconds.
                    </p>
                </div>

                <div className="about-section">
                    <h2>How it works</h2>
                    <div className="about-steps">
                        <div className="about-step">
                            <span className="about-step__num">1</span>
                            <div>
                                <strong>Upload your recording</strong>
                                <p>Drop an audio file or paste a URL. Supports MP3, WAV, M4A, and more.</p>
                            </div>
                        </div>
                        <div className="about-step">
                            <span className="about-step__num">2</span>
                            <div>
                                <strong>Automated analysis</strong>
                                <p>Selki transcribes your speech with Whisper ASR, detects pauses with Silero VAD, and extracts pitch and energy features.</p>
                            </div>
                        </div>
                        <div className="about-step">
                            <span className="about-step__num">3</span>
                            <div>
                                <strong>Get your results</strong>
                                <p>View scores, a timeline of key moments, detailed per-metric breakdowns, and actionable feedback.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="about-section">
                    <h2>What we measure</h2>
                    <div className="about-metrics">
                        <div className="about-metric-card">
                            <strong>Pace</strong>
                            <p>Words per minute across your full talk and in 30-second segments. Optimal range is 110–170 WPM.</p>
                        </div>
                        <div className="about-metric-card">
                            <strong>Fillers</strong>
                            <p>Frequency of filler words ("um", "uh", "like", "you know") and where they cluster.</p>
                        </div>
                        <div className="about-metric-card">
                            <strong>Pause Quality</strong>
                            <p>Distinguishing purposeful pauses (emphasis, transitions) from hesitation gaps.</p>
                        </div>
                        <div className="about-metric-card">
                            <strong>Intonation</strong>
                            <p>Pitch variation, range, and energy — the expressiveness of your voice.</p>
                        </div>
                        <div className="about-metric-card">
                            <strong>Content Structure</strong>
                            <p>Sentence clarity, average length, and use of signpost phrases that guide your audience.</p>
                        </div>
                        <div className="about-metric-card">
                            <strong>Confidence</strong>
                            <p>A composite signal of filler rate, pace consistency, vocal variety, and pause behavior.</p>
                        </div>
                    </div>
                </div>

                <div className="about-section about-section--note">
                    <p>
                        Selki uses rule-based analysis — there is no large language model judging your content.
                        Scores reflect observable delivery characteristics, not the quality of your ideas.
                    </p>
                </div>

                <div className="about-seals">
                    <div className="about-seal-row">
                        <img src="/seal-glasses.png" alt="seal with glasses" className="about-seal-img" />
                        <div className="about-speech-bubble">from</div>
                    </div>
                    <div className="about-seal-row">
                        <img src="/seal-flowers.png" alt="seal with flowers" className="about-seal-img" />
                        <div className="about-speech-bubble">yours</div>
                    </div>
                    <div className="about-seal-row">
                        <img src="/seal-stars.png" alt="seal with stars" className="about-seal-img" />
                        <div className="about-speech-bubble">truly</div>
                    </div>
                </div>
            </div>
        </>
    );
}
