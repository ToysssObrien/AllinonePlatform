from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..db import get_account, get_chat, list_all_chats, list_chats, rename_chat, touch_chat
from ..schemas import RenameChatPayload
from ..telegram_gateway import TelegramGateway

logger = logging.getLogger("omnidesk.chats")

router = APIRouter(tags=["chats"])

_gateway: TelegramGateway | None = None
_broadcast = None


def configure(*, gateway: TelegramGateway, broadcast) -> None:
    global _gateway, _broadcast
    _gateway = gateway
    _broadcast = broadcast


@router.get("/api/chats")
def api_chats(account_id: int | None = None) -> list[dict]:
    if account_id is None:
        return list_all_chats()
    return list_chats(account_id)


@router.post("/api/chats/{chat_id}/read")
def api_mark_chat_read(chat_id: int) -> dict:
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    touch_chat(chat_id)
    refreshed = get_chat(chat_id)
    return {"chat": refreshed or chat}


@router.patch("/api/chats/{chat_id}/rename")
async def api_rename_chat(chat_id: int, payload: RenameChatPayload) -> dict:
    chat = get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    account = get_account(int(chat["account_id"]))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    display_name = payload.display_name.strip()
    try:
        renamed_chat = rename_chat(chat_id, display_name)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if not renamed_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    telegram_warning: str | None = None
    if payload.sync_telegram:
        if account.get("platform") != "telegram":
            telegram_warning = "This account is not a Telegram account."
        elif not account.get("api_id") or not account.get("api_hash") or not account.get("session_path"):
            telegram_warning = "Telegram credentials are incomplete."
        else:
            try:
                await _gateway.rename_contact(
                    api_id=account.get("api_id"),
                    api_hash=account.get("api_hash"),
                    session_path=account.get("session_path"),
                    chat_external_id=str(chat["external_chat_id"]),
                    display_name=display_name,
                )
            except Exception as error:
                telegram_warning = str(error) or error.__class__.__name__
                logger.warning("Telegram contact rename failed for chat %d: %s", chat_id, telegram_warning)

    if _broadcast:
        await _broadcast(
            {
                "type": "chat:upsert",
                "source": "rename",
                "account_id": account["id"],
                "chat": renamed_chat,
            }
        )

    return {
        "chat": renamed_chat,
        "telegram_synced": bool(payload.sync_telegram and not telegram_warning),
        "telegram_warning": telegram_warning,
    }
