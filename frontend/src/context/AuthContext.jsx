import { createContext, useContext, useState, useCallback } from "react";
import { getToken, setToken as storeToken, clearToken } from "../utils/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [token, setTokenState] = useState(() => getToken());
    const [user, setUser] = useState(() => {
        const stored = localStorage.getItem("selki_user");
        try { return stored ? JSON.parse(stored) : null; } catch { return null; }
    });

    const login = useCallback(async (email, password) => {
        const res = await fetch("/api/v1/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Login failed");
        }
        const data = await res.json();
        storeToken(data.token);
        const u = { user_id: data.user_id, username: data.username, email: data.email };
        localStorage.setItem("selki_user", JSON.stringify(u));
        setTokenState(data.token);
        setUser(u);
    }, []);

    const register = useCallback(async (username, email, password) => {
        const res = await fetch("/api/v1/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Registration failed");
        }
        const data = await res.json();
        storeToken(data.token);
        const u = { user_id: data.user_id, username: data.username, email: data.email };
        localStorage.setItem("selki_user", JSON.stringify(u));
        setTokenState(data.token);
        setUser(u);
    }, []);

    const logout = useCallback(() => {
        clearToken();
        localStorage.removeItem("selki_user");
        setTokenState(null);
        setUser(null);
    }, []);

    const authedFetch = useCallback(async (url, options = {}) => {
        const currentToken = getToken();
        const headers = {
            ...(options.headers || {}),
            ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
        };
        return fetch(url, { ...options, headers });
    }, []);

    return (
        <AuthContext.Provider value={{ token, user, login, logout, register, authedFetch, isLoggedIn: !!token }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
