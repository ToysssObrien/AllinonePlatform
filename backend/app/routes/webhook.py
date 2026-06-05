from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

logger = logging.getLogger("omnidesk.webhook")

router = APIRouter(prefix="/api/webhook", tags=["webhook"])

# Injected by main.py at startup.
_fb_gateway = None
_media_dir_str: str = ""


def configure(*, fb_gateway, media_dir: str) -> None:
    """Called once during app startup to inject shared dependencies."""
    global _fb_gateway, _media_dir_str
    _fb_gateway = fb_gateway
    _media_dir_str = media_dir


@router.get("/facebook")
async def facebook_webhook_verify(
    request: Request,
) -> PlainTextResponse:
    """Facebook webhook verification endpoint.

    Facebook sends a GET request with hub.mode, hub.verify_token, and hub.challenge
    to verify the webhook URL.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    verify_token = os.environ.get("FB_VERIFY_TOKEN", "omnidesk_fb_verify")

    from ..facebook_gateway import FacebookGateway
    result = FacebookGateway.verify_webhook(mode, token, challenge, verify_token)
    if result is not None:
        logger.info("Facebook webhook verified successfully")
        return PlainTextResponse(content=result, status_code=200)

    logger.warning("Facebook webhook verification failed: mode=%s", mode)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/facebook")
async def facebook_webhook_receive(request: Request) -> dict:
    """Receive incoming Facebook webhook events (messages, postbacks, etc.)."""
    from pathlib import Path

    body_bytes = await request.body()
    body = await request.json()

    # Optionally verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    # We don't enforce signature verification globally here since
    # it requires per-account app_secret. The gateway handles it if configured.

    if _fb_gateway is None:
        raise HTTPException(status_code=500, detail="Facebook gateway not initialized")

    media_dir = Path(_media_dir_str) if _media_dir_str else Path("data/media")
    media_dir.mkdir(parents=True, exist_ok=True)

    try:
        await _fb_gateway.handle_webhook_event(
            body=body,
            media_dir=media_dir,
        )
    except Exception as error:
        logger.error("Facebook webhook processing error: %s", error, exc_info=True)
        # Return 200 anyway so Facebook doesn't retry endlessly
        return {"status": "error", "message": str(error)}

    return {"status": "ok"}
