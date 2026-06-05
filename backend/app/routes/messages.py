from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..db import (
    get_account,
    get_chat,
    get_message,
    delete_message,
    infer_read_receipts_from_incoming,
    list_messages,
    save_message,
    update_account_login_state,
    update_message_delivery,
)
from ..schemas import DeleteMessagePayload, ForwardPayload
from ..attachment import (
    attachment_fallback_text,
    persist_upload,
    resolve_attachment_file_path,
    resolve_message_attachment_file_path,
    user_facing_error,
)
from ..telegram_gateway import TelegramGateway
from ..facebook_gateway import FacebookGateway

logger = logging.getLogger("omnidesk.messages")

router = APIRouter(tags=["messages"])

# Injected by main.py at startup.
_gateway: TelegramGateway | None = None
_fb_gateway: FacebookGateway | None = None
_broadcast: Callable[[dict[str, Any]], Awaitable[None]] | None = None


def configure(*, gateway: TelegramGateway, fb_gateway: FacebookGateway, broadcast: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
    """Called once during app startup to inject shared dependencies."""
    global _gateway, _fb_gateway, _broadcast
    _gateway = gateway
    _fb_gateway = fb_gateway
    _broadcast = broadcast


@router.get("/api/messages")
def api_messages(chat_id: int) -> list[dict]:
    infer_read_receipts_from_incoming(chat_id)
    return list_messages(chat_id)


def _telegram_delete_missing(error_message: str) -> bool:
    normalized = error_message.lower()
    return "not found" in normalized or "message id" in normalized and "invalid" in normalized


@router.delete("/api/messages/{message_id}")
async def api_delete_message(message_id: int, payload: DeleteMessagePayload | None = None) -> dict:
    payload = payload or DeleteMessagePayload()
    message = get_message(message_id)
    if not message:
        fallback_chat = get_chat(payload.chat_id) if payload.chat_id else None
        fallback_account = get_account(payload.account_id) if payload.account_id else None
        if fallback_chat and fallback_account and payload.delete_for_everyone and payload.telegram_message_id:
            is_fallback_telegram = bool(
                fallback_account.get("platform") == "telegram"
                and fallback_account.get("api_id")
                and fallback_account.get("api_hash")
                and fallback_account.get("session_path")
            )
            if is_fallback_telegram:
                try:
                    await asyncio.wait_for(
                        _gateway.delete_message(
                            api_id=fallback_account.get("api_id"),
                            api_hash=fallback_account.get("api_hash"),
                            session_path=fallback_account.get("session_path"),
                            chat_external_id=str(fallback_chat["external_chat_id"]),
                            telegram_message_id=str(payload.telegram_message_id),
                            revoke=True,
                        ),
                        timeout=35,
                    )
                except Exception as error:
                    error_message = user_facing_error(error)
                    if not _telegram_delete_missing(error_message):
                        raise HTTPException(status_code=409, detail=error_message) from error
        if _broadcast and fallback_chat and fallback_account:
            await _broadcast(
                {
                    "type": "message:deleted",
                    "source": "already-deleted",
                    "account_id": fallback_account["id"],
                    "chat": fallback_chat,
                    "message_id": str(message_id),
                    "telegram_message_id": payload.telegram_message_id,
                }
            )
        return {
            "status": "already_deleted",
            "mode": "local",
            "chat": fallback_chat,
            "message_id": str(message_id),
        }

    chat = get_chat(int(message["chat_id"]))
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    account = get_account(int(message["account_id"]))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    delete_for_everyone = bool(payload.delete_for_everyone)
    is_real_telegram = bool(
        account.get("platform") == "telegram"
        and account.get("api_id")
        and account.get("api_hash")
        and account.get("session_path")
        and message.get("telegram_message_id")
    )

    deleted = delete_message(message_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Message not found")

    refreshed_chat = get_chat(int(chat["id"])) or chat
    await _broadcast(
        {
            "type": "message:deleted",
            "source": "telegram-delete" if is_real_telegram else "local-delete",
            "account_id": account["id"],
            "chat": refreshed_chat,
            "message_id": str(message_id),
            "telegram_message_id": message.get("telegram_message_id"),
        }
    )

    remote_warning: str | None = None
    if is_real_telegram:
        try:
            await asyncio.wait_for(
                _gateway.delete_message(
                    api_id=account.get("api_id"),
                    api_hash=account.get("api_hash"),
                    session_path=account.get("session_path"),
                    chat_external_id=str(chat["external_chat_id"]),
                    telegram_message_id=str(message["telegram_message_id"]),
                    revoke=delete_for_everyone,
                ),
                timeout=35,
            )
        except Exception as error:
            error_message = user_facing_error(error)
            if _telegram_delete_missing(error_message):
                logger.info("Telegram message %d already missing remotely; local row removed", message_id)
            else:
                logger.warning("Telegram delete failed after local delete for message %d: %s", message_id, error_message)
                update_account_login_state(account["id"], last_error=error_message)
                remote_warning = error_message

    return {
        "status": "deleted",
        "mode": "telegram" if is_real_telegram else "local",
        "chat": refreshed_chat,
        "message_id": str(message_id),
        "remote_warning": remote_warning,
    }


@router.post("/api/messages/{message_id}/forward")
async def api_forward_message(message_id: int, payload: ForwardPayload) -> dict:
    source_message = get_message(message_id)
    if not source_message:
        raise HTTPException(status_code=404, detail="Message not found")

    source_chat = get_chat(int(source_message["chat_id"]))
    target_chat = get_chat(payload.target_chat_id)
    if not source_chat or not target_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if int(source_chat["account_id"]) != int(target_chat["account_id"]):
        raise HTTPException(status_code=400, detail="Forward target must be in the same account")

    account = get_account(int(source_chat["account_id"]))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    is_real_telegram = bool(
        account.get("platform") == "telegram"
        and account.get("api_id")
        and account.get("api_hash")
        and account.get("session_path")
    )

    text_value = str(source_message.get("text") or "")
    telegram_message_id: str | None = None
    delivery_status = "sent"
    delivery_error: str | None = None

    try:
        if is_real_telegram and source_message.get("telegram_message_id"):
            result = await asyncio.wait_for(
                _gateway.forward_message(
                    api_id=account.get("api_id"),
                    api_hash=account.get("api_hash"),
                    session_path=account.get("session_path"),
                    source_chat_external_id=str(source_chat["external_chat_id"]),
                    target_chat_external_id=str(target_chat["external_chat_id"]),
                    telegram_message_id=str(source_message["telegram_message_id"]),
                ),
                timeout=35,
            )
            telegram_message_id = result.telegram_message_id
        else:
            result = await asyncio.wait_for(
                _gateway.send_message(
                    api_id=account.get("api_id"),
                    api_hash=account.get("api_hash"),
                    session_path=account.get("session_path"),
                    chat_external_id=str(target_chat["external_chat_id"]),
                    text=text_value,
                    attachment_path=resolve_message_attachment_file_path(source_message),
                    attachment_name=source_message.get("attachment_name"),
                    attachment_mime=source_message.get("attachment_mime"),
                    attachment_type=source_message.get("attachment_type"),
                ),
                timeout=35,
            )
            telegram_message_id = result.telegram_message_id
    except Exception as error:
        delivery_status = "failed"
        delivery_error = user_facing_error(error)
        logger.warning("Forward failed for message %d: %s", message_id, delivery_error)
        if is_real_telegram:
            update_account_login_state(account["id"], last_error=delivery_error)

    stored = save_message(
        chat_id=target_chat["id"],
        account_id=account["id"],
        direction="out",
        sender_name=account["display_name"],
        text=text_value,
        telegram_message_id=telegram_message_id,
        delivery_status=delivery_status,
        delivery_error=delivery_error,
        attachment_type=source_message.get("attachment_type"),
        attachment_name=source_message.get("attachment_name"),
        attachment_path=source_message.get("attachment_path"),
        attachment_mime=source_message.get("attachment_mime"),
        attachment_size=source_message.get("attachment_size"),
    )
    refreshed_chat = get_chat(target_chat["id"]) or target_chat
    await _broadcast(
        {
            "type": "message:new",
            "source": "forward",
            "account_id": account["id"],
            "chat": refreshed_chat,
            "message": stored,
        }
    )
    if delivery_status == "failed":
        raise HTTPException(status_code=409, detail=delivery_error or "Forward failed")

    return {"mode": "telegram" if is_real_telegram else "demo", "chat": refreshed_chat, "message": stored}


@router.post("/api/send")
async def api_send(
    account_id: int = Form(...),
    chat_id: int = Form(...),
    text: str = Form(""),
    client_message_id: str | None = Form(None),
    media_type: str | None = Form(None),
    media_duration: int | None = Form(None),
    media: UploadFile | None = File(None),
) -> dict:
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat["account_id"] != account_id:
        raise HTTPException(status_code=400, detail="Chat does not belong to the selected account")

    account = get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    text_value = text.strip()
    attachment_data: dict[str, object] = {}
    if media is not None:
        try:
            attachment_data = await persist_upload(media, account_id=account_id, chat_id=chat_id, direction="out", forced_type=media_type)
        except RuntimeError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        if media_duration is not None:
            attachment_data["duration"] = max(0, int(media_duration))

    if not text_value and not attachment_data:
        raise HTTPException(status_code=400, detail="Message text or media file is required")

    is_real_telegram = bool(
        account.get("platform") == "telegram"
        and account.get("api_id")
        and account.get("api_hash")
        and account.get("session_path")
    )
    is_facebook = bool(
        account.get("platform") == "facebook_page"
        and account.get("page_access_token")
    )

    stored = save_message(
        chat_id=chat_id,
        account_id=account_id,
        direction="out",
        sender_name=account["display_name"],
        text=text_value or (attachment_fallback_text(attachment_data) if attachment_data else "Attachment"),
        telegram_message_id=None,
        client_message_id=client_message_id,
        delivery_status="queued" if (is_real_telegram or is_facebook) else "sent",
        attachment_type=attachment_data.get("attachment_type") if attachment_data else None,
        attachment_name=attachment_data.get("attachment_name") if attachment_data else None,
        attachment_path=attachment_data.get("attachment_path") if attachment_data else None,
        attachment_mime=attachment_data.get("attachment_mime") if attachment_data else None,
        attachment_size=attachment_data.get("attachment_size") if attachment_data else None,
    )

    if is_real_telegram:
        try:
            loop = asyncio.get_running_loop()
            last_progress_percent = -1

            async def emit_telegram_progress(percent: int) -> None:
                await _broadcast(
                    {
                        "type": "message:progress",
                        "source": "telegram-send",
                        "account_id": account_id,
                        "chat_id": chat_id,
                        "message_id": stored["id"],
                        "client_message_id": client_message_id,
                        "progress": max(45, min(99, percent)),
                    }
                )

            def telegram_progress_callback(sent_bytes: int, total_bytes: int) -> None:
                nonlocal last_progress_percent
                if not total_bytes:
                    return
                telegram_percent = int((sent_bytes / total_bytes) * 55) + 45
                telegram_percent = max(45, min(99, telegram_percent))
                if telegram_percent <= last_progress_percent:
                    return
                last_progress_percent = telegram_percent
                loop.create_task(emit_telegram_progress(telegram_percent))

            result = await asyncio.wait_for(
                _gateway.send_message(
                    api_id=account.get("api_id"),
                    api_hash=account.get("api_hash"),
                    session_path=account.get("session_path"),
                    chat_external_id=chat["external_chat_id"],
                    text=text_value,
                    attachment_path=resolve_attachment_file_path(attachment_data),
                    attachment_name=attachment_data.get("attachment_name") if attachment_data else None,
                    attachment_mime=attachment_data.get("attachment_mime") if attachment_data else None,
                    attachment_type=attachment_data.get("attachment_type") if attachment_data else None,
                    attachment_duration=attachment_data.get("duration") if attachment_data else None,
                    progress_callback=telegram_progress_callback if attachment_data else None,
                ),
                timeout=35,
            )
            updated = update_message_delivery(
                stored["id"],
                telegram_message_id=result.telegram_message_id,
                delivery_status="sent",
                delivery_error=None,
            )
            inferred_read_messages = infer_read_receipts_from_incoming(chat_id)
            for inferred_message in inferred_read_messages:
                if str(inferred_message.get("id")) == str(stored["id"]):
                    updated = inferred_message
                await _broadcast(
                    {
                        "type": "message:updated",
                        "source": "telegram-send-read-inference",
                        "account_id": account_id,
                        "chat": chat,
                        "message": inferred_message,
                    }
                )
            await _broadcast(
                {
                    "type": "message:updated",
                    "source": "telegram-send",
                    "account_id": account_id,
                    "chat": chat,
                    "message": updated,
                }
            )
            return {
                "mode": "telegram",
                "message": updated,
            }
        except Exception as error:
            error_message = user_facing_error(error)
            logger.warning("Telegram send failed for chat %d: %s", chat_id, error_message)
            updated = update_message_delivery(
                stored["id"],
                delivery_status="failed",
                delivery_error=error_message,
            )
            update_account_login_state(account_id, last_error=error_message)
            await _broadcast(
                {
                    "type": "message:updated",
                    "source": "telegram-send",
                    "account_id": account_id,
                    "chat": chat,
                    "message": updated,
                }
            )
            raise HTTPException(status_code=409, detail=error_message) from error

    if is_facebook:
        try:
            result = await asyncio.wait_for(
                _fb_gateway.send_message(
                    page_access_token=account.get("page_access_token"),
                    recipient_id=chat["external_chat_id"],
                    text=text_value,
                    attachment_path=resolve_attachment_file_path(attachment_data),
                    attachment_name=attachment_data.get("attachment_name") if attachment_data else None,
                    attachment_mime=attachment_data.get("attachment_mime") if attachment_data else None,
                    attachment_type=attachment_data.get("attachment_type") if attachment_data else None,
                ),
                timeout=35,
            )
            updated = update_message_delivery(
                stored["id"],
                delivery_status="sent",
                delivery_error=None,
            )
            await _broadcast(
                {
                    "type": "message:updated",
                    "source": "facebook-send",
                    "account_id": account_id,
                    "chat": chat,
                    "message": updated,
                }
            )
            return {
                "mode": "facebook",
                "message": updated,
            }
        except Exception as error:
            error_message = user_facing_error(error)
            logger.warning("Facebook send failed for chat %d: %s", chat_id, error_message)
            updated = update_message_delivery(
                stored["id"],
                delivery_status="failed",
                delivery_error=error_message,
            )
            update_account_login_state(account_id, last_error=error_message)
            await _broadcast(
                {
                    "type": "message:updated",
                    "source": "facebook-send",
                    "account_id": account_id,
                    "chat": chat,
                    "message": updated,
                }
            )
            raise HTTPException(status_code=409, detail=error_message) from error

    # Demo mode (no real Telegram credentials)
    try:
        result = await _gateway.send_message(
            api_id=account.get("api_id"),
            api_hash=account.get("api_hash"),
            session_path=account.get("session_path"),
            chat_external_id=chat["external_chat_id"],
            text=text_value,
            attachment_path=resolve_attachment_file_path(attachment_data),
            attachment_name=attachment_data.get("attachment_name") if attachment_data else None,
            attachment_mime=attachment_data.get("attachment_mime") if attachment_data else None,
            attachment_type=attachment_data.get("attachment_type") if attachment_data else None,
            attachment_duration=attachment_data.get("duration") if attachment_data else None,
        )
    except Exception as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    stored = save_message(
        chat_id=chat_id,
        account_id=account_id,
        direction="out",
        sender_name=account["display_name"],
        text=text_value or (attachment_fallback_text(attachment_data) if attachment_data else "Attachment"),
        telegram_message_id=result.telegram_message_id,
        delivery_status="sent",
        attachment_type=attachment_data.get("attachment_type") if attachment_data else None,
        attachment_name=attachment_data.get("attachment_name") if attachment_data else None,
        attachment_path=attachment_data.get("attachment_path") if attachment_data else None,
        attachment_mime=attachment_data.get("attachment_mime") if attachment_data else None,
        attachment_size=attachment_data.get("attachment_size") if attachment_data else None,
    )

    return {
        "mode": result.mode,
        "message": stored,
    }


@router.post("/api/chats/{chat_id}/demo/incoming")
async def api_demo_incoming(
    chat_id: int,
    sender_name: str = Form("Customer"),
    text: str = Form(""),
    media: UploadFile | None = File(None),
) -> dict:
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    account = get_account(chat["account_id"])
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    text_value = text.strip()
    attachment_data: dict[str, object] = {}
    if media is not None:
        try:
            attachment_data = await persist_upload(media, account_id=account["id"], chat_id=chat_id, direction="in")
        except RuntimeError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    if not text_value and not attachment_data:
        raise HTTPException(status_code=400, detail="Message text or media file is required")

    stored = save_message(
        chat_id=chat_id,
        account_id=account["id"],
        direction="in",
        sender_name=sender_name.strip() or "Customer",
        text=text_value or (attachment_fallback_text(attachment_data) if attachment_data else "Attachment"),
        attachment_type=attachment_data.get("attachment_type") if attachment_data else None,
        attachment_name=attachment_data.get("attachment_name") if attachment_data else None,
        attachment_path=attachment_data.get("attachment_path") if attachment_data else None,
        attachment_mime=attachment_data.get("attachment_mime") if attachment_data else None,
        attachment_size=attachment_data.get("attachment_size") if attachment_data else None,
    )
    await _broadcast(
        {
            "type": "message:new",
            "source": "demo",
            "account_id": account["id"],
            "chat": chat,
            "message": stored,
        }
    )
    return {"message": stored}
