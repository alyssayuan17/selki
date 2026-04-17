"""
Application configuration loaded from environment variables.
"""
import os

# Password required to access the API.
# Set AUTH_PASSWORD in your environment before deploying.
# If unset, auth is disabled (dev mode only).
AUTH_PASSWORD: str | None = os.environ.get("AUTH_PASSWORD")

# Comma-separated list of allowed CORS origins.
# Example: "https://selki.example.com,https://www.selki.example.com"
# Defaults to "*" if unset (dev mode).
_cors_raw = os.environ.get("CORS_ORIGINS", "")
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()] or ["*"]
