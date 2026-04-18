import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { setToken } from "../../utils/auth";
import "./LoginPage.css";

export default function LoginPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const [password, setPassword] = useState("");
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const from = location.state?.from || "/";

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const response = await fetch("/api/v1/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password }),
            });

            if (!response.ok) {
                setError("Incorrect password.");
                setLoading(false);
                return;
            }

            const data = await response.json();
            setToken(data.token);
            navigate(from, { replace: true });
        } catch {
            setError("Could not connect to server.");
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-card">
                <div className="login-logo">
                    Selki
                    <img src="/selki_logo_v2.svg" alt="Selki logo" className="login-logo__icon" />
                </div>
                <h1 className="login-title">Sign in</h1>
                <form onSubmit={handleSubmit} className="login-form">
                    <input
                        type="password"
                        className="login-input"
                        placeholder="Password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoFocus
                        required
                    />
                    {error && <p className="login-error">{error}</p>}
                    <button type="submit" className="login-btn" disabled={loading || !password}>
                        {loading ? "Signing in..." : "Sign in"}
                    </button>
                </form>
            </div>
        </div>
    );
}
