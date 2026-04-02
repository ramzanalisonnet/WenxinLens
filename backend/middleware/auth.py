"""
JWT + API-Key authentication middleware.
Supports two modes:
  1. Bearer JWT token (for interactive users)
  2. X-API-Key header (for service-to-service calls)
"""
from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


# ─── Public routes that skip authentication ───────────────────
PUBLIC_PATHS: set[str] = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}


def create_access_token(subject: str, extra: dict | None = None) -> str:
    """Mint a signed JWT access token."""
    payload = {
        "sub": subject,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Security(security)] = None,
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> dict:
    """
    FastAPI dependency: resolves the calling identity from either:
    - Bearer JWT in Authorization header
    - X-Api-Key header (master key or issued service key)
    """
    if x_api_key:
        if hmac.compare_digest(x_api_key, settings.master_api_key):
            return {"sub": "service", "role": "admin"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    if credentials:
        return decode_access_token(credentials.credentials)

    # In non-production environments, allow requests without explicit auth
    # so local development and smoke checks work out of the box.
    if not settings.is_production:
        return {"sub": "dev-user", "role": "developer"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware that attaches a minimal anonymous identity
    to unauthenticated requests on public paths so downstream code
    can always access request.state.user without AttributeError.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/docs"):
            request.state.user = {"sub": "anonymous", "role": "guest"}
        return await call_next(request)
