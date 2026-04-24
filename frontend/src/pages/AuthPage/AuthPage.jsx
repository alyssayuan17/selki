import { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import "./AuthPage.css";

export default function AuthPage() {
    const [searchParams] = useSearchParams();
    const defaultTab = searchParams.get("tab") === "register" ? "register" : "login";
    const returnTo = searchParams.get("returnTo") || "/history";

    const { login, register, isLoggedIn } = useAuth();
    const navigate = useNavigate();

    const [tab, setTab] = useState(defaultTab);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const [loginEmail, setLoginEmail] = useState("");
    const [loginPassword, setLoginPassword] = useState("");

    const [regUsername, setRegUsername] = useState("");
    const [regEmail, setRegEmail] = useState("");
    const [regPassword, setRegPassword] = useState("");

    useEffect(() => {
        if (isLoggedIn) navigate(returnTo, { replace: true });
    }, [isLoggedIn, navigate, returnTo]);

    useEffect(() => { setError(null); }, [tab]);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true); setError(null);
        try {
            await login(loginEmail, loginPassword);
            navigate(returnTo, { replace: true });
        } catch (err) {
            setError(err.message);
        } finally { setLoading(false); }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        if (regPassword.length < 6) { setError("Password must be at least 6 characters"); return; }
        setLoading(true); setError(null);
        try {
            await register(regUsername, regEmail, regPassword);
            navigate(returnTo, { replace: true });
        } catch (err) {
            setError(err.message);
        } finally { setLoading(false); }
    };

    return (
        <div className="auth-page">
            {/* Left panel — branding */}
            <div className="auth-page__left">
                <Link to="/" className="auth-page__back">← Back to home</Link>

                <div className="auth-page__brand">
                    <span className="auth-page__brand-name">Selki</span>
                    <img src="/selki_logo_v2.svg" alt="Selki" className="auth-page__brand-logo" />
                </div>

                <div className="auth-page__tagline">
                    <h2 className="auth-page__tagline-h">Your voice,<br />perfected.</h2>
                    <p className="auth-page__tagline-sub">Save your analyses, track progress, and become a better speaker over time.</p>
                </div>

                <div className="auth-page__orbs" aria-hidden="true">
                    <div className="auth-page__orb auth-page__orb--1" />
                    <div className="auth-page__orb auth-page__orb--2" />
                    <div className="auth-page__orb auth-page__orb--3" />
                </div>
            </div>

            {/* Right panel — form */}
            <div className="auth-page__right">
                <div className="auth-card">
                    <div className="auth-card__macbar">
                        <span className="auth-card__dot auth-card__dot--red" />
                        <span className="auth-card__dot auth-card__dot--yellow" />
                        <span className="auth-card__dot auth-card__dot--green" />
                    </div>

                    <div className="auth-card__inner">
                        <h1 className="auth-card__title">
                            {tab === "login" ? "Welcome back" : "Join Selki"}
                        </h1>
                        <p className="auth-card__subtitle">
                            {tab === "login"
                                ? "Sign in to access your saved analyses."
                                : "Create an account to save your progress."}
                        </p>

                        <div className="auth-card__tabs">
                            <button
                                className={`auth-card__tab${tab === "login" ? " auth-card__tab--active" : ""}`}
                                onClick={() => setTab("login")}
                            >
                                Sign In
                            </button>
                            <button
                                className={`auth-card__tab${tab === "register" ? " auth-card__tab--active" : ""}`}
                                onClick={() => setTab("register")}
                            >
                                Create Account
                            </button>
                        </div>

                        {tab === "login" ? (
                            <form className="auth-card__form" onSubmit={handleLogin}>
                                <div className="auth-field">
                                    <label className="auth-field__label">Email</label>
                                    <input
                                        type="email"
                                        className="auth-field__input"
                                        value={loginEmail}
                                        onChange={(e) => setLoginEmail(e.target.value)}
                                        placeholder="you@example.com"
                                        required
                                        autoFocus
                                    />
                                </div>
                                <div className="auth-field">
                                    <label className="auth-field__label">Password</label>
                                    <input
                                        type="password"
                                        className="auth-field__input"
                                        value={loginPassword}
                                        onChange={(e) => setLoginPassword(e.target.value)}
                                        placeholder="••••••••"
                                        required
                                    />
                                </div>
                                {error && <p className="auth-card__error">{error}</p>}
                                <button type="submit" className="auth-card__submit" disabled={loading}>
                                    {loading ? "Signing in…" : "Sign In →"}
                                </button>
                                <p className="auth-card__footer-text">
                                    New here?{" "}
                                    <button type="button" className="auth-card__link" onClick={() => setTab("register")}>
                                        Create an account
                                    </button>
                                </p>
                            </form>
                        ) : (
                            <form className="auth-card__form" onSubmit={handleRegister}>
                                <div className="auth-field">
                                    <label className="auth-field__label">Username</label>
                                    <input
                                        type="text"
                                        className="auth-field__input"
                                        value={regUsername}
                                        onChange={(e) => setRegUsername(e.target.value)}
                                        placeholder="yourname"
                                        required
                                        autoFocus
                                    />
                                </div>
                                <div className="auth-field">
                                    <label className="auth-field__label">Email</label>
                                    <input
                                        type="email"
                                        className="auth-field__input"
                                        value={regEmail}
                                        onChange={(e) => setRegEmail(e.target.value)}
                                        placeholder="you@example.com"
                                        required
                                    />
                                </div>
                                <div className="auth-field">
                                    <label className="auth-field__label">Password</label>
                                    <input
                                        type="password"
                                        className="auth-field__input"
                                        value={regPassword}
                                        onChange={(e) => setRegPassword(e.target.value)}
                                        placeholder="Min. 6 characters"
                                        required
                                    />
                                </div>
                                {error && <p className="auth-card__error">{error}</p>}
                                <button type="submit" className="auth-card__submit" disabled={loading}>
                                    {loading ? "Creating account…" : "Create Account →"}
                                </button>
                                <p className="auth-card__footer-text">
                                    Already have an account?{" "}
                                    <button type="button" className="auth-card__link" onClick={() => setTab("login")}>
                                        Sign in
                                    </button>
                                </p>
                            </form>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
