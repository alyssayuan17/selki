"""
Shared FastAPI dependencies.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import config

_bearer = HTTPBearer(auto_error=False)


def require_auth(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> None:
    """
    Validates the Bearer token against AUTH_PASSWORD.
    If AUTH_PASSWORD is not configured, auth is skipped (dev mode).
    """
    if not config.AUTH_PASSWORD:
        return  # dev mode — no password set

    if credentials is None or credentials.credentials != config.AUTH_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
