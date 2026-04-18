"""
Auth endpoints.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import config

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    """
    Validate the shared password and return a Bearer token.
    If AUTH_PASSWORD is not set (dev mode), any password is accepted.
    """
    if config.AUTH_PASSWORD and body.password != config.AUTH_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    # The token IS the password — the backend validates it on every request.
    token = body.password if config.AUTH_PASSWORD else "dev"
    return LoginResponse(token=token)
