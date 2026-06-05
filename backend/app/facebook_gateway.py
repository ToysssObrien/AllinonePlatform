from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("omnidesk.facebook")

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


@dataclass
class SendResult:
    mode: str
    facebook_message_id: str | None


@dataclass
class UserProfile:
    first_name: str | None = None
    last_name: str | None = None
    profile_pic: str | None = None


class FacebookGateway:
    """Gateway for Facebook Page Messaging via the Graph API."""

    def __init__(self) -> None:
        self._http: httpx.AsyncClient | None = None
        self._event_sink: Callable[[dict[str, Any]], Awaitable[None]] | None = None
        self._profile_cache: dict[str, UserProfile] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(timeout=30.0)
        return self._http

    def set_event_sink(self, sink: Callable[[dict[str, Any]], Awaitable[None]] | None) -> None:
        self._event_sink = sink

    async def _emit_event(self, payload: dict[str, Any]) -> None:
        if self._event_sink is None:
            return
        await self._event_sink(payload)

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Webhook verification
    # ------------------------------------------------------------------

    @staticmethod
    def verify_webhook(
        mode: str | None,
        token: str | None,
        challenge: str | None,
        verify_token: str | None,
    ) -> str | None:
        """Return the challenge string if the webhook verification is valid."""
        expected = verify_token or os.environ.get("FB_VERIFY_TOKEN", "omnidesk_fb_verify")
        if mode == "subscribe" and token == expected:
            return challenge
        return None

    @staticmethod
    def verify_signature(payload: bytes, signature: str | None, app_secret: str | None) -> bool:
        """Verify X-Hub-Signature-256 header from Facebook."""
        if not app_secret or not signature:
            # If no app_secret configured, skip verification
            return True
        if not signature.startswith("sha256="):
            return False
        expected = hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature[7:], expected)

    # ------------------------------------------------------------------
    # Send messages
    # ------------------------------------------------------------------

    async def send_message(
        self,
        *,
        page_access_token: str | None,
        recipient_id: str,
        text: str,
        attachment_path: str | None = None,
        attachment_name: str | None = None,
        attachment_mime: str | None = None,
        attachment_type: str | None = None,
    ) -> SendResult:
        if not page_access_token:
            return SendResult(mode="demo", facebook_message_id=None)

        client = self._client()

        if attachment_path and Path(attachment_path).exists():
            return await self._send_attachment(
                client=client,
                page_access_token=page_access_token,
                recipient_id=recipient_id,
                text=text,
                attachment_path=attachment_path,
                attachment_name=attachment_name,
                attachment_mime=attachment_mime,
                attachment_type=attachment_type,
            )

        # Text-only message
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text or "(empty)"},
            "messaging_type": "RESPONSE",
        }

        response = await client.post(
            f"{GRAPH_API_BASE}/me/messages",
            params={"access_token": page_access_token},
            json=payload,
        )
        data = response.json()
        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", response.text)
            raise RuntimeError(f"Facebook API error: {error_msg}")

        message_id = data.get("message_id")
        return SendResult(mode="facebook", facebook_message_id=message_id)

    async def _send_attachment(
        self,
        *,
        client: httpx.AsyncClient,
        page_access_token: str,
        recipient_id: str,
        text: str,
        attachment_path: str,
        attachment_name: str | None,
        attachment_mime: str | None,
        attachment_type: str | None,
    ) -> SendResult:
        fb_type = self._map_attachment_type(attachment_type, attachment_mime)
        file_path = Path(attachment_path)
        filename = attachment_name or file_path.name
        mime = attachment_mime or "application/octet-stream"

        message_payload: dict[str, Any] = {
            "attachment": {
                "type": fb_type,
                "payload": {"is_reusable": False},
            },
        }
        if text and text.strip():
            # Facebook doesn't support caption with attachment in one call.
            # Send text first, then attachment.
            text_payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": text},
                "messaging_type": "RESPONSE",
            }
            await client.post(
                f"{GRAPH_API_BASE}/me/messages",
                params={"access_token": page_access_token},
                json=text_payload,
            )

        with open(file_path, "rb") as f:
            files = {
                "message": (None, __import__("json").dumps({"attachment": {"type": fb_type, "payload": {"is_reusable": False}}})),
                "filedata": (filename, f, mime),
                "recipient": (None, __import__("json").dumps({"id": recipient_id})),
                "messaging_type": (None, "RESPONSE"),
            }
            response = await client.post(
                f"{GRAPH_API_BASE}/me/messages",
                params={"access_token": page_access_token},
                files=files,
            )

        data = response.json()
        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", response.text)
            raise RuntimeError(f"Facebook API error: {error_msg}")

        message_id = data.get("message_id")
        return SendResult(mode="facebook", facebook_message_id=message_id)

    # ------------------------------------------------------------------
    # Receive webhook events
    # ------------------------------------------------------------------

    async def handle_webhook_event(
        self,
        *,
        body: dict[str, Any],
        media_dir: Path,
    ) -> None:
        """Process an incoming Facebook webhook event."""
        if body.get("object") != "page":
            return

        for entry in body.get("entry", []):
            page_id = str(entry.get("id", ""))
            for messaging_event in entry.get("messaging", []):
                await self._process_messaging_event(
                    page_id=page_id,
                    event=messaging_event,
                    media_dir=media_dir,
                )

    async def _process_messaging_event(
        self,
        *,
        page_id: str,
        event: dict[str, Any],
        media_dir: Path,
    ) -> None:
        from .db import get_account_by_page_id, upsert_chat, save_message

        sender_id = str(event.get("sender", {}).get("id", ""))
        recipient_id = str(event.get("recipient", {}).get("id", ""))
        message_data = event.get("message")

        if not sender_id or not message_data:
            return

        # Ignore echo messages (messages sent by the page itself)
        if message_data.get("is_echo"):
            return

        # Find the account for this page
        account = get_account_by_page_id(page_id)
        if not account:
            # Try matching by recipient_id (which is the page's PSID)
            account = get_account_by_page_id(recipient_id)
        if not account:
            logger.warning("No account found for page_id=%s or recipient=%s", page_id, recipient_id)
            return

        account_id = account["id"]
        page_access_token = account.get("page_access_token")

        # Get user profile for sender name
        profile = await self._get_user_profile(page_access_token, sender_id)
        sender_name = " ".join(
            part for part in [profile.first_name, profile.last_name] if part
        ).strip() or f"User {sender_id}"

        # Upsert chat
        chat_row = upsert_chat(
            account_id,
            sender_id,  # external_chat_id = sender's PSID
            sender_name,
            chat_type="private",
            profile_first_name=profile.first_name,
            profile_last_name=profile.last_name,
            profile_photo_path=None,
        )

        # Download profile photo if available
        if profile.profile_pic and page_access_token:
            try:
                await self._download_profile_photo(
                    url=profile.profile_pic,
                    media_dir=media_dir,
                    account_id=account_id,
                    external_chat_id=sender_id,
                )
            except Exception as e:
                logger.warning("Failed to download FB profile photo: %s", e)

        # Process message text
        text = message_data.get("text", "")
        external_message_id = message_data.get("mid")

        # Process attachments
        attachment_info: dict[str, Any] = {}
        attachments = message_data.get("attachments", [])
        if attachments:
            attachment_info = await self._process_attachment(
                attachments[0],
                media_dir=media_dir,
                account_id=account_id,
                external_chat_id=sender_id,
            )

        stored = save_message(
            chat_id=chat_row["id"],
            account_id=account_id,
            direction="in",
            sender_name=sender_name,
            text=text or attachment_info.get("fallback_text", "Attachment"),
            telegram_message_id=None,
            external_message_id=external_message_id,
            attachment_type=attachment_info.get("attachment_type"),
            attachment_name=attachment_info.get("attachment_name"),
            attachment_path=attachment_info.get("attachment_path"),
            attachment_mime=attachment_info.get("attachment_mime"),
            attachment_size=attachment_info.get("attachment_size"),
        )

        await self._emit_event({
            "type": "message:new",
            "source": "facebook-webhook",
            "account_id": account_id,
            "chat": chat_row,
            "message": stored,
        })

    # ------------------------------------------------------------------
    # User profiles
    # ------------------------------------------------------------------

    async def _get_user_profile(self, page_access_token: str | None, user_id: str) -> UserProfile:
        if user_id in self._profile_cache:
            return self._profile_cache[user_id]

        if not page_access_token:
            return UserProfile()

        try:
            client = self._client()
            response = await client.get(
                f"{GRAPH_API_BASE}/{user_id}",
                params={
                    "fields": "first_name,last_name,profile_pic",
                    "access_token": page_access_token,
                },
            )
            if response.status_code == 200:
                data = response.json()
                profile = UserProfile(
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    profile_pic=data.get("profile_pic"),
                )
                self._profile_cache[user_id] = profile
                return profile
        except Exception as e:
            logger.warning("Failed to get Facebook user profile for %s: %s", user_id, e)

        return UserProfile()

    async def _download_profile_photo(
        self,
        *,
        url: str,
        media_dir: Path,
        account_id: int,
        external_chat_id: str,
    ) -> str | None:
        try:
            client = self._client()
            response = await client.get(url, follow_redirects=True)
            if response.status_code != 200:
                return None

            profile_dir = media_dir / "profiles"
            profile_dir.mkdir(parents=True, exist_ok=True)
            safe_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(external_chat_id))
            destination = profile_dir / f"{account_id}-fb-{safe_id}.jpg"
            destination.write_bytes(response.content)
            return str(destination.relative_to(media_dir)).replace("\\", "/")
        except Exception as e:
            logger.warning("Failed to download profile photo: %s", e)
            return None

    # ------------------------------------------------------------------
    # Attachment processing
    # ------------------------------------------------------------------

    async def _process_attachment(
        self,
        attachment: dict[str, Any],
        *,
        media_dir: Path,
        account_id: int,
        external_chat_id: str,
    ) -> dict[str, Any]:
        att_type = attachment.get("type", "file")
        payload = attachment.get("payload", {})
        url = payload.get("url")

        if not url:
            return {}

        fb_type_map = {
            "image": "image",
            "video": "video",
            "audio": "audio",
            "file": "file",
            "fallback": "file",
        }
        attachment_type = fb_type_map.get(att_type, "file")

        # Determine file extension from type
        ext_map = {
            "image": ".jpg",
            "video": ".mp4",
            "audio": ".mp3",
            "file": ".bin",
        }
        extension = ext_map.get(attachment_type, ".bin")

        # Download the attachment
        try:
            client = self._client()
            response = await client.get(url, follow_redirects=True)
            if response.status_code != 200:
                return {}

            dest_dir = media_dir / f"fb-{account_id}-{external_chat_id}"
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Try to infer filename from Content-Disposition or URL
            content_type = response.headers.get("content-type", "application/octet-stream")
            filename = f"fb-attachment-{__import__('uuid').uuid4().hex[:8]}{extension}"
            destination = dest_dir / filename
            destination.write_bytes(response.content)

            relative_path = str(destination.relative_to(media_dir)).replace("\\", "/")
            fallback_text_map = {
                "image": "Photo",
                "video": "Video",
                "audio": "Audio message",
                "file": "File attachment",
            }
            return {
                "attachment_type": attachment_type,
                "attachment_name": filename,
                "attachment_path": relative_path,
                "attachment_mime": content_type.split(";")[0].strip(),
                "attachment_size": len(response.content),
                "fallback_text": fallback_text_map.get(attachment_type, "Attachment"),
            }
        except Exception as e:
            logger.warning("Failed to download Facebook attachment: %s", e)
            return {}

    # ------------------------------------------------------------------
    # Sync conversations from Page
    # ------------------------------------------------------------------

    async def sync_conversations(
        self,
        *,
        page_access_token: str,
        page_id: str,
        account_id: int,
        media_dir: Path,
        limit: int = 20,
    ) -> dict[str, int]:
        """Sync recent conversations from a Facebook Page."""
        from .db import upsert_chat, save_message

        client = self._client()
        chats_synced = 0
        messages_synced = 0

        await self._emit_event({
            "type": "sync:start",
            "account_id": account_id,
            "full_history": False,
        })

        try:
            # Get conversations
            response = await client.get(
                f"{GRAPH_API_BASE}/{page_id}/conversations",
                params={
                    "fields": "participants,updated_time,messages.limit(10){message,from,created_time,attachments}",
                    "limit": str(limit),
                    "access_token": page_access_token,
                },
            )

            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", response.text)
                raise RuntimeError(f"Facebook API error: {error_msg}")

            data = response.json()
            conversations = data.get("data", [])

            for conversation in conversations:
                # Find the non-page participant
                participants = conversation.get("participants", {}).get("data", [])
                external_chat_id = ""
                participant_name = "Facebook User"
                for participant in participants:
                    pid = str(participant.get("id", ""))
                    if pid != page_id:
                        external_chat_id = pid
                        participant_name = participant.get("name", f"User {pid}")
                        break

                if not external_chat_id:
                    continue

                # Upsert chat
                profile = await self._get_user_profile(page_access_token, external_chat_id)
                chat_row = upsert_chat(
                    account_id,
                    external_chat_id,
                    participant_name,
                    chat_type="private",
                    last_message_at=conversation.get("updated_time"),
                    profile_first_name=profile.first_name,
                    profile_last_name=profile.last_name,
                )
                chats_synced += 1

                await self._emit_event({
                    "type": "chat:upsert",
                    "source": "facebook-sync",
                    "account_id": account_id,
                    "chat": chat_row,
                })

                # Process messages
                messages_data = conversation.get("messages", {}).get("data", [])
                for msg in reversed(messages_data):  # oldest first
                    from_data = msg.get("from", {})
                    from_id = str(from_data.get("id", ""))
                    from_name = from_data.get("name", "Unknown")
                    direction = "out" if from_id == page_id else "in"
                    sender_name = "You" if direction == "out" else from_name

                    text = msg.get("message", "")
                    external_message_id = msg.get("id")

                    # Process attachments from sync
                    attachment_info: dict[str, Any] = {}
                    msg_attachments = msg.get("attachments", {}).get("data", [])
                    if msg_attachments:
                        att = msg_attachments[0]
                        att_url = att.get("image_data", {}).get("url") or att.get("file_url") or att.get("video_data", {}).get("url")
                        if att_url:
                            mime_type = att.get("mime_type", "application/octet-stream")
                            att_type_raw = att.get("type", "file")
                            attachment_info = await self._process_attachment(
                                {"type": att_type_raw if att_type_raw != "share" else "file", "payload": {"url": att_url}},
                                media_dir=media_dir,
                                account_id=account_id,
                                external_chat_id=external_chat_id,
                            )

                    save_message(
                        chat_id=chat_row["id"],
                        account_id=account_id,
                        direction=direction,
                        sender_name=sender_name,
                        text=text or attachment_info.get("fallback_text", ""),
                        telegram_message_id=None,
                        external_message_id=external_message_id,
                        attachment_type=attachment_info.get("attachment_type"),
                        attachment_name=attachment_info.get("attachment_name"),
                        attachment_path=attachment_info.get("attachment_path"),
                        attachment_mime=attachment_info.get("attachment_mime"),
                        attachment_size=attachment_info.get("attachment_size"),
                        update_chat=False,
                    )
                    messages_synced += 1

                logger.info("FB sync: '%s' done — %d messages", participant_name, len(messages_data))

        except Exception as e:
            logger.error("Facebook sync failed for account %d: %s", account_id, e, exc_info=True)
            raise

        await self._emit_event({
            "type": "sync:complete",
            "account_id": account_id,
            "full_history": False,
            "chats_synced": chats_synced,
            "messages_synced": messages_synced,
        })

        logger.info("FB sync complete: account=%d chats=%d messages=%d", account_id, chats_synced, messages_synced)
        return {"chats_synced": chats_synced, "messages_synced": messages_synced}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_attachment_type(attachment_type: str | None, mime: str | None) -> str:
        """Map OmniDesk attachment types to Facebook attachment types."""
        if attachment_type in {"image", "sticker", "gif"}:
            return "image"
        if attachment_type == "video":
            return "video"
        if attachment_type in {"audio", "voice"}:
            return "audio"
        if mime:
            if mime.startswith("image/"):
                return "image"
            if mime.startswith("video/"):
                return "video"
            if mime.startswith("audio/"):
                return "audio"
        return "file"
