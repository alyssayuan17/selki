import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import "./ProcessingPage.css";
import "../../components/Button/Button.css";

const STATUS_MESSAGES = [
    "Transcribing your speech…",
    "Detecting pauses and fillers…",
    "Analyzing pitch and energy…",
    "Measuring pace and rhythm…",
    "Scoring your delivery…",
    "Almost there…",
];

export default function ProcessingPage() {
    const { jobId } = useParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState("processing");
    const [error, setError] = useState(null);
    const [progress, setProgress] = useState(0);
    const [msgIdx, setMsgIdx] = useState(0);

    useEffect(() => {
        const msgId = setInterval(() => setMsgIdx(i => (i + 1) % STATUS_MESSAGES.length), 2800);
        return () => clearInterval(msgId);
    }, []);

    useEffect(() => {
        let intervalId;
        let progressIntervalId;

        const timeoutId = setTimeout(() => {
            clearInterval(intervalId);
            clearInterval(progressIntervalId);
            setError("Analysis is taking too long. The job may have been interrupted — please try uploading again.");
            setStatus("error");
        }, 10 * 60 * 1000);

        progressIntervalId = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 90) return prev;
                return prev + Math.random() * 10;
            });
        }, 500);

        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/v1/presentations/${jobId}`);
                if (!response.ok) throw new Error("Failed to check status");
                const data = await response.json();

                if (data.status === "done") {
                    clearInterval(intervalId);
                    clearInterval(progressIntervalId);
                    clearTimeout(timeoutId);
                    setProgress(100);
                    setTimeout(() => navigate(`/results/${jobId}`), 500);
                } else if (data.status === "failed") {
                    clearInterval(intervalId);
                    clearInterval(progressIntervalId);
                    clearTimeout(timeoutId);
                    setError(data.failure?.message || "Analysis failed");
                    setStatus("failed");
                } else {
                    setStatus(data.status);
                }
            } catch (err) {
                clearInterval(intervalId);
                clearInterval(progressIntervalId);
                clearTimeout(timeoutId);
                setError(err.message);
                setStatus("error");
            }
        };

        checkStatus();
        intervalId = setInterval(checkStatus, 2000);

        return () => {
            clearInterval(intervalId);
            clearInterval(progressIntervalId);
            clearTimeout(timeoutId);
        };
    }, [jobId, navigate]);

    if (status === "failed" || status === "error") {
        return (
            <>
                <Navbar />
                <div className="processing-overlay">
                    <div className="processing-popup processing-popup--error">
                        <div className="processing-error-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                        </div>
                        <h2 className="processing-error-title">Analysis Failed</h2>
                        <p className="processing-error-msg">{error || "An error occurred during analysis"}</p>
                        <button className="btn btn-primary" onClick={() => navigate("/")}>Try Again</button>
                    </div>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            <div className="processing-overlay">
                <div className="processing-popup">
                    <div className="processing-spinner-wrap">
                        <div className="processing-spinner" />
                        <div className="processing-spinner-inner" />
                    </div>

                    <h2 className="processing-title">
                        <span className="processing-title-serif">Analyzing</span> your recording
                    </h2>

                    <p className="processing-status__text" key={msgIdx}>
                        {STATUS_MESSAGES[msgIdx]}
                    </p>

                    <div className="processing-progress-track">
                        <div className="processing-progress-bar" style={{ width: `${Math.min(progress, 100)}%` }} />
                    </div>

                </div>
            </div>
        </>
    );
}
