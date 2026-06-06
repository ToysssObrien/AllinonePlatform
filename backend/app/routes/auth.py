from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

logger = logging.getLogger("omnidesk.auth")

router = APIRouter(tags=["auth"])

# --- Admin credentials from environment variables ---
# Set ADMIN_USERNAME and ADMIN_PASSWORD in your environment (Render dashboard).
# Falls back to "Admin" / "123456" for local development only.
_raw_password = os.environ.get("ADMIN_PASSWORD", "123456")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "Admin")
ADMIN_DISPLAY_NAME = os.environ.get("ADMIN_DISPLAY_NAME", ADMIN_USERNAME)
ADMIN_ROLE = "Admin Account"
ADMIN_PASSWORD_HASH = hashlib.sha256(_raw_password.encode()).hexdigest()

# --- In-memory session store ---
_sessions: dict[str, dict] = {}

SESSION_COOKIE_NAME = "omnidesk_session"
SESSION_MAX_AGE = 60 * 60 * 24  # 24 hours


class LoginPayload(BaseModel):
    username: str
    password: str


def _verify_credentials(username: str, password: str) -> bool:
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH


def _create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "username": username,
        "display_name": ADMIN_DISPLAY_NAME if username == ADMIN_USERNAME else username,
        "role": ADMIN_ROLE,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return token


def get_current_user(session_token: str | None) -> dict | None:
    """Return user info if session is valid, else None."""
    if not session_token:
        return None
    session = _sessions.get(session_token)
    if not session:
        return None
    return session


def is_authenticated(request: Request) -> bool:
    """Check if the request has a valid session cookie."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return get_current_user(token) is not None


@router.post("/api/auth/login")
async def api_login(payload: LoginPayload, response: Response) -> dict:
    if not _verify_credentials(payload.username, payload.password):
        logger.warning("Failed login attempt for user: %s", payload.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = _create_session(payload.username)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )
    logger.info("User '%s' logged in successfully", payload.username)
    return {"status": "ok", "username": payload.username, "display_name": ADMIN_DISPLAY_NAME, "role": ADMIN_ROLE}


@router.post("/api/auth/logout")
async def api_logout(
    response: Response,
    omnidesk_session: str | None = Cookie(None),
) -> dict:
    if omnidesk_session and omnidesk_session in _sessions:
        del _sessions[omnidesk_session]
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    logger.info("User logged out")
    return {"status": "ok"}


@router.get("/api/auth/me")
async def api_me(omnidesk_session: str | None = Cookie(None)) -> dict:
    user = get_current_user(omnidesk_session)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "username": user["username"],
        "display_name": user.get("display_name") or user["username"],
        "role": user.get("role") or ADMIN_ROLE,
    }
