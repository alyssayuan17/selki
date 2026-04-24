import { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import "./AuthModal.css";

export default function AuthModal({ onClose, defaultTab = "login" }) {
    const { login, register } = useAuth();
    const [tab, setTab] = useState(defaultTab);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Login fields
    const [loginEmail, setLoginEmail] = useState("");
    const [loginPassword, setLoginPassword] = useState("");

    // Register fields
    const [regUsername, setRegUsername] = useState("");
    const [regEmail, setRegEmail] = useState("");
    const [regPassword, setRegPassword] = useState("");

    useEffect(() => {
        setError(null);
    }, [tab]);

    // Close on Escape
    useEffect(() => {
        const handler = (e) => { if (e.key === "Escape") onClose(); };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [onClose]);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await login(loginEmail, loginPassword);
            onClose();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        if (regPassword.length < 6) { setError("Password must be at least 6 characters"); return; }
        setLoading(true);
        setError(null);
        try {
            await register(regUsername, regEmail, regPassword);
            onClose();
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
            <div className="auth-modal">
                <div className="auth-modal__macbar">
                    <span className="auth-modal__dot auth-modal__dot--red" onClick={onClose} />
                    <span className="auth-modal__dot auth-modal__dot--yellow" />
                    <span className="auth-modal__dot auth-modal__dot--green" />
                </div>

                <div className="auth-modal__logo">
                    <img src="/selki_logo_v2.svg" alt="Selki" className="auth-modal__logo-img" />
                    <span className="auth-modal__logo-text">selki</span>
                </div>

                <div className="auth-modal__tabs">
                    <button
                        className={`auth-modal__tab${tab === "login" ? " auth-modal__tab--active" : ""}`}
                        onClick={() => setTab("login")}
                    >
                        Sign In
                    </button>
                    <button
                        className={`auth-modal__tab${tab === "register" ? " auth-modal__tab--active" : ""}`}
                        onClick={() => setTab("register")}
                    >
                        Create Account
                    </button>
                </div>

                {tab === "login" ? (
                    <form className="auth-modal__form" onSubmit={handleLogin}>
                        <div className="auth-modal__field">
                            <label className="auth-modal__label">Email</label>
                            <input
                                type="email"
                                className="auth-modal__input"
                                value={loginEmail}
                                onChange={(e) => setLoginEmail(e.target.value)}
                                placeholder="you@example.com"
                                required
                                autoFocus
                            />
                        </div>
                        <div className="auth-modal__field">
                            <label className="auth-modal__label">Password</label>
                            <input
                                type="password"
                                className="auth-modal__input"
                                value={loginPassword}
                                onChange={(e) => setLoginPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                            />
                        </div>
                        {error && <p className="auth-modal__error">{error}</p>}
                        <button type="submit" className="auth-modal__submit" disabled={loading}>
                            {loading ? "Signing in…" : "Sign In"}
                        </button>
                        <p className="auth-modal__switch">
                            New to Selki?{" "}
                            <button type="button" className="auth-modal__switch-link" onClick={() => setTab("register")}>
                                Create an account
                            </button>
                        </p>
                    </form>
                ) : (
                    <form className="auth-modal__form" onSubmit={handleRegister}>
                        <div className="auth-modal__field">
                            <label className="auth-modal__label">Username</label>
                            <input
                                type="text"
                                className="auth-modal__input"
                                value={regUsername}
                                onChange={(e) => setRegUsername(e.target.value)}
                                placeholder="yourname"
                                required
                                autoFocus
                            />
                        </div>
                        <div className="auth-modal__field">
                            <label className="auth-modal__label">Email</label>
                            <input
                                type="email"
                                className="auth-modal__input"
                                value={regEmail}
                                onChange={(e) => setRegEmail(e.target.value)}
                                placeholder="you@example.com"
                                required
                            />
                        </div>
                        <div className="auth-modal__field">
                            <label className="auth-modal__label">Password</label>
                            <input
                                type="password"
                                className="auth-modal__input"
                                value={regPassword}
                                onChange={(e) => setRegPassword(e.target.value)}
                                placeholder="Min. 6 characters"
                                required
                            />
                        </div>
                        {error && <p className="auth-modal__error">{error}</p>}
                        <button type="submit" className="auth-modal__submit" disabled={loading}>
                            {loading ? "Creating account…" : "Create Account"}
                        </button>
                        <p className="auth-modal__switch">
                            Already have an account?{" "}
                            <button type="button" className="auth-modal__switch-link" onClick={() => setTab("login")}>
                                Sign in
                            </button>
                        </p>
                    </form>
                )}
            </div>
        </div>
    );
}
