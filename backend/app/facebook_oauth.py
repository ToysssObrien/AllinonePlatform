from __future__ import annotations

import logging
import os
import secrets
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger("omnidesk.facebook_oauth")

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
OAUTH_DIALOG_URL = "https://www.facebook.com/v21.0/dialog/oauth"

# Required permissions for managing Pages and messaging
OAUTH_SCOPES = [
    "pages_show_list",
    "pages_messaging",
    "pages_read_engagement",
    "pages_manage_metadata",
]


def _app_id() -> str:
    return os.environ.get("FB_APP_ID", "")


def _app_secret() -> str:
    return os.environ.get("FB_APP_SECRET", "")


def is_configured() -> bool:
    """Return True if FB_APP_ID and FB_APP_SECRET are set."""
    return bool(_app_id() and _app_secret())


def generate_state_token() -> str:
    """Generate a CSRF state token for OAuth flow."""
    return secrets.token_urlsafe(32)


def get_login_url(redirect_uri: str, state: str) -> str:
    """Build the Facebook OAuth login URL."""
    params = {
        "client_id": _app_id(),
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": ",".join(OAUTH_SCOPES),
        "response_type": "code",
    }
    return f"{OAUTH_DIALOG_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange an authorization code for a short-lived User Access Token."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "client_id": _app_id(),
                "client_secret": _app_secret(),
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        data = response.json()
        if response.status_code != 200 or "error" in data:
            error_msg = data.get("error", {}).get("message", response.text)
            raise RuntimeError(f"Token exchange failed: {error_msg}")
        return data  # {"access_token": "...", "token_type": "bearer", "expires_in": ...}


async def get_long_lived_token(short_lived_token: str) -> dict[str, Any]:
    """Exchange a short-lived token for a long-lived User Access Token (~60 days)."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": _app_id(),
                "client_secret": _app_secret(),
                "fb_exchange_token": short_lived_token,
            },
        )
        data = response.json()
        if response.status_code != 200 or "error" in data:
            error_msg = data.get("error", {}).get("message", response.text)
            raise RuntimeError(f"Long-lived token exchange failed: {error_msg}")
        return data


async def list_managed_pages(user_access_token: str) -> list[dict[str, Any]]:
    """Fetch all Pages managed by the user. Returns Page Access Tokens that don't expire."""
    pages: list[dict[str, Any]] = []
    url = f"{GRAPH_API_BASE}/me/accounts"
    params: dict[str, str] = {
        "fields": "id,name,access_token,category,picture.type(small){url}",
        "limit": "100",
        "access_token": user_access_token,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        while url:
            response = await client.get(url, params=params)
            data = response.json()

            if response.status_code != 200 or "error" in data:
                error_msg = data.get("error", {}).get("message", response.text)
                raise RuntimeError(f"Failed to list pages: {error_msg}")

            for page in data.get("data", []):
                pages.append({
                    "id": page["id"],
                    "name": page.get("name", f"Page {page['id']}"),
                    "access_token": page.get("access_token", ""),
                    "category": page.get("category", ""),
                    "picture_url": page.get("picture", {}).get("data", {}).get("url", ""),
                })

            # Handle pagination
            next_url = data.get("paging", {}).get("next")
            if next_url:
                url = next_url
                params = {}  # params are embedded in the next URL
            else:
                break

    return pages


async def get_user_info(user_access_token: str) -> dict[str, Any]:
    """Get basic info about the logged-in Facebook user."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{GRAPH_API_BASE}/me",
            params={
                "fields": "id,name,email",
                "access_token": user_access_token,
            },
        )
        data = response.json()
        if response.status_code != 200 or "error" in data:
            error_msg = data.get("error", {}).get("message", response.text)
            raise RuntimeError(f"Failed to get user info: {error_msg}")
        return data
