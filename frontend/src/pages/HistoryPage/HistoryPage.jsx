import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import "./HistoryPage.css";

const STATUS_LABEL = {
    done: "Done",
    processing: "Processing",
    queued: "Queued",
    failed: "Failed",
};

function formatDate(isoString) {
    if (!isoString) return "—";
    return new Date(isoString).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function formatDuration(sec) {
    if (!sec) return "—";
    const m = Math.floor(sec / 60);
    const s = Math.round(sec % 60);
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export default function HistoryPage() {
    const [jobs, setJobs] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const LIMIT = 20;

    useEffect(() => {
        setLoading(true);
        fetch(`/api/v1/presentations?limit=${LIMIT}&offset=${page * LIMIT}`)
            .then((r) => {
                if (!r.ok) throw new Error("Failed to load history");
                return r.json();
            })
            .then((data) => {
                setJobs(data.jobs);
                setTotal(data.total);
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    }, [page]);

    const totalPages = Math.ceil(total / LIMIT);

    return (
        <>
            <Navbar />
            <div className="page history-page">
                <h1 className="gradient-title">Your Analyses</h1>
                <p className="subtitle-text">{total} total recording{total !== 1 ? "s" : ""}</p>

                {loading && <div className="history-loading">Loading...</div>}
                {error && <div className="history-error">{error}</div>}

                {!loading && !error && jobs.length === 0 && (
                    <div className="history-empty">
                        <p>No analyses yet.</p>
                        <Link to="/upload" className="btn-primary">Analyze a Presentation</Link>
                    </div>
                )}

                {!loading && !error && jobs.length > 0 && (
                    <>
                        <div className="history-list">
                            {jobs.map((job) => (
                                <div key={job.job_id} className={`history-card history-card--${job.status}`}>
                                    <div className="history-card__left">
                                        <span className={`history-status history-status--${job.status}`}>
                                            {STATUS_LABEL[job.status] ?? job.status}
                                        </span>
                                        <div className="history-meta">
                                            <span className="history-type">
                                                {job.talk_type ?? "Unknown type"}
                                                {job.audience_type ? ` · ${job.audience_type}` : ""}
                                            </span>
                                            <span className="history-date">{formatDate(job.created_at)}</span>
                                            {job.duration_sec && (
                                                <span className="history-duration">{formatDuration(job.duration_sec)}</span>
                                            )}
                                        </div>
                                    </div>

                                    <div className="history-card__right">
                                        {job.status === "done" && job.score_value != null && (
                                            <div className={`history-score history-score--${job.score_label}`}>
                                                <span className="history-score__value">{job.score_value}</span>
                                                <span className="history-score__label">{job.score_label?.replace(/_/g, " ")}</span>
                                            </div>
                                        )}
                                        {job.status === "done" && (
                                            <Link
                                                to={`/results/${job.job_id}`}
                                                className="btn-view"
                                            >
                                                View →
                                            </Link>
                                        )}
                                        {job.status === "failed" && (
                                            <span className="history-failed-label">Analysis failed</span>
                                        )}
                                        {(job.status === "processing" || job.status === "queued") && (
                                            <Link
                                                to={`/processing/${job.job_id}`}
                                                className="btn-view"
                                            >
                                                Check status →
                                            </Link>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {totalPages > 1 && (
                            <div className="history-pagination">
                                <button
                                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                                    disabled={page === 0}
                                    className="btn-page"
                                >
                                    ← Prev
                                </button>
                                <span className="history-page-info">
                                    Page {page + 1} of {totalPages}
                                </span>
                                <button
                                    onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                                    disabled={page >= totalPages - 1}
                                    className="btn-page"
                                >
                                    Next →
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </>
    );
}
