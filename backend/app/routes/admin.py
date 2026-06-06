from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..db import DATA_DIR, DB_PATH, add_user, get_connection, init_db, list_users, set_user_active
from .auth import SESSION_COOKIE_NAME, get_current_user
from ..telegram_gateway import build_session_path

logger = logging.getLogger("omnidesk.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])

EXPECTED_TABLES = {"accounts", "chats", "messages"}


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=256)


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


def require_super_admin(omnidesk_session: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)) -> dict:
    user = get_current_user(omnidesk_session)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Super admin permission required")
    return user


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _validate_sqlite(path: Path) -> dict[str, int]:
    try:
        with sqlite3.connect(path) as conn:
            conn.row_factory = sqlite3.Row
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise HTTPException(status_code=400, detail=f"SQLite integrity check failed: {integrity}")

            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            missing = sorted(EXPECTED_TABLES - tables)
            if missing:
                raise HTTPException(status_code=400, detail=f"Missing required tables: {', '.join(missing)}")

            return {
                "accounts": conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
                "chats": conn.execute("SELECT COUNT(*) FROM chats").fetchone()[0],
                "messages": conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
            }
    except HTTPException:
        raise
    except sqlite3.Error as error:
        raise HTTPException(status_code=400, detail=f"Invalid SQLite database: {error}") from error


def _copy_current_database_backup() -> str | None:
    if not DB_PATH.exists():
        return None

    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"app-before-restore-{_utc_stamp()}.db"
    shutil.copy2(DB_PATH, backup_path)
    return str(backup_path)


def _remove_sqlite_sidecars() -> None:
    for suffix in ("-wal", "-shm"):
        sidecar = Path(f"{DB_PATH}{suffix}")
        if sidecar.exists():
            sidecar.unlink()


def _install_uploaded_database(uploaded_db: Path) -> None:
    staging_db = DB_PATH.with_name(f"{DB_PATH.name}.restore-staging-{_utc_stamp()}")
    shutil.copy2(uploaded_db, staging_db)
    _validate_sqlite(staging_db)
    _remove_sqlite_sidecars()
    os.replace(staging_db, DB_PATH)
    _remove_sqlite_sidecars()


def _normalize_restored_database(*, session_uploaded: bool) -> dict[str, int]:
    init_db()

    with get_connection() as conn:
        accounts = conn.execute("SELECT id, platform FROM accounts ORDER BY id ASC").fetchall()
        for account in accounts:
            account_id = int(account["id"])
            platform = str(account["platform"] or "telegram")
            session_path = build_session_path(account_id)
            if platform == "telegram":
                status = "authorized" if session_uploaded else "error"
                last_error = None if session_uploaded else "Telegram session was not restored. Please log in again on Render."
                conn.execute(
                    """
                    UPDATE accounts
                    SET session_path = ?, phone_code_hash = NULL, status = ?, last_error = ?
                    WHERE id = ?
                    """,
                    (session_path, status, last_error, account_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE accounts
                    SET session_path = ?, phone_code_hash = NULL
                    WHERE id = ?
                    """,
                    (session_path, account_id),
                )

        counts = {
            "accounts": conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0],
            "chats": conn.execute("SELECT COUNT(*) FROM chats").fetchone()[0],
            "messages": conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        }
        conn.commit()
        return counts


async def _save_upload(upload: UploadFile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as target:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)


@router.post("/restore-sqlite")
async def api_restore_sqlite(
    db_file: UploadFile = File(...),
    session_file: UploadFile | None = File(None),
    _super_admin: dict = Depends(require_super_admin),
) -> dict:
    """Restore an OmniDesk SQLite database onto the persistent data disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    temp_dir_raw = tempfile.mkdtemp(prefix="omnidesk-restore-")
    temp_dir = Path(temp_dir_raw)
    try:
        uploaded_db = temp_dir / "uploaded-restore.db"
        await _save_upload(db_file, uploaded_db)
        uploaded_counts = _validate_sqlite(uploaded_db)

        backup_path = _copy_current_database_backup()
        _install_uploaded_database(uploaded_db)

        session_uploaded = False
        if session_file is not None and session_file.filename:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                first_telegram = conn.execute(
                    """
                    SELECT id
                    FROM accounts
                    WHERE platform = 'telegram'
                    ORDER BY id ASC
                    LIMIT 1
                    """
                ).fetchone()
            if first_telegram:
                session_destination = Path(f"{build_session_path(int(first_telegram['id']))}.session")
                await _save_upload(session_file, session_destination)
                session_uploaded = True

        restored_counts = _normalize_restored_database(session_uploaded=session_uploaded)
        return {
            "status": "restored",
            "backup_path": backup_path,
            "uploaded_counts": uploaded_counts,
            "restored_counts": restored_counts,
            "session_uploaded": session_uploaded,
        }
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Database restore failed")
        raise HTTPException(status_code=500, detail=f"Database restore failed: {error}") from error
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            logger.debug("Failed to clean restore temp dir %s", temp_dir, exc_info=True)


@router.get("/users")
def api_list_admin_users(_super_admin: dict = Depends(require_super_admin)) -> list[dict]:
    return list_users()


@router.post("/users")
def api_create_admin_user(
    payload: AdminUserCreate,
    _super_admin: dict = Depends(require_super_admin),
) -> dict:
    username = payload.username.strip()
    display_name = payload.display_name.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    if not display_name:
        raise HTTPException(status_code=400, detail="Display name is required")
    if any(char.isspace() for char in username):
        raise HTTPException(status_code=400, detail="Username cannot contain spaces")
    try:
        return add_user(username=username, display_name=display_name, password=payload.password, role="Admin")
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.patch("/users/{user_id}")
def api_update_admin_user_status(
    user_id: int,
    payload: AdminUserStatusUpdate,
    _super_admin: dict = Depends(require_super_admin),
) -> dict:
    try:
        user = set_user_active(user_id, payload.is_active)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
