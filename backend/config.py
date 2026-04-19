"""
Application configuration loaded from environment variables.

Automatically reads a .env file in the project root if present.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (two levels up from backend/)
load_dotenv(Path(__file__).parent.parent / ".env")

# Password required to access the API.
# Set AUTH_PASSWORD in your environment before deploying.
# If unset, auth is disabled (dev mode only).
AUTH_PASSWORD: str | None = os.environ.get("AUTH_PASSWORD")

# Comma-separated list of allowed CORS origins.
# Example: "https://selki.example.com,https://www.selki.example.com"
# Defaults to "*" if unset (dev mode).
_cors_raw = os.environ.get("CORS_ORIGINS", "https://selki.us")
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()] or ["https://selki.us"]
