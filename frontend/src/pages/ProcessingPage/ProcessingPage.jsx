import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import "./ProcessingPage.css";

export default function ProcessingPage() {
    const { jobId } = useParams();
    const navigate = useNavigate();
    const [status, setStatus] = useState("processing");
    const [error, setError] = useState(null);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        let intervalId;
        let progressIntervalId;

        // simulate progress animation
        progressIntervalId = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 90) return prev;
                return prev + Math.random() * 10;
            });
        }, 500);

        // poll status every 2 seconds
        const checkStatus = async () => {
            try {
                const response = await fetch(`/api/v1/presentations/${jobId}`);

                if (!response.ok) {
                    throw new Error("Failed to check status");
                }

                const data = await response.json();

                if (data.status === "done") {
                    clearInterval(intervalId);
                    clearInterval(progressIntervalId);
                    setProgress(100);
                    // wait briefly to show 100% before navigating
                    setTimeout(() => {
                        navigate(`/results/${jobId}`);
                    }, 500);
                } else if (data.status === "failed") {
                    clearInterval(intervalId);
                    clearInterval(progressIntervalId);
                    setError(data.failure?.message || "Analysis failed");
                    setStatus("failed");
                } else {
                    setStatus(data.status);
                }
            } catch (err) {
                clearInterval(intervalId);
                clearInterval(progressIntervalId);
                setError(err.message);
                setStatus("error");
            }
        };

        // check immediately
        checkStatus();

        // then poll every 2 seconds
        intervalId = setInterval(checkStatus, 2000);

        // cleanup
        return () => {
            clearInterval(intervalId);
            clearInterval(progressIntervalId);
        };
    }, [jobId, navigate]);

    if (status === "failed" || status === "error") {
        return (
            <>
            <Navbar />
            <div className="page processing-page">
                <div className="processing-error">
                    <h2>Analysis Failed</h2>
                    <p>{error || "An error occurred during analysis"}</p>
                    <button
                        className="btn-primary"
                        onClick={() => navigate("/upload")}
                    >
                        Try Again
                    </button>
                </div>
            </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            {/* Processing Modal Overlay */}
            <div className="processing-overlay" id="processingOverlay">
                <div className="processing-popup" id="processingPopup">
                    <h2>Processing...</h2>
                    <div className="loader"></div>
                    <p className="processing-status__text">
                        {status === "queued" ? "Queued" : "Analyzing your presentation"}...
                    </p>
                    <p className="processing-note">
                        Job ID: <code>{jobId}</code>
                    </p>
                </div>
            </div>
        </>
    );
}
