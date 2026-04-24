import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar/Navbar";
import AuthModal from "../../components/AuthModal/AuthModal";
import { useAuth } from "../../context/AuthContext";
import "./HistoryPage.css";

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

function ScoreCircle({ value, label }) {
    const n = parseInt(value);
    const level = isNaN(n) ? "na" : n >= 75 ? "excellent" : n >= 50 ? "good" : n >= 30 ? "needs" : "poor";
    return (
        <div className={`history-score history-score--${level}`}>
            <span className="history-score__value">{value ?? "—"}</span>
            <span className="history-score__label">{label?.replace(/_/g, " ") ?? ""}</span>
        </div>
    );
}

export default function HistoryPage() {
    const { isLoggedIn, user, authedFetch, logout } = useAuth();
    const [jobs, setJobs] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showAuthModal, setShowAuthModal] = useState(false);
    const [authModalTab, setAuthModalTab] = useState("login");

    const LIMIT = 20;

    useEffect(() => {
        if (!isLoggedIn) { setLoading(false); return; }
        setLoading(true);
        authedFetch(`/api/v1/history?limit=${LIMIT}&offset=${page * LIMIT}`)
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
    }, [page, isLoggedIn, authedFetch]);

    const totalPages = Math.ceil(total / LIMIT);

    const openLogin = () => { setAuthModalTab("login"); setShowAuthModal(true); };
    const openRegister = () => { setAuthModalTab("register"); setShowAuthModal(true); };

    return (
        <>
            <Navbar />
            {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} defaultTab={authModalTab} />}

            <div className="page history-page">
                <div className="history-header">
                    <h1 className="history-title">Saved Analyses</h1>
                    {isLoggedIn && user && (
                        <div className="history-user-row">
                            <span className="history-username">@{user.username}</span>
                            <button className="history-logout-btn" onClick={logout}>Sign out</button>
                        </div>
                    )}
                </div>

                {!isLoggedIn ? (
                    <div className="history-auth-prompt">
                        <div className="history-auth-prompt__macbar">
                            <span className="history-auth-dot history-auth-dot--red" />
                            <span className="history-auth-dot history-auth-dot--yellow" />
                            <span className="history-auth-dot history-auth-dot--green" />
                        </div>
                        <div className="history-auth-prompt__body">
                            <p className="history-auth-prompt__text">
                                Sign in to view your saved analyses and track your progress over time.
                            </p>
                            <div className="history-auth-prompt__btns">
                                <button className="history-auth-btn history-auth-btn--primary" onClick={openLogin}>
                                    Sign In
                                </button>
                                <button className="history-auth-btn history-auth-btn--secondary" onClick={openRegister}>
                                    Create Account
                                </button>
                            </div>
                        </div>
                    </div>
                ) : (
                    <>
                        {loading && <div className="history-loading">Loading…</div>}
                        {error && <div className="history-error">{error}</div>}

                        {!loading && !error && jobs.length === 0 && (
                            <div className="history-empty">
                                <div className="history-empty__macbar">
                                    <span className="history-auth-dot history-auth-dot--red" />
                                    <span className="history-auth-dot history-auth-dot--yellow" />
                                    <span className="history-auth-dot history-auth-dot--green" />
                                </div>
                                <p className="history-empty__text">No saved analyses yet.</p>
                                <p className="history-empty__sub">After analyzing a presentation, hit <strong>Save Analysis</strong> to keep it here.</p>
                                <Link to="/upload" className="history-empty__btn">Analyze a Presentation →</Link>
                            </div>
                        )}

                        {!loading && !error && jobs.length > 0 && (
                            <>
                                <p className="history-count">{total} saved recording{total !== 1 ? "s" : ""}</p>
                                <div className="history-list">
                                    {jobs.map((job) => (
                                        <Link key={job.job_id} to={`/results/${job.job_id}`} className="history-card">
                                            <div className="history-card__macbar">
                                                <span className="history-card__dot history-card__dot--red" />
                                                <span className="history-card__dot history-card__dot--yellow" />
                                                <span className="history-card__dot history-card__dot--green" />
                                            </div>
                                            <div className="history-card__body">
                                                <div className="history-card__left">
                                                    <span className="history-card__type">
                                                        {job.talk_type ?? "Recording"}
                                                        {job.audience_type ? ` · ${job.audience_type}` : ""}
                                                    </span>
                                                    <div className="history-card__meta">
                                                        <span className="history-card__date">{formatDate(job.created_at)}</span>
                                                        {job.duration_sec && (
                                                            <span className="history-card__duration">{formatDuration(job.duration_sec)}</span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="history-card__right">
                                                    {job.score_value != null && (
                                                        <ScoreCircle value={job.score_value} label={job.score_label} />
                                                    )}
                                                    <span className="history-card__arrow">→</span>
                                                </div>
                                            </div>
                                        </Link>
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
                    </>
                )}
            </div>
        </>
    );
}
