from __future__ import annotations

import asyncio
import logging
import subprocess
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

logger = logging.getLogger("omnidesk.attachment")

# Resolved at import time — updated by main.py before first use.
MEDIA_DIR: Path = Path(__file__).resolve().parents[2] / "data" / "media"


def set_media_dir(path: Path) -> None:
    """Called once during app startup to set the canonical media directory."""
    global MEDIA_DIR
    MEDIA_DIR = path


def attachment_type_for(mime_type: str | None, filename: str | None = None, forced_type: str | None = None) -> str:
    lower_name = (filename or "").lower()
    normalized_mime = (mime_type or "").split(";", 1)[0].strip().lower()
    normalized_forced_type = (forced_type or "").strip().lower()
    if normalized_forced_type == "voice":
        return "voice"
    if lower_name.startswith("voice-") and lower_name.endswith((".webm", ".ogg", ".oga", ".opus")):
        return "voice"
    if normalized_mime in {"audio/ogg", "audio/opus", "audio/webm"}:
        return "voice"
    if normalized_forced_type in {"image", "video", "audio", "gif", "sticker", "file"}:
        return normalized_forced_type
    if normalized_mime:
        if normalized_mime == "application/x-tgsticker":
            return "sticker"
        if normalized_mime == "image/gif":
            return "gif"
        if normalized_mime == "image/webp":
            return "sticker"
        if normalized_mime.startswith("image/"):
            return "image"
        if normalized_mime.startswith("video/"):
            return "video"
        if normalized_mime.startswith("audio/"):
            return "audio"
    if lower_name.endswith(".tgs"):
        return "sticker"
    if lower_name.endswith(".webp"):
        return "sticker"
    if lower_name.endswith(".gif"):
        return "gif"
    if lower_name.endswith((".ogg", ".opus", ".oga", ".webm")):
        return "voice"
    if lower_name.endswith((".mp3", ".m4a", ".wav", ".aac", ".flac")):
        return "audio"
    return "file"


def build_attachment_url(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    normalized = str(relative_path).replace("\\", "/").lstrip("/")
    return f"/media/{normalized}"


def attachment_fallback_text(attachment_data: dict[str, object]) -> str:
    attachment_type = str(attachment_data.get("attachment_type") or "")
    attachment_name = str(attachment_data.get("attachment_name") or "Attachment")
    if attachment_type == "sticker":
        return "Sticker"
    if attachment_type == "gif":
        return "GIF"
    if attachment_type == "voice":
        return "Voice message"
    if attachment_type == "audio":
        return "Audio file"
    return attachment_name


def resolve_attachment_file_path(attachment_data: dict[str, object] | None) -> str | None:
    if not attachment_data:
        return None
    relative_path = attachment_data.get("attachment_path")
    if not relative_path:
        return None
    candidate = (MEDIA_DIR / str(relative_path)).resolve()
    try:
        candidate.relative_to(MEDIA_DIR.resolve())
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid attachment path") from error
    return str(candidate)


def resolve_message_attachment_file_path(message: dict[str, object] | None) -> str | None:
    if not message:
        return None
    relative_path = message.get("attachment_path")
    if not relative_path:
        return None
    candidate = (MEDIA_DIR / str(relative_path)).resolve()
    try:
        candidate.relative_to(MEDIA_DIR.resolve())
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Invalid attachment path") from error
    return str(candidate)


def user_facing_error(error: Exception) -> str:
    if isinstance(error, asyncio.TimeoutError):
        return "Send timed out. Please try again."
    message = str(error) or error.__class__.__name__ or "Request failed"
    if "Facebook API error" in message:
        return message.replace("Facebook API error: ", "")
    return message


def convert_voice_upload_to_ogg(source: Path) -> Path:
    try:
        import imageio_ffmpeg
    except ImportError as error:
        raise RuntimeError("Install imageio-ffmpeg to prepare Telegram voice notes.") from error

    output_path = source.with_suffix(".ogg")
    if output_path == source:
        return source

    command = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-y",
        "-loglevel",
        "error",
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
    return output_path


async def persist_upload(upload: UploadFile, *, account_id: int, chat_id: int, direction: str, forced_type: str | None = None) -> dict[str, object]:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    upload_dir = MEDIA_DIR / f"{direction}-{account_id}-{chat_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = upload.filename or "attachment"
    suffix = Path(original_name).suffix.lower()
    if len(suffix) > 10:
        suffix = ""
    file_name = f"{uuid4().hex}{suffix}"
    destination = upload_dir / file_name

    data = await upload.read()
    destination.write_bytes(data)

    mime_type = upload.content_type or "application/octet-stream"
    att_type = attachment_type_for(mime_type, original_name, forced_type=forced_type)
    attachment_size = len(data)
    if att_type == "voice":
        try:
            converted_destination = convert_voice_upload_to_ogg(destination)
        except RuntimeError:
            destination.unlink(missing_ok=True)
            raise
        if converted_destination != destination:
            destination.unlink(missing_ok=True)
        destination = converted_destination
        original_name = "voice.ogg"
        mime_type = "audio/ogg"
        attachment_size = destination.stat().st_size

    relative_path = str(destination.relative_to(MEDIA_DIR)).replace("\\", "/")
    return {
        "attachment_type": att_type,
        "attachment_name": original_name,
        "attachment_path": relative_path,
        "attachment_mime": mime_type,
        "attachment_size": attachment_size,
    }
