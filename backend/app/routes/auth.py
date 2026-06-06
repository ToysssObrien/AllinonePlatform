from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from pydantic import BaseModel

from ..db import get_user_by_username, verify_password

logger = logging.getLogger("omnidesk.auth")

router = APIRouter(tags=["auth"])

# --- In-memory session store ---
_sessions: dict[str, dict] = {}

SESSION_COOKIE_NAME = "omnidesk_session"
SESSION_MAX_AGE = 60 * 60 * 24  # 24 hours


class LoginPayload(BaseModel):
    username: str
    password: str


def _verify_credentials(username: str, password: str) -> dict | None:
    user = get_user_by_username(username)
    if not user or not user.get("is_active"):
        return None
    if not verify_password(password, str(user.get("password_hash") or "")):
        return None
    return user


def _create_session(user: dict) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "user_id": user["id"],
        "username": user["username"],
        "display_name": user.get("display_name") or user["username"],
        "role": user.get("role") or "Admin",
        "is_super_admin": bool(user.get("is_super_admin")),
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
    user = _verify_credentials(payload.username, payload.password)
    if not user:
        logger.warning("Failed login attempt for user: %s", payload.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = _create_session(user)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE,
    )
    logger.info("User '%s' logged in successfully", user["username"])
    return {
        "status": "ok",
        "username": user["username"],
        "display_name": user.get("display_name") or user["username"],
        "role": user.get("role") or "Admin",
        "is_super_admin": bool(user.get("is_super_admin")),
    }


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
        "id": user.get("user_id"),
        "username": user["username"],
        "display_name": user.get("display_name") or user["username"],
        "role": user.get("role") or "Admin",
        "is_super_admin": bool(user.get("is_super_admin")),
    }
