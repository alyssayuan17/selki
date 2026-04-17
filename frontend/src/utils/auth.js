const TOKEN_KEY = "selki_token";

export function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn() {
    return !!getToken();
}

/**
 * Drop-in replacement for fetch() that adds the Authorization header
 * and redirects to /login on 401.
 */
export async function authedFetch(url, options = {}) {
    const token = getToken();
    const headers = {
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        clearToken();
        window.location.href = "/login";
        throw new Error("Session expired. Please log in again.");
    }

    return response;
}
