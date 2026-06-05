from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request

from ..db import (
    get_account,
    get_account_by_page_id,
    list_accounts,
    add_account,
    delete_account,
    update_account_login_state,
    update_account_profile,
)
from ..schemas import (
    AccountCreate,
    AccountUpdate,
    ConfirmCodePayload,
    ConfirmPasswordPayload,
    FacebookConnectPayload,
    FacebookConnectPagePayload,
    RequestCodePayload,
    SyncPayload,
)
from ..telegram_gateway import TelegramGateway, build_session_path
from ..facebook_gateway import FacebookGateway
from .. import facebook_oauth

logger = logging.getLogger("omnidesk.accounts")

# Temporary storage for OAuth state tokens (in production, use Redis or DB)
_oauth_states: dict[str, float] = {}

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

# These are set by main.py at startup.
_gateway: TelegramGateway | None = None
_fb_gateway: FacebookGateway | None = None
_media_dir_str: str = ""
_broadcast = None


def configure(*, gateway: TelegramGateway, fb_gateway: FacebookGateway, media_dir: str, broadcast) -> None:
    """Called once during app startup to inject shared dependencies."""
    global _gateway, _fb_gateway, _media_dir_str, _broadcast
    _gateway = gateway
    _fb_gateway = fb_gateway
    _media_dir_str = media_dir
    _broadcast = broadcast


@router.get("")
def api_accounts() -> list[dict]:
    return list_accounts()


@router.post("")
def api_create_account(payload: AccountCreate) -> dict:
    account = add_account(payload.display_name, payload.phone, payload.platform)
    if payload.api_id or payload.api_hash:
        account = update_account_profile(
            account["id"],
            api_id=payload.api_id,
            api_hash=payload.api_hash,
            session_path=account.get("session_path") or build_session_path(account["id"]),
        )
    if payload.page_access_token or payload.page_id or payload.fb_app_secret:
        account = update_account_profile(
            account["id"],
            page_access_token=payload.page_access_token,
            page_id=payload.page_id,
            fb_app_secret=payload.fb_app_secret,
        )
    return account


@router.get("/{account_id}")
def api_account(account_id: int) -> dict:
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/{account_id}")
def api_update_account(account_id: int, payload: AccountUpdate) -> dict:
    account = update_account_profile(
        account_id,
        display_name=payload.display_name,
        platform=payload.platform,
        phone=payload.phone,
        api_id=payload.api_id,
        api_hash=payload.api_hash,
        page_access_token=payload.page_access_token,
        page_id=payload.page_id,
        fb_app_secret=payload.fb_app_secret,
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/{account_id}")
async def api_delete_account(account_id: int) -> dict:
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Close any active Telegram client
    if account.get("api_id") and account.get("api_hash") and account.get("session_path"):
        try:
            await _gateway.close_client(
                api_id=account["api_id"],
                api_hash=account["api_hash"],
                session_path=account["session_path"],
            )
        except Exception as e:
            logger.warning("Failed to close client for account %d: %s", account_id, e)

    deleted = delete_account(account_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete account")

    if _broadcast:
        await _broadcast({"type": "account:deleted", "account_id": account_id})

    return {"status": "deleted", "account_id": account_id}


@router.post("/{account_id}/login/request-code")
async def api_request_login_code(account_id: int, payload: RequestCodePayload) -> dict:
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    phone = payload.phone or account.get("phone") or account.get("login_phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")
    if account.get("platform") != "telegram":
        raise HTTPException(status_code=400, detail="Telegram login is only available for Telegram accounts")
    if not account.get("api_id") or not account.get("api_hash"):
        raise HTTPException(status_code=400, detail="api_id and api_hash are required")

    session_path = account.get("session_path") or build_session_path(account_id)
    update_account_profile(account_id, phone=phone, session_path=session_path)

    try:
        result = await _gateway.request_login_code(
            api_id=account["api_id"],
            api_hash=account["api_hash"],
            session_path=session_path,
            phone=phone,
        )
    except Exception as error:
        logger.warning("Login code request failed for account %d: %s", account_id, error)
        update_account_login_state(account_id, status="error", phone=phone, last_error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error

    update_account_login_state(
        account_id,
        status="code_sent",
        phone=phone,
        phone_code_hash=result.phone_code_hash,
        clear_error=True,
    )
    return {"status": "code_sent", "phone": phone}


@router.post("/{account_id}/login/confirm-code")
async def api_confirm_login_code(account_id: int, payload: ConfirmCodePayload) -> dict:
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    phone = payload.phone or account.get("login_phone") or account.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required")
    if account.get("platform") != "telegram":
        raise HTTPException(status_code=400, detail="Telegram login is only available for Telegram accounts")
    if not account.get("api_id") or not account.get("api_hash"):
        raise HTTPException(status_code=400, detail="api_id and api_hash are required")
    if not account.get("session_path"):
        raise HTTPException(status_code=400, detail="Session path is missing")

    try:
        result = await _gateway.confirm_login_code(
            api_id=account["api_id"],
            api_hash=account["api_hash"],
            session_path=account["session_path"],
            phone=phone,
            code=payload.code,
            phone_code_hash=account.get("phone_code_hash"),
        )
    except Exception as error:
        logger.warning("Login code confirm failed for account %d: %s", account_id, error)
        update_account_login_state(account_id, status="error", phone=phone, last_error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error

    if result.mode == "password_needed":
        update_account_login_state(account_id, status="2fa_required", phone=phone, clear_error=True)
        return {"status": "2fa_required"}

    await _gateway.ensure_live_updates(
        api_id=account["api_id"],
        api_hash=account["api_hash"],
        session_path=account["session_path"],
        account_id=account_id,
    )

    update_account_login_state(
        account_id,
        status="authorized",
        phone=phone,
        phone_code_hash=None,
        clear_error=True,
    )
    return {"status": "authorized"}


@router.post("/{account_id}/login/confirm-password")
async def api_confirm_login_password(account_id: int, payload: ConfirmPasswordPayload) -> dict:
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if not account.get("api_id") or not account.get("api_hash"):
        raise HTTPException(status_code=400, detail="api_id and api_hash are required")
    if not account.get("session_path"):
        raise HTTPException(status_code=400, detail="Session path is missing")
    if account.get("platform") != "telegram":
        raise HTTPException(status_code=400, detail="Telegram password flow is only available for Telegram accounts")

    try:
        await _gateway.confirm_2fa_password(
            api_id=account["api_id"],
            api_hash=account["api_hash"],
            session_path=account["session_path"],
            password=payload.password,
        )
    except Exception as error:
        logger.warning("2FA password confirm failed for account %d: %s", account_id, error)
        update_account_login_state(account_id, status="2fa_required", last_error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error

    update_account_login_state(
        account_id,
        status="authorized",
        phone_code_hash=None,
        clear_error=True,
    )
    await _gateway.ensure_live_updates(
        api_id=account["api_id"],
        api_hash=account["api_hash"],
        session_path=account["session_path"],
        account_id=account_id,
    )
    return {"status": "authorized"}


@router.post("/{account_id}/sync")
async def api_sync_account(account_id: int, payload: SyncPayload | None = None) -> dict:
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.get("platform") != "telegram":
        raise HTTPException(status_code=400, detail="Sync is only available for Telegram accounts")
    if not account.get("api_id") or not account.get("api_hash") or not account.get("session_path"):
        raise HTTPException(status_code=400, detail="Telegram credentials are incomplete")

    full_history = bool(payload.full_history) if payload else False
    dialog_limit = None if full_history else 20
    message_limit = None if full_history else 20

    async def run_sync() -> None:
        try:
            try:
                await _gateway.ensure_live_updates(
                    api_id=account["api_id"],
                    api_hash=account["api_hash"],
                    session_path=account["session_path"],
                    account_id=account_id,
                )
            except Exception as live_err:
                logger.warning("ensure_live_updates failed (non-fatal, sync continues): %s", live_err)

            await _gateway.sync_recent_inbox(
                api_id=account["api_id"],
                api_hash=account["api_hash"],
                session_path=account["session_path"],
                account_id=account_id,
                media_root=_media_dir_str,
                dialog_limit=dialog_limit,
                message_limit=message_limit,
                include_archived=full_history,
            )
            logger.info("Sync completed for account %d", account_id)
            update_account_login_state(account_id, status="authorized", clear_error=True)
        except Exception as error:
            logger.error("Sync failed for account %d: %s", account_id, error, exc_info=True)
            # Don't change auth status for non-auth errors (e.g. database locked)
            err_str = str(error).lower()
            if "database is locked" in err_str or "operational" in err_str:
                update_account_login_state(account_id, last_error=str(error))
            else:
                update_account_login_state(account_id, status="error", last_error=str(error))

    task = asyncio.create_task(run_sync())
    return {"status": "queued", "task": task.get_name(), "full_history": full_history}


@router.post("/{account_id}/facebook/connect")
async def api_facebook_connect(account_id: int, payload: FacebookConnectPayload) -> dict:
    """Connect a Facebook Page by setting the Page Access Token."""
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.get("platform") != "facebook_page":
        raise HTTPException(status_code=400, detail="This endpoint is only for Facebook Page accounts")

    page_id = payload.page_id

    # If page_id not provided, try to fetch it from the token
    if not page_id and payload.page_access_token:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://graph.facebook.com/v21.0/me",
                    params={"access_token": payload.page_access_token, "fields": "id,name"},
                )
                if response.status_code == 200:
                    data = response.json()
                    page_id = data.get("id")
                    # Optionally update display name if it's still default
                    page_name = data.get("name")
                    if page_name and account.get("display_name", "").startswith("Support"):
                        update_account_profile(account_id, display_name=page_name)
                else:
                    error_msg = response.json().get("error", {}).get("message", response.text)
                    raise HTTPException(status_code=400, detail=f"Invalid token: {error_msg}")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"Could not verify token: {e}") from e

    updated = update_account_profile(
        account_id,
        page_access_token=payload.page_access_token,
        page_id=page_id,
        fb_app_secret=payload.fb_app_secret,
    )
    update_account_login_state(account_id, status="authorized", clear_error=True)

    return {"status": "connected", "account": updated, "page_id": page_id}


@router.post("/{account_id}/facebook/sync")
async def api_facebook_sync(account_id: int) -> dict:
    """Sync recent conversations from a Facebook Page."""
    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.get("platform") != "facebook_page":
        raise HTTPException(status_code=400, detail="Sync is only for Facebook Page accounts")
    if not account.get("page_access_token"):
        raise HTTPException(status_code=400, detail="Page Access Token is required. Connect the page first.")
    if not account.get("page_id"):
        raise HTTPException(status_code=400, detail="Page ID is missing. Reconnect the page.")

    from pathlib import Path

    async def run_fb_sync() -> None:
        try:
            await _fb_gateway.sync_conversations(
                page_access_token=account["page_access_token"],
                page_id=account["page_id"],
                account_id=account_id,
                media_dir=Path(_media_dir_str),
            )
            update_account_login_state(account_id, status="authorized", clear_error=True)
        except Exception as error:
            logger.error("Facebook sync failed for account %d: %s", account_id, error, exc_info=True)
            update_account_login_state(account_id, status="error", last_error=str(error))

    task = asyncio.create_task(run_fb_sync())
    return {"status": "queued", "task": task.get_name()}


# ------------------------------------------------------------------
# Facebook OAuth endpoints
# ------------------------------------------------------------------

@router.get("/facebook/oauth/check")
def api_facebook_oauth_check() -> dict:
    """Check if Facebook OAuth is configured (FB_APP_ID & FB_APP_SECRET set)."""
    return {"configured": facebook_oauth.is_configured()}


@router.get("/facebook/oauth/start")
def api_facebook_oauth_start(request: "Request") -> "RedirectResponse":
    """Start Facebook OAuth flow — redirect user to Facebook Login."""
    from fastapi.responses import RedirectResponse
    from starlette.requests import Request as StarletteRequest

    if not facebook_oauth.is_configured():
        raise HTTPException(status_code=400, detail="Facebook OAuth is not configured. Set FB_APP_ID and FB_APP_SECRET.")

    # Build redirect URI from the current request
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", "localhost:8000"))
    redirect_uri = f"{scheme}://{host}/api/accounts/facebook/oauth/callback"

    state = facebook_oauth.generate_state_token()
    import time
    _oauth_states[state] = time.time()

    # Clean old states (> 10 min)
    cutoff = time.time() - 600
    for key in list(_oauth_states):
        if _oauth_states[key] < cutoff:
            del _oauth_states[key]

    login_url = facebook_oauth.get_login_url(redirect_uri, state)
    return RedirectResponse(url=login_url, status_code=302)


@router.get("/facebook/oauth/callback")
async def api_facebook_oauth_callback(code: str = "", state: str = "", error: str = "") -> "RedirectResponse":
    """Handle Facebook OAuth callback — exchange code for token and redirect to UI."""
    from fastapi.responses import RedirectResponse
    from urllib.parse import urlencode
    import time

    if error:
        params = urlencode({"fb_oauth_error": error})
        return RedirectResponse(url=f"/?{params}#/accounts", status_code=302)

    if not code:
        return RedirectResponse(url="/?fb_oauth_error=no_code#/accounts", status_code=302)

    # Validate state token
    if state not in _oauth_states:
        return RedirectResponse(url="/?fb_oauth_error=invalid_state#/accounts", status_code=302)
    del _oauth_states[state]

    try:
        # Reconstruct redirect_uri (must match the one used in /start)
        import os
        base_url = os.environ.get("OMNIDESK_BASE_URL", "http://localhost:8000")
        redirect_uri = f"{base_url}/api/accounts/facebook/oauth/callback"

        # Exchange code for short-lived token
        token_data = await facebook_oauth.exchange_code_for_token(code, redirect_uri)
        short_token = token_data["access_token"]

        # Get long-lived token
        long_lived_data = await facebook_oauth.get_long_lived_token(short_token)
        user_token = long_lived_data["access_token"]

        # Redirect back to UI with token (params before hash for JS access)
        params = urlencode({"fb_user_token": user_token})
        return RedirectResponse(url=f"/?{params}#/accounts", status_code=302)

    except Exception as e:
        logger.error("Facebook OAuth callback error: %s", e, exc_info=True)
        params = urlencode({"fb_oauth_error": str(e)[:200]})
        return RedirectResponse(url=f"/?{params}#/accounts", status_code=302)


@router.get("/facebook/pages")
async def api_facebook_list_pages(fb_user_token: str = "") -> dict:
    """List all Facebook Pages managed by the authenticated user."""
    if not fb_user_token:
        raise HTTPException(status_code=400, detail="fb_user_token is required")

    try:
        pages = await facebook_oauth.list_managed_pages(fb_user_token)
        user_info = await facebook_oauth.get_user_info(fb_user_token)
        return {
            "pages": pages,
            "user": user_info,
        }
    except Exception as e:
        logger.error("Failed to list Facebook pages: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/facebook/connect-page")
async def api_facebook_connect_page(payload: FacebookConnectPagePayload) -> dict:
    """Connect a Facebook Page by selecting it from the OAuth page list.
    Creates a new account or updates an existing one."""
    if not payload.fb_user_token or not payload.page_id:
        raise HTTPException(status_code=400, detail="fb_user_token and page_id are required")

    try:
        # Get all managed pages to find the selected one
        pages = await facebook_oauth.list_managed_pages(payload.fb_user_token)
        selected_page = None
        for page in pages:
            if str(page["id"]) == str(payload.page_id):
                selected_page = page
                break

        if not selected_page:
            raise HTTPException(status_code=404, detail="Page not found. Make sure you have admin access to this page.")

        page_access_token = selected_page["access_token"]
        page_name = payload.page_name or selected_page.get("name", f"Page {payload.page_id}")

        # Check if an account for this page already exists
        existing = get_account_by_page_id(payload.page_id)
        if existing:
            # Update existing account with fresh token
            updated = update_account_profile(
                existing["id"],
                display_name=page_name,
                page_access_token=page_access_token,
                page_id=payload.page_id,
            )
            update_account_login_state(existing["id"], status="authorized", clear_error=True)
            return {"status": "updated", "account": updated, "page_id": payload.page_id}

        # Create new account
        account = add_account(page_name, phone=None, platform="facebook_page")
        updated = update_account_profile(
            account["id"],
            page_access_token=page_access_token,
            page_id=payload.page_id,
        )
        update_account_login_state(account["id"], status="authorized", clear_error=True)

        if _broadcast:
            await _broadcast({"type": "account:created", "account": updated})

        return {"status": "created", "account": updated, "page_id": payload.page_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Facebook connect page error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
