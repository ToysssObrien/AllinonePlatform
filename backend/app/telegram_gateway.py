from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
import sqlite3
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("omnidesk.telegram")

from telethon.errors import SessionPasswordNeededError


@dataclass
class SendResult:
    mode: str
    telegram_message_id: str | None


@dataclass
class LoginCodeResult:
    phone_code_hash: str


@dataclass
class LoginResult:
    mode: str
    telegram_user_id: str | None = None


@dataclass
class SyncResult:
    chats_synced: int
    messages_synced: int


class TelegramGateway:
    def __init__(self) -> None:
        self._clients: dict[str, Any] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._entity_cache: dict[tuple[str, str], Any] = {}
        self._live_handler_keys: set[str] = set()
        self._event_sink: Callable[[dict[str, Any]], Awaitable[None]] | None = None

    def _client_key(self, api_id: str | None, api_hash: str | None, session_path: str | None) -> str:
        session = os.path.abspath(session_path or "")
        return f"{session}|{api_id or ''}|{api_hash or ''}"

    def _get_lock(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    def set_event_sink(self, sink: Callable[[dict[str, Any]], Awaitable[None]] | None) -> None:
        self._event_sink = sink

    async def _emit_event(self, payload: dict[str, Any]) -> None:
        if self._event_sink is None:
            return
        await self._event_sink(payload)

    async def _get_client(self, *, api_id: str, api_hash: str, session_path: str) -> tuple[str, Any]:
        from telethon import TelegramClient  # imported lazily

        key = self._client_key(api_id, api_hash, session_path)
        client = self._clients.get(key)
        if client is None:
            client = TelegramClient(session_path, int(api_id), api_hash)
            self._clients[key] = client
        if not client.is_connected():
            logger.debug("Connecting Telegram client for session %s", session_path)
            last_error: Exception | None = None
            for attempt in range(5):
                try:
                    await client.connect()
                    break
                except sqlite3.OperationalError as error:
                    last_error = error
                    if "database is locked" not in str(error).lower() or attempt >= 4:
                        raise
                    await asyncio.sleep(0.25 * (attempt + 1))
            if last_error and not client.is_connected():
                raise last_error
        return key, client

    async def _resolve_entity(self, client: Any, key: str, chat_external_id: str) -> Any:
        cache_key = (key, str(chat_external_id))
        entity = self._entity_cache.get(cache_key)
        if entity is not None:
            return entity

        peer = int(chat_external_id) if str(chat_external_id).lstrip("-").isdigit() else chat_external_id
        entity = await client.get_input_entity(peer)
        self._entity_cache[cache_key] = entity
        return entity

    def _title_for_chat(self, entity: Any, fallback: str) -> str:
        title = getattr(entity, "title", None)
        if title:
            return str(title)
        first_name = getattr(entity, "first_name", None)
        last_name = getattr(entity, "last_name", None)
        username = getattr(entity, "username", None)
        if first_name or last_name:
            return " ".join(part for part in [str(first_name or ""), str(last_name or "")] if part).strip()
        if username:
            return f"@{username}"
        return fallback

    def _chat_type_for_dialog(self, dialog: Any) -> str:
        if getattr(dialog, "is_user", False):
            return "private"
        if getattr(dialog, "is_group", False):
            return "group"
        if getattr(dialog, "is_channel", False):
            return "channel"
        return "private"

    async def _profile_for_entity(
        self,
        *,
        client: Any,
        entity: Any,
        media_dir: Path,
        account_id: int,
        external_chat_id: str,
    ) -> dict[str, str | None]:
        first_name = getattr(entity, "first_name", None)
        last_name = getattr(entity, "last_name", None)
        username = getattr(entity, "username", None)
        phone = getattr(entity, "phone", None)
        profile_photo_path: str | None = None

        if entity is not None:
            profile_dir = media_dir / "profiles"
            profile_dir.mkdir(parents=True, exist_ok=True)
            safe_external_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(external_chat_id))
            destination = profile_dir / f"{account_id}-{safe_external_id}.jpg"
            try:
                downloaded = await client.download_profile_photo(entity, file=str(destination))
                if downloaded:
                    profile_photo_path = str(Path(downloaded).relative_to(media_dir)).replace("\\", "/")
                elif destination.exists():
                    profile_photo_path = str(destination.relative_to(media_dir)).replace("\\", "/")
            except Exception:
                if destination.exists():
                    profile_photo_path = str(destination.relative_to(media_dir)).replace("\\", "/")

        return {
            "profile_first_name": str(first_name) if first_name else None,
            "profile_last_name": str(last_name) if last_name else None,
            "profile_username": str(username) if username else None,
            "profile_phone": str(phone) if phone else None,
            "profile_photo_path": profile_photo_path,
        }

    async def prime_live_clients(self, accounts: list[dict[str, Any]]) -> None:
        for account in accounts:
            if account.get("platform") != "telegram":
                continue
            if not account.get("api_id") or not account.get("api_hash") or not account.get("session_path"):
                continue
            for attempt in range(3):
                try:
                    await self.ensure_live_updates(
                        api_id=str(account["api_id"]),
                        api_hash=str(account["api_hash"]),
                        session_path=str(account["session_path"]),
                        account_id=int(account["id"]),
                    )
                    break
                except Exception as exc:
                    if attempt < 2:
                        logger.warning("prime_live_clients attempt %d failed for account %d: %s, retrying...", attempt + 1, account["id"], exc)
                        await asyncio.sleep(2)
                    else:
                        logger.warning("Failed to prime live client for account %d after 3 attempts: %s", account["id"], exc)

    async def ensure_live_updates(
        self,
        *,
        api_id: str,
        api_hash: str,
        session_path: str,
        account_id: int,
    ) -> bool:
        from telethon import events  # imported lazily

        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            key, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            if not await client.is_user_authorized():
                return False

            await client.get_me()
            if key in self._live_handler_keys:
                return True

            async def _handle_new_message(event: Any) -> None:
                try:
                    await self._ingest_live_message(
                        client=client,
                        account_id=account_id,
                        event=event,
                        media_dir=None,
                        source="telegram-live",
                    )
                except Exception as error:
                    await self._emit_event(
                        {
                            "type": "telethon:error",
                            "account_id": account_id,
                            "message": str(error),
                        }
                    )

            client.add_event_handler(_handle_new_message, events.NewMessage(incoming=True))

            # Track when recipient reads our outgoing messages
            from telethon.tl.types import (
                UpdateReadHistoryOutbox,
                UpdateShort,
                Updates,
                UpdatesCombined,
                UpdateShortMessage,
            )
            from telethon import utils
            from .db import mark_messages_read_by_telegram_id, get_chat_by_external_id

            def _read_peer_id_candidates(peer: Any) -> list[str]:
                candidates: list[str] = []
                for value in (
                    getattr(peer, "user_id", None),
                    getattr(peer, "chat_id", None),
                    getattr(peer, "channel_id", None),
                ):
                    if value is not None:
                        candidates.append(str(value))
                try:
                    marked_peer_id = utils.get_peer_id(peer)
                    candidates.append(str(marked_peer_id))
                    resolved_peer_id, _ = utils.resolve_id(marked_peer_id)
                    candidates.append(str(resolved_peer_id))
                except Exception:
                    pass
                return list(dict.fromkeys(candidates))

            async def _handle_read_outbox(event: Any) -> None:
                try:
                    # Extract individual updates from container types
                    updates_list = []
                    if isinstance(event, UpdateReadHistoryOutbox):
                        updates_list = [event]
                    elif isinstance(event, UpdateShort):
                        updates_list = [event.update]
                    elif isinstance(event, (Updates, UpdatesCombined)):
                        updates_list = getattr(event, "updates", [])
                    
                    for update in updates_list:
                        if not isinstance(update, UpdateReadHistoryOutbox):
                            continue
                        peer_ids = _read_peer_id_candidates(update.peer)
                        if not peer_ids:
                            continue
                        max_id = update.max_id
                        logger.info("Read outbox event: peers=%s max_id=%s", peer_ids, max_id)
                        for peer_id in peer_ids:
                            updated = mark_messages_read_by_telegram_id(account_id, peer_id, max_id)
                            if not updated:
                                continue
                            chat = get_chat_by_external_id(account_id, peer_id)
                            for msg in updated:
                                await self._emit_event({
                                    "type": "message:updated",
                                    "account_id": account_id,
                                    "message": msg,
                                    "chat": chat,
                                })
                            logger.info("Marked %d messages as read for peer %s", len(updated), peer_id)
                            break
                except Exception as error:
                    logger.warning("Read outbox handler error: %s", error, exc_info=True)

            client.add_event_handler(_handle_read_outbox, events.Raw)

            self._live_handler_keys.add(key)
            logger.info("Live updates enabled for account %d", account_id)
            return True

    async def close_all_clients(self) -> None:
        for client in list(self._clients.values()):
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception:
                pass
        logger.info("Closed %d Telegram client(s)", len(self._clients))
        self._clients.clear()
        self._entity_cache.clear()
        self._live_handler_keys.clear()

    async def close_client(self, *, api_id: str, api_hash: str, session_path: str) -> None:
        """Close and remove a single Telegram client."""
        key = self._client_key(api_id, api_hash, session_path)
        client = self._clients.pop(key, None)
        if client:
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception:
                pass
        self._entity_cache.pop(key, None)
        self._live_handler_keys.discard(key)
        logger.info("Closed Telegram client for key %s", key)

    async def request_login_code(
        self,
        *,
        api_id: str,
        api_hash: str,
        session_path: str,
        phone: str,
    ) -> LoginCodeResult:
        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            _, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            sent = await client.send_code_request(phone)
            phone_code_hash = getattr(sent, "phone_code_hash", None)
            if not phone_code_hash:
                raise RuntimeError("Telegram did not return a phone_code_hash.")
            return LoginCodeResult(phone_code_hash=phone_code_hash)

    async def confirm_login_code(
        self,
        *,
        api_id: str,
        api_hash: str,
        session_path: str,
        phone: str,
        code: str,
        phone_code_hash: str | None,
    ) -> LoginResult:
        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            _, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            try:
                user = await client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=phone_code_hash,
                )
                return LoginResult(mode="authorized", telegram_user_id=str(getattr(user, "id", "")))
            except SessionPasswordNeededError:
                return LoginResult(mode="password_needed", telegram_user_id=None)

    async def confirm_2fa_password(
        self,
        *,
        api_id: str,
        api_hash: str,
        session_path: str,
        password: str,
    ) -> LoginResult:
        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            _, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            user = await client.sign_in(password=password)
            return LoginResult(mode="authorized", telegram_user_id=str(getattr(user, "id", "")))

    async def send_message(
        self,
        *,
        api_id: str | None,
        api_hash: str | None,
        session_path: str | None,
        chat_external_id: str,
        text: str,
        attachment_path: str | None = None,
        attachment_name: str | None = None,
        attachment_mime: str | None = None,
        attachment_type: str | None = None,
        attachment_duration: int | None = None,
        progress_callback: Callable[[int, int], object] | None = None,
    ) -> SendResult:
        if not api_id or not api_hash or not session_path:
            return SendResult(mode="demo", telegram_message_id=None)

        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            _, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            if not client.is_connected():
                await client.connect()
            if not await client.is_user_authorized():
                raise RuntimeError("Telegram session is not authorized yet.")
            entity = await self._resolve_entity(client, key, chat_external_id)
            caption = text.strip() if text else ""
            if attachment_path:
                normalized_mime = (attachment_mime or "").split(";", 1)[0].strip().lower()
                normalized_name = (attachment_name or Path(attachment_path).name).lower()
                is_voice_attachment = (
                    attachment_type == "voice"
                    or (
                        normalized_mime in {"audio/ogg", "audio/opus", "audio/webm"}
                        and (normalized_name.startswith("voice-") or normalized_name == "voice.ogg")
                    )
                )
                prepared_attachment_path = attachment_path
                prepared_attachment_mime = attachment_mime
                cleanup_path: str | None = None
                if is_voice_attachment:
                    prepared_attachment_path, prepared_attachment_mime, cleanup_path = self._prepare_voice_note_file(
                        attachment_path=attachment_path,
                        attachment_mime=attachment_mime,
                    )
                send_kwargs = {
                    "file": prepared_attachment_path,
                    "caption": None if is_voice_attachment else caption or None,
                }
                if progress_callback is not None:
                    send_kwargs["progress_callback"] = progress_callback
                if is_voice_attachment:
                    send_kwargs["voice_note"] = True
                    send_kwargs["force_document"] = False
                    send_kwargs["mime_type"] = prepared_attachment_mime or "audio/ogg"
                    from telethon.tl.types import DocumentAttributeAudio

                    duration = max(1, int(attachment_duration or 1))
                    send_kwargs["attributes"] = [
                        DocumentAttributeAudio(
                            duration=duration,
                            voice=True,
                            waveform=self._default_voice_waveform(),
                        )
                    ]
                elif attachment_type == "gif":
                    send_kwargs["force_document"] = True
                    send_kwargs["mime_type"] = attachment_mime or "image/gif"
                elif attachment_type == "sticker":
                    send_kwargs["force_document"] = True
                    send_kwargs["mime_type"] = attachment_mime or ("application/x-tgsticker" if str(prepared_attachment_path).lower().endswith(".tgs") else "image/webp")
                elif attachment_type == "video":
                    send_kwargs["supports_streaming"] = True
                try:
                    sent = await asyncio.wait_for(client.send_file(entity, **send_kwargs), timeout=30)
                finally:
                    if cleanup_path:
                        Path(cleanup_path).unlink(missing_ok=True)
            else:
                sent = await asyncio.wait_for(client.send_message(entity, caption), timeout=30)
            return SendResult(mode="telegram", telegram_message_id=str(sent.id))

    async def forward_message(
        self,
        *,
        api_id: str | None,
        api_hash: str | None,
        session_path: str | None,
        source_chat_external_id: str,
        target_chat_external_id: str,
        telegram_message_id: str | None,
    ) -> SendResult:
        if not api_id or not api_hash or not session_path or not telegram_message_id:
            return SendResult(mode="demo", telegram_message_id=None)

        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            _, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            if not client.is_connected():
                await client.connect()
            if not await client.is_user_authorized():
                raise RuntimeError("Telegram session is not authorized yet.")

            source_entity = await self._resolve_entity(client, key, source_chat_external_id)
            target_entity = await self._resolve_entity(client, key, target_chat_external_id)
            sent = await asyncio.wait_for(
                client.forward_messages(
                    target_entity,
                    int(telegram_message_id),
                    from_peer=source_entity,
                ),
                timeout=30,
            )
            return SendResult(mode="telegram", telegram_message_id=str(getattr(sent, "id", "")))

    async def delete_message(
        self,
        *,
        api_id: str | None,
        api_hash: str | None,
        session_path: str | None,
        chat_external_id: str,
        telegram_message_id: str | None,
        revoke: bool = False,
    ) -> SendResult:
        if not api_id or not api_hash or not session_path or not telegram_message_id:
            return SendResult(mode="demo", telegram_message_id=None)

        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            _, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            if not client.is_connected():
                await client.connect()
            if not await client.is_user_authorized():
                raise RuntimeError("Telegram session is not authorized yet.")

            entity = await self._resolve_entity(client, key, chat_external_id)
            await asyncio.wait_for(
                client.delete_messages(
                    entity,
                    [int(telegram_message_id)],
                    revoke=revoke,
                ),
                timeout=30,
            )
            return SendResult(mode="telegram", telegram_message_id=str(telegram_message_id))

    async def rename_contact(
        self,
        *,
        api_id: str | None,
        api_hash: str | None,
        session_path: str | None,
        chat_external_id: str,
        display_name: str,
    ) -> None:
        if not api_id or not api_hash or not session_path:
            raise RuntimeError("Telegram credentials are incomplete.")

        parts = [part for part in display_name.strip().split() if part]
        if not parts:
            raise RuntimeError("Display name is required.")
        first_name = parts[0]
        last_name = " ".join(parts[1:])

        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            _, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            if not client.is_connected():
                await client.connect()
            if not await client.is_user_authorized():
                raise RuntimeError("Telegram session is not authorized yet.")

            entity = await self._resolve_entity(client, key, chat_external_id)
            full_entity = await client.get_entity(entity)
            if getattr(full_entity, "bot", False):
                raise RuntimeError("Telegram bot contacts cannot be renamed from this account.")
            if not hasattr(full_entity, "access_hash"):
                raise RuntimeError("Only private Telegram users can be renamed as contacts.")

            from telethon.tl.functions.contacts import AddContactRequest

            input_user = await client.get_input_entity(full_entity)
            await asyncio.wait_for(
                client(
                    AddContactRequest(
                        id=input_user,
                        first_name=first_name,
                        last_name=last_name,
                        phone="",
                        add_phone_privacy_exception=False,
                    )
                ),
                timeout=30,
            )

    def _prepare_voice_note_file(
        self,
        *,
        attachment_path: str,
        attachment_mime: str | None,
    ) -> tuple[str, str, str | None]:
        source = Path(attachment_path)
        lower_name = source.name.lower()
        lower_mime = (attachment_mime or "").lower()
        if lower_name.endswith((".ogg", ".oga", ".opus")) and lower_mime not in {"audio/webm", "video/webm"}:
            return str(source), attachment_mime or "audio/ogg", None

        try:
            import imageio_ffmpeg
        except ImportError as error:
            raise RuntimeError("Install imageio-ffmpeg to send browser voice recordings as Telegram voice notes.") from error

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        with tempfile.NamedTemporaryFile(prefix="telegram-voice-", suffix=".ogg", delete=False) as temporary:
            output_path = Path(temporary.name)

        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(source),
            "-vn",
            "-c:a",
            "libopus",
            "-b:a",
            "48k",
            "-ac",
            "1",
            "-application",
            "voip",
            str(output_path),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True)
        except Exception as error:
            output_path.unlink(missing_ok=True)
            raise RuntimeError("Could not convert browser voice recording to Telegram voice note format.") from error
        return str(output_path), "audio/ogg", str(output_path)

    def _default_voice_waveform(self) -> bytes:
        levels = [4, 6, 8, 10, 12, 16, 20, 18, 14, 12, 15, 19, 23, 21, 17, 13]
        return bytes((levels * 4)[:64])

    async def _store_message(
        self,
        *,
        client: Any,
        account_id: int,
        media_dir: Path,
        external_chat_id: str,
        title: str,
        chat_type: str,
        message: Any,
        entity: Any | None = None,
        update_chat: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        from .db import save_message, upsert_chat

        profile_info = await self._profile_for_entity(
            client=client,
            entity=entity if entity is not None else getattr(message, "chat", None),
            media_dir=media_dir,
            account_id=account_id,
            external_chat_id=external_chat_id,
        )

        chat_row = upsert_chat(
            account_id,
            external_chat_id,
            title,
            chat_type=chat_type,
            last_message_at=self._telegram_datetime_to_iso(getattr(message, "date", None)),
            **profile_info,
        )

        attachment_info = await self._build_attachment_from_message(
            client=client,
            message=message,
            media_dir=media_dir,
            account_id=account_id,
            external_chat_id=external_chat_id,
        )

        direction = "out" if getattr(message, "out", False) else "in"
        sender_name = "You" if direction == "out" else str(chat_row.get("title") or title)
        text = (getattr(message, "message", "") or "").strip()

        stored = save_message(
            chat_id=chat_row["id"],
            account_id=account_id,
            direction=direction,
            sender_name=sender_name,
            text=text or attachment_info.get("fallback_text", "Attachment"),
            telegram_message_id=str(message.id),
            attachment_type=attachment_info.get("attachment_type"),
            attachment_name=attachment_info.get("attachment_name"),
            attachment_path=attachment_info.get("attachment_path"),
            attachment_mime=attachment_info.get("attachment_mime"),
            attachment_size=attachment_info.get("attachment_size"),
            update_chat=update_chat,
        )
        return chat_row, stored

    async def _ingest_live_message(
        self,
        *,
        client: Any,
        account_id: int,
        event: Any,
        media_dir: Path | None,
        source: str,
    ) -> None:
        message = getattr(event, "message", None) or event
        if message is None:
            return

        entity = getattr(event, "chat", None) or getattr(message, "chat", None)
        if entity is None and hasattr(event, "get_chat"):
            try:
                entity = await event.get_chat()
            except Exception:
                entity = None
        external_chat_id = str(
            getattr(entity, "id", None)
            or getattr(event, "chat_id", None)
            or getattr(message, "chat_id", None)
            or ""
        )
        if not external_chat_id:
            return

        title = self._title_for_chat(entity, external_chat_id)
        chat_type = (
            "private"
            if getattr(event, "is_private", False) or getattr(message, "is_private", False)
            else "group"
            if getattr(event, "is_group", False) or getattr(message, "is_group", False)
            else "channel"
            if getattr(event, "is_channel", False) or getattr(message, "is_channel", False)
            else "private"
        )
        media_target = media_dir or Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "media")))
        media_target.mkdir(parents=True, exist_ok=True)

        chat_row, stored = await self._store_message(
            client=client,
            account_id=account_id,
            media_dir=media_target,
            external_chat_id=external_chat_id,
            title=title,
            chat_type=chat_type,
            message=message,
            entity=entity,
            update_chat=True,
        )

        if stored.get("direction") == "in":
            try:
                from .db import mark_messages_read_by_telegram_id

                incoming_message_id = int(getattr(message, "id", 0) or 0)
                if incoming_message_id:
                    updated_read_messages = mark_messages_read_by_telegram_id(
                        account_id,
                        external_chat_id,
                        incoming_message_id,
                    )
                    for updated_message in updated_read_messages:
                        await self._emit_event(
                            {
                                "type": "message:updated",
                                "source": "telegram-live-read-fallback",
                                "account_id": account_id,
                                "chat": chat_row,
                                "message": updated_message,
                            }
                        )
            except Exception as error:
                logger.warning("Could not infer read receipt from inbound message: %s", error)

        await self._emit_event(
            {
                "type": "message:new",
                "source": source,
                "account_id": account_id,
                "chat": chat_row,
                "message": stored,
            }
        )

    async def sync_recent_inbox(
        self,
        *,
        api_id: str,
        api_hash: str,
        session_path: str,
        account_id: int,
        media_root: str,
        dialog_limit: int | None = 20,
        message_limit: int | None = 20,
        include_archived: bool = False,
    ) -> SyncResult:
        logger.info(
            "sync_recent_inbox START account=%d dialog_limit=%s message_limit=%s archived=%s",
            account_id, dialog_limit, message_limit, include_archived,
        )
        key = self._client_key(api_id, api_hash, session_path)
        async with self._get_lock(key):
            _, client = await self._get_client(api_id=api_id, api_hash=api_hash, session_path=session_path)
            if not await client.is_user_authorized():
                raise RuntimeError("Telegram session is not authorized yet.")

        media_dir = Path(media_root)
        media_dir.mkdir(parents=True, exist_ok=True)

        chats_synced = 0
        messages_synced = 0
        seen_dialog_ids: set[str] = set()
        dialog_passes = [False, True] if include_archived else [False]
        from .db import save_message, upsert_chat

        await self._emit_event(
            {
                "type": "sync:start",
                "account_id": account_id,
                "full_history": bool(include_archived),
            }
        )

        for archived in dialog_passes:
            logger.info("sync: iterating dialogs (archived=%s, limit=%s)", archived, dialog_limit)
            dialog_count_in_pass = 0
            async for dialog in client.iter_dialogs(limit=dialog_limit, archived=archived):
                entity = dialog.entity
                external_chat_id = str(getattr(entity, "id", None) or dialog.id)
                if external_chat_id in seen_dialog_ids:
                    continue
                seen_dialog_ids.add(external_chat_id)

                title = dialog.name or self._title_for_chat(entity, external_chat_id)
                chat_type = self._chat_type_for_dialog(dialog)
                dialog_count_in_pass += 1
                logger.info(
                    "sync: dialog #%d '%s' (id=%s, type=%s, archived=%s)",
                    dialog_count_in_pass, title, external_chat_id, chat_type, archived,
                )

                try:
                    profile_info = await self._profile_for_entity(
                        client=client,
                        entity=entity,
                        media_dir=media_dir,
                        account_id=account_id,
                        external_chat_id=external_chat_id,
                    )
                except Exception as e:
                    logger.warning("sync: failed to get profile for '%s': %s", title, e)
                    profile_info = {}

                chat_row = upsert_chat(
                    account_id,
                    external_chat_id,
                    title,
                    chat_type=chat_type,
                    last_message_at=self._telegram_datetime_to_iso(getattr(dialog, "date", None)),
                    **profile_info,
                )
                chats_synced += 1
                await self._emit_event(
                    {
                        "type": "chat:upsert",
                        "source": "telegram-sync",
                        "account_id": account_id,
                        "chat": chat_row,
                    }
                )

                msg_count = 0
                try:
                    async for message in client.iter_messages(entity, limit=message_limit):
                        if not message:
                            continue

                        telegram_message_id = str(message.id)
                        text = (getattr(message, "message", "") or "").strip()
                        direction = "out" if getattr(message, "out", False) else "in"
                        sender_name = "You" if direction == "out" else str(chat_row.get("title") or title)
                        attachment_info = await self._build_attachment_from_message(
                            client=client,
                            message=message,
                            media_dir=media_dir,
                            account_id=account_id,
                            external_chat_id=external_chat_id,
                        )

                        save_message(
                            chat_id=chat_row["id"],
                            account_id=account_id,
                            direction=direction,
                            sender_name=sender_name,
                            text=text or attachment_info.get("fallback_text", "Attachment"),
                            telegram_message_id=telegram_message_id,
                            attachment_type=attachment_info.get("attachment_type"),
                            attachment_name=attachment_info.get("attachment_name"),
                            attachment_path=attachment_info.get("attachment_path"),
                            attachment_mime=attachment_info.get("attachment_mime"),
                            attachment_size=attachment_info.get("attachment_size"),
                            update_chat=False,
                        )
                        msg_count += 1
                        messages_synced += 1
                except Exception as e:
                    logger.error("sync: error fetching messages for '%s': %s", title, e)

                logger.info("sync: dialog '%s' done — %d messages saved", title, msg_count)

            logger.info("sync: pass archived=%s done — %d dialogs found", archived, dialog_count_in_pass)

        logger.info(
            "sync_recent_inbox COMPLETE account=%d chats=%d messages=%d",
            account_id, chats_synced, messages_synced,
        )
        await self._emit_event(
            {
                "type": "sync:complete",
                "account_id": account_id,
                "full_history": bool(include_archived),
                "chats_synced": chats_synced,
                "messages_synced": messages_synced,
            }
        )
        return SyncResult(chats_synced=chats_synced, messages_synced=messages_synced)

    async def _build_attachment_from_message(
        self,
        *,
        client: Any,
        message: Any,
        media_dir: Path,
        account_id: int,
        external_chat_id: str,
    ) -> dict[str, Any]:
        if not getattr(message, "media", None):
            return {}

        file = getattr(message, "file", None)
        mime_type = getattr(file, "mime_type", None) if file else None
        original_name = getattr(file, "name", None) if file else None

        attachment_type = "file"
        special_sticker = bool(getattr(message, "sticker", False) or mime_type == "application/x-tgsticker" or (original_name or "").lower().endswith((".webp", ".tgs")))
        special_gif = bool(getattr(message, "gif", False) or mime_type == "image/gif" or (original_name or "").lower().endswith(".gif"))
        if special_sticker:
            attachment_type = "sticker"
        elif special_gif:
            attachment_type = "gif"
        elif getattr(message, "voice", False):
            attachment_type = "voice"
        elif getattr(message, "audio", False):
            attachment_type = "audio"
        elif getattr(message, "photo", False):
            attachment_type = "image"
        elif getattr(message, "video", False):
            attachment_type = "video"
        elif mime_type:
            if mime_type.startswith("audio/"):
                attachment_type = "voice" if mime_type in {"audio/ogg", "audio/opus", "audio/webm"} else "audio"
            elif mime_type.startswith("video/"):
                attachment_type = "video"
            elif mime_type.startswith("image/") and not special_sticker and not special_gif:
                attachment_type = "image"

        if not original_name:
            extension_map = {
                "image": ".jpg",
                "video": ".mp4",
                "gif": ".gif",
                "voice": ".ogg",
                "audio": ".mp3",
                "sticker": ".tgs" if mime_type == "application/x-tgsticker" else ".webp",
                "file": ".bin",
            }
            original_name = f"{attachment_type}{extension_map.get(attachment_type, '.bin')}"

        safe_name = f"{message.id}-{original_name}"
        destination_dir = media_dir / f"telegram-sync-{account_id}-{external_chat_id}"
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / safe_name
        await client.download_media(message, file=str(destination))
        relative_path = str(destination.relative_to(media_dir)).replace("\\", "/")

        return {
            "attachment_type": attachment_type,
            "attachment_name": original_name,
            "attachment_path": relative_path,
            "attachment_mime": mime_type or "application/octet-stream",
            "attachment_size": destination.stat().st_size if destination.exists() else None,
            "fallback_text": (
                "Sticker"
                if attachment_type == "sticker"
                else "GIF"
                if attachment_type == "gif"
                else "Voice message"
                if attachment_type == "voice"
                else "Audio file"
                if attachment_type == "audio"
                else original_name
            ),
        }

    @staticmethod
    def _telegram_datetime_to_iso(value: Any) -> str | None:
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                return None
        return None


def build_session_path(account_id: int) -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "sessions"))
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"account-{account_id}")
