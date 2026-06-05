from __future__ import annotations

import logging
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("omnidesk.db")

from .telegram_gateway import build_session_path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = DATA_DIR / "media"
DB_PATH = DATA_DIR / "app.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                platform TEXT NOT NULL DEFAULT 'telegram',
                phone TEXT,
                status TEXT NOT NULL DEFAULT 'demo',
                api_id TEXT,
                api_hash TEXT,
                session_path TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                external_chat_id TEXT NOT NULL,
                title TEXT NOT NULL,
                custom_title TEXT,
                chat_type TEXT NOT NULL DEFAULT 'private',
                profile_first_name TEXT,
                profile_last_name TEXT,
                profile_username TEXT,
                profile_phone TEXT,
                profile_photo_path TEXT,
                profile_updated_at TEXT,
                last_message_at TEXT,
                unread_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                UNIQUE(account_id, external_chat_id)
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('in', 'out')),
                sender_name TEXT NOT NULL,
                text TEXT NOT NULL,
                telegram_message_id TEXT,
                client_message_id TEXT,
                delivery_status TEXT NOT NULL DEFAULT 'sent',
                delivery_error TEXT,
                attachment_type TEXT,
                attachment_name TEXT,
                attachment_path TEXT,
                attachment_mime TEXT,
                attachment_size INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            """
        )
        existing_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(accounts)").fetchall()
        }
        for column_sql in [
            "platform TEXT NOT NULL DEFAULT 'telegram'",
            "login_phone TEXT",
            "phone_code_hash TEXT",
            "last_error TEXT",
            "page_access_token TEXT",
            "page_id TEXT",
            "fb_app_secret TEXT",
        ]:
            column_name = column_sql.split()[0]
            if column_name not in existing_columns:
                conn.execute(f"ALTER TABLE accounts ADD COLUMN {column_sql}")

        message_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(messages)").fetchall()
        }
        for column_sql in [
            "attachment_type TEXT",
            "attachment_name TEXT",
            "attachment_path TEXT",
            "attachment_mime TEXT",
            "attachment_size INTEGER",
            "delivery_status TEXT NOT NULL DEFAULT 'sent'",
            "delivery_error TEXT",
            "client_message_id TEXT",
            "external_message_id TEXT",
        ]:
            column_name = column_sql.split()[0]
            if column_name not in message_columns:
                conn.execute(f"ALTER TABLE messages ADD COLUMN {column_sql}")

        chat_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(chats)").fetchall()
        }
        for column_sql in [
            "profile_first_name TEXT",
            "profile_last_name TEXT",
            "profile_username TEXT",
            "profile_phone TEXT",
            "profile_photo_path TEXT",
            "profile_updated_at TEXT",
            "custom_title TEXT",
        ]:
            column_name = column_sql.split()[0]
            if column_name not in chat_columns:
                conn.execute(f"ALTER TABLE chats ADD COLUMN {column_sql}")

        rows = conn.execute("SELECT id FROM accounts WHERE session_path IS NULL").fetchall()
        for row in rows:
            conn.execute(
                """
                UPDATE accounts
                SET session_path = ?
                WHERE id = ?
                """,
                (build_session_path(row["id"]), row["id"]),
            )
        conn.execute(
            """
            UPDATE accounts
            SET platform = 'telegram'
            WHERE platform IS NULL OR platform = ''
            """
        )
        conn.commit()


def seed_demo_data() -> None:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM accounts").fetchone()["c"]
        if count:
            rows = conn.execute(
                """
                SELECT id, display_name, platform
                FROM accounts
                ORDER BY id ASC
                LIMIT 6
                """
            ).fetchall()
            demo_layout = [
                ("Support 1", "telegram", "+855 100 000 001"),
                ("Support 2", "facebook_page", "page-001"),
                ("Support 3", "line", "line-001"),
                ("Support 4", "whatsapp", "+855 100 000 004"),
                ("Support 5", "instagram", "ig-001"),
                ("Support 6", "telegram", "+855 100 000 006"),
            ]
            if len(rows) == 6 and all(row["display_name"].startswith("Support ") for row in rows):
                for row, (display_name, platform, phone) in zip(rows, demo_layout, strict=False):
                    conn.execute(
                        """
                        UPDATE accounts
                        SET display_name = ?, platform = ?, phone = ?, status = 'demo',
                            api_id = NULL, api_hash = NULL
                        WHERE id = ?
                        """,
                        (display_name, platform, phone, row["id"]),
                    )
            conn.commit()
            return

        now = utc_now()
        accounts = [
            ("Support 1", "telegram", "+855 100 000 001"),
            ("Support 2", "facebook_page", "page-001"),
            ("Support 3", "line", "line-001"),
            ("Support 4", "whatsapp", "+855 100 000 004"),
            ("Support 5", "instagram", "ig-001"),
            ("Support 6", "telegram", "+855 100 000 006"),
        ]

        for display_name, platform, phone in accounts:
            cursor = conn.execute(
                """
                INSERT INTO accounts (display_name, platform, phone, status, api_id, api_hash, session_path, created_at)
                VALUES (?, ?, ?, 'demo', NULL, NULL, NULL, ?)
                """,
                (display_name, platform, phone, now),
            )
            account_id = cursor.lastrowid
            conn.execute(
                """
                UPDATE accounts
                SET session_path = ?
                WHERE id = ?
                """,
                (build_session_path(account_id), account_id),
            )

            for index, title in enumerate([f"Lead {account_id}-A", f"Lead {account_id}-B"], start=1):
                chat_cursor = conn.execute(
                    """
                    INSERT INTO chats (
                        account_id, external_chat_id, title, chat_type,
                        last_message_at, unread_count, created_at
                    )
                    VALUES (?, ?, ?, 'private', ?, ?, ?)
                    """,
                    (
                        account_id,
                        f"demo-{account_id}-{index}",
                        title,
                        now,
                        1 if index == 1 else 0,
                        now,
                    ),
                )
                chat_id = chat_cursor.lastrowid
                conn.execute(
                    """
                    INSERT INTO messages (
                        chat_id, account_id, direction, sender_name, text, telegram_message_id, created_at
                    )
                    VALUES (?, ?, 'in', ?, ?, NULL, ?)
                    """,
                    (
                        chat_id,
                        account_id,
                        title,
                        "Hello, I need help with my order.",
                        now,
                    ),
                )

        conn.commit()


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def chat_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    chat = dict(row)
    telegram_title = chat.get("title")
    custom_title = chat.get("custom_title")
    chat["telegram_title"] = telegram_title
    if custom_title:
        chat["title"] = custom_title
    profile_photo_path = chat.get("profile_photo_path")
    if profile_photo_path:
        normalized_path = str(profile_photo_path).replace("\\", "/").lstrip("/")
        chat["profile_photo_url"] = f"/media/{normalized_path}"
    else:
        chat["profile_photo_url"] = None
    return chat


def message_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    message = dict(row)
    attachment_path = message.get("attachment_path")
    if attachment_path:
        normalized_path = str(attachment_path).replace("\\", "/").lstrip("/")
        message["attachment_url"] = f"/media/{normalized_path}"
    else:
        message["attachment_url"] = None
    return message


def list_accounts() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM accounts
            ORDER BY id ASC
            """
        ).fetchall()
    return rows_to_dicts(rows)


def add_account(display_name: str, phone: str | None = None, platform: str = "telegram") -> dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO accounts (display_name, platform, phone, status, api_id, api_hash, session_path, created_at)
            VALUES (?, ?, ?, 'demo', NULL, NULL, NULL, ?)
            """,
            (display_name, platform, phone, utc_now()),
        )
        account_id = cursor.lastrowid
        conn.execute(
            """
            UPDATE accounts
            SET session_path = ?
            WHERE id = ?
            """,
            (build_session_path(account_id), account_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return dict(row)


def get_account(account_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return dict(row) if row else None


def update_account_profile(
    account_id: int,
    *,
    display_name: str | None = None,
    platform: str | None = None,
    phone: str | None = None,
    api_id: str | None = None,
    api_hash: str | None = None,
    session_path: str | None = None,
    page_access_token: str | None = None,
    page_id: str | None = None,
    fb_app_secret: str | None = None,
) -> dict[str, Any] | None:
    fields: list[str] = []
    values: list[Any] = []

    if display_name is not None:
        fields.append("display_name = ?")
        values.append(display_name)
    if platform is not None:
        fields.append("platform = ?")
        values.append(platform)
    if phone is not None:
        fields.append("phone = ?")
        values.append(phone)
    if api_id is not None:
        fields.append("api_id = ?")
        values.append(api_id)
    if api_hash is not None:
        fields.append("api_hash = ?")
        values.append(api_hash)
    if session_path is not None:
        fields.append("session_path = ?")
        values.append(session_path)
    if page_access_token is not None:
        fields.append("page_access_token = ?")
        values.append(page_access_token)
    if page_id is not None:
        fields.append("page_id = ?")
        values.append(page_id)
    if fb_app_secret is not None:
        fields.append("fb_app_secret = ?")
        values.append(fb_app_secret)

    if not fields:
        return get_account(account_id)

    with get_connection() as conn:
        conn.execute(
            f"""
            UPDATE accounts
            SET {", ".join(fields)}
            WHERE id = ?
            """,
            (*values, account_id),
        )
        conn.commit()
    return get_account(account_id)


def delete_account(account_id: int) -> bool:
    """Delete an account and all its chats/messages (via CASCADE)."""
    account = get_account(account_id)
    if not account:
        return False

    with get_connection() as conn:
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()

    # Remove session file if it exists
    session_path = account.get("session_path")
    if session_path:
        for ext in ("", ".session"):
            p = Path(str(session_path) + ext)
            if p.exists():
                try:
                    p.unlink()
                    logger.info("Removed session file: %s", p)
                except OSError as e:
                    logger.warning("Could not remove session file %s: %s", p, e)

    logger.info("Deleted account %d (%s)", account_id, account.get("display_name", "?"))
    return True


def update_account_login_state(
    account_id: int,
    *,
    status: str | None = None,
    phone: str | None = None,
    phone_code_hash: str | None = None,
    last_error: str | None = None,
    clear_error: bool = False,
) -> dict[str, Any] | None:
    fields: list[str] = []
    values: list[Any] = []

    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if phone is not None:
        fields.append("login_phone = ?")
        values.append(phone)
    if phone_code_hash is not None:
        fields.append("phone_code_hash = ?")
        values.append(phone_code_hash)
    if clear_error:
        fields.append("last_error = NULL")
    elif last_error is not None:
        fields.append("last_error = ?")
        values.append(last_error)

    if not fields:
        return get_account(account_id)

    _db_error: Exception | None = None
    for attempt in range(5):
        try:
            with get_connection() as conn:
                conn.execute(
                    f"""
                    UPDATE accounts
                    SET {", ".join(fields)}
                    WHERE id = ?
                    """,
                    (*values, account_id),
                )
                conn.commit()
            break
        except sqlite3.OperationalError as error:
            _db_error = error
            if "database is locked" not in str(error).lower() or attempt >= 4:
                raise
            logger.warning("Database locked on update_account_login_state (attempt %d/5)", attempt + 1)
            time.sleep(0.25 * (attempt + 1))
    if _db_error and attempt >= 4:
        raise _db_error
    return get_account(account_id)


def get_account_by_page_id(page_id: str) -> dict[str, Any] | None:
    """Find an account by its Facebook page_id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE page_id = ? AND platform = 'facebook_page'",
            (page_id,),
        ).fetchone()
    return dict(row) if row else None


def list_chats(account_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM chats
            WHERE account_id = ?
            ORDER BY COALESCE(last_message_at, created_at) DESC, id DESC
            """,
            (account_id,),
        ).fetchall()
    return [chat_row_to_dict(row) for row in rows]


def list_all_chats() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM chats
            ORDER BY COALESCE(last_message_at, created_at) DESC, id DESC
            """
        ).fetchall()
    return [chat_row_to_dict(row) for row in rows]


def get_chat(chat_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
    return chat_row_to_dict(row) if row else None


def get_chat_by_external_id(account_id: int, external_chat_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM chats
            WHERE account_id = ? AND external_chat_id = ?
            """,
            (account_id, external_chat_id),
        ).fetchone()
    return chat_row_to_dict(row) if row else None


def rename_chat(chat_id: int, display_name: str) -> dict[str, Any] | None:
    cleaned = display_name.strip()
    if not cleaned:
        raise ValueError("Display name is required")

    with get_connection() as conn:
        chat = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
        if not chat:
            return None
        conn.execute(
            """
            UPDATE chats
            SET custom_title = ?
            WHERE id = ?
            """,
            (cleaned, chat_id),
        )
        conn.execute(
            """
            UPDATE messages
            SET sender_name = ?
            WHERE chat_id = ? AND direction = 'in'
            """,
            (cleaned, chat_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,)).fetchone()
    return chat_row_to_dict(row) if row else None


def upsert_chat(
    account_id: int,
    external_chat_id: str,
    title: str,
    *,
    chat_type: str = "private",
    last_message_at: str | None = None,
    profile_first_name: str | None = None,
    profile_last_name: str | None = None,
    profile_username: str | None = None,
    profile_phone: str | None = None,
    profile_photo_path: str | None = None,
) -> dict[str, Any]:
    now = utc_now()
    profile_updated_at = now if any([profile_first_name, profile_last_name, profile_username, profile_phone, profile_photo_path]) else None
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT *
            FROM chats
            WHERE account_id = ? AND external_chat_id = ?
            """,
            (account_id, external_chat_id),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE chats
                SET title = ?,
                    chat_type = ?,
                    profile_first_name = COALESCE(?, profile_first_name),
                    profile_last_name = COALESCE(?, profile_last_name),
                    profile_username = COALESCE(?, profile_username),
                    profile_phone = COALESCE(?, profile_phone),
                    profile_photo_path = COALESCE(?, profile_photo_path),
                    profile_updated_at = COALESCE(?, profile_updated_at),
                    last_message_at = COALESCE(?, last_message_at)
                WHERE id = ?
                """,
                (
                    title,
                    chat_type,
                    profile_first_name,
                    profile_last_name,
                    profile_username,
                    profile_phone,
                    profile_photo_path,
                    profile_updated_at,
                    last_message_at,
                    existing["id"],
                ),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM chats WHERE id = ?", (existing["id"],)).fetchone()
            return chat_row_to_dict(row)

        cursor = conn.execute(
            """
            INSERT INTO chats (
                account_id, external_chat_id, title, chat_type,
                profile_first_name, profile_last_name, profile_username, profile_phone,
                profile_photo_path, profile_updated_at,
                last_message_at, unread_count, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                account_id,
                external_chat_id,
                title,
                chat_type,
                profile_first_name,
                profile_last_name,
                profile_username,
                profile_phone,
                profile_photo_path,
                profile_updated_at,
                last_message_at,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM chats WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return chat_row_to_dict(row)


def list_messages(chat_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,),
        ).fetchall()
    return [message_row_to_dict(row) for row in rows]


def infer_read_receipts_from_incoming(chat_id: int) -> list[dict[str, Any]]:
    """Infer read receipts when an incoming Telegram reply arrives after our sent messages."""
    updated: list[dict[str, Any]] = []
    with get_connection() as conn:
        latest_incoming = conn.execute(
            """
            SELECT MAX(CAST(telegram_message_id AS INTEGER)) AS max_id
            FROM messages
            WHERE chat_id = ?
              AND direction = 'in'
              AND telegram_message_id IS NOT NULL
              AND telegram_message_id GLOB '[0-9]*'
            """,
            (chat_id,),
        ).fetchone()
        max_id = latest_incoming["max_id"] if latest_incoming else None
        if not max_id:
            return updated

        rows = conn.execute(
            """
            SELECT id
            FROM messages
            WHERE chat_id = ?
              AND direction = 'out'
              AND delivery_status = 'sent'
              AND telegram_message_id IS NOT NULL
              AND telegram_message_id GLOB '[0-9]*'
              AND CAST(telegram_message_id AS INTEGER) < ?
            """,
            (chat_id, max_id),
        ).fetchall()
        if not rows:
            return updated

        ids = [row["id"] for row in rows]
        placeholders = ", ".join("?" for _ in ids)
        conn.execute(
            f"UPDATE messages SET delivery_status = 'read' WHERE id IN ({placeholders})",
            ids,
        )
        conn.commit()

        for message_id in ids:
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
            if row:
                updated.append(message_row_to_dict(row))
    return updated


def get_message_by_telegram_id(chat_id: int, telegram_message_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM messages
            WHERE chat_id = ? AND telegram_message_id = ?
            """,
            (chat_id, telegram_message_id),
        ).fetchone()
    return message_row_to_dict(row) if row else None


def get_message_by_external_id(chat_id: int, external_message_id: str) -> dict[str, Any] | None:
    """Find a message by its Facebook/external message ID."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM messages
            WHERE chat_id = ? AND external_message_id = ?
            """,
            (chat_id, external_message_id),
        ).fetchone()
    return message_row_to_dict(row) if row else None


def get_message(message_id: int) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    return message_row_to_dict(row) if row else None


def delete_message(message_id: int) -> dict[str, Any] | None:
    message = get_message(message_id)
    if not message:
        return None

    chat_id = int(message["chat_id"])
    attachment_path = message.get("attachment_path")
    with get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        if message.get("direction") == "in":
            conn.execute(
                """
                UPDATE chats
                SET unread_count = MAX(unread_count - 1, 0)
                WHERE id = ?
                """,
                (chat_id,),
            )
        latest = conn.execute(
            """
            SELECT MAX(created_at) AS latest_created_at
            FROM messages
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()
        conn.execute(
            """
            UPDATE chats
            SET last_message_at = ?
            WHERE id = ?
            """,
            (latest["latest_created_at"] if latest else None, chat_id),
        )
        remaining_attachment_refs = 0
        if attachment_path:
            remaining_attachment_refs = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM messages
                WHERE attachment_path = ?
                """,
                (attachment_path,),
            ).fetchone()["count"]
        conn.commit()

    if attachment_path and not remaining_attachment_refs:
        candidate = (MEDIA_DIR / str(attachment_path)).resolve()
        try:
            candidate.relative_to(MEDIA_DIR.resolve())
            candidate.unlink(missing_ok=True)
        except (OSError, ValueError) as error:
            logger.warning("Could not remove attachment file for deleted message %d: %s", message_id, error)

    logger.info("Deleted message %d from chat %d", message_id, chat_id)
    return message


def save_message(
    chat_id: int,
    account_id: int,
    direction: str,
    sender_name: str,
    text: str,
    telegram_message_id: str | None = None,
    *,
    client_message_id: str | None = None,
    external_message_id: str | None = None,
    delivery_status: str = "sent",
    delivery_error: str | None = None,
    attachment_type: str | None = None,
    attachment_name: str | None = None,
    attachment_path: str | None = None,
    attachment_mime: str | None = None,
    attachment_size: int | None = None,
    update_chat: bool = True,
) -> dict[str, Any]:
    if telegram_message_id is not None:
        existing = get_message_by_telegram_id(chat_id, telegram_message_id)
        if existing:
            return existing
    if external_message_id is not None:
        existing = get_message_by_external_id(chat_id, external_message_id)
        if existing:
            return existing

    now = utc_now()
    with get_connection() as conn:
        cursor = conn.execute(
              """
              INSERT INTO messages (
                  chat_id, account_id, direction, sender_name, text, telegram_message_id, client_message_id,
                  external_message_id, delivery_status, delivery_error,
                  attachment_type, attachment_name, attachment_path, attachment_mime, attachment_size,
                  created_at
              )
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              """,
            (
                chat_id,
                account_id,
                direction,
                sender_name,
                text,
                telegram_message_id,
                client_message_id,
                external_message_id,
                delivery_status,
                delivery_error,
                attachment_type,
                attachment_name,
                attachment_path,
                attachment_mime,
                attachment_size,
                now,
            ),
        )
        if update_chat:
            if direction == "in":
                conn.execute(
                    """
                    UPDATE chats
                    SET unread_count = unread_count + 1,
                        last_message_at = ?
                    WHERE id = ?
                    """,
                    (now, chat_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE chats
                    SET last_message_at = ?,
                        unread_count = 0
                    WHERE id = ?
                    """,
                    (now, chat_id),
                )
        conn.commit()
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return message_row_to_dict(row)


def update_message_delivery(
    message_id: int,
    *,
    telegram_message_id: str | None = None,
    delivery_status: str | None = None,
    delivery_error: str | None = None,
) -> dict[str, Any] | None:
    fields: list[str] = []
    values: list[Any] = []

    if telegram_message_id is not None:
        fields.append("telegram_message_id = ?")
        values.append(telegram_message_id)
    if delivery_status is not None:
        fields.append("delivery_status = ?")
        values.append(delivery_status)
    if delivery_error is not None:
        fields.append("delivery_error = ?")
        values.append(delivery_error)

    if not fields:
        return None

    with get_connection() as conn:
        conn.execute(
            f"""
            UPDATE messages
            SET {", ".join(fields)}
            WHERE id = ?
            """,
            (*values, message_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    return message_row_to_dict(row) if row else None


def mark_messages_read_by_telegram_id(
    account_id: int,
    external_chat_id: str,
    max_telegram_id: int,
) -> list[dict[str, Any]]:
    """Mark outgoing messages as 'read' where telegram_message_id <= max_telegram_id.
    Returns list of updated message dicts."""
    updated = []
    with get_connection() as conn:
        # Find chat for this account + external_chat_id
        chat = conn.execute(
            "SELECT id FROM chats WHERE account_id = ? AND external_chat_id = ?",
            (account_id, str(external_chat_id)),
        ).fetchone()
        if not chat:
            return updated

        chat_id = chat["id"]
        rows = conn.execute(
            """
            SELECT id, telegram_message_id FROM messages
            WHERE chat_id = ? AND direction = 'out'
              AND delivery_status = 'sent'
              AND telegram_message_id IS NOT NULL
              AND telegram_message_id GLOB '[0-9]*'
              AND CAST(telegram_message_id AS INTEGER) <= ?
            """,
            (chat_id, max_telegram_id),
        ).fetchall()

        if not rows:
            return updated

        ids = [r["id"] for r in rows]
        placeholders = ", ".join("?" for _ in ids)
        conn.execute(
            f"UPDATE messages SET delivery_status = 'read' WHERE id IN ({placeholders})",
            ids,
        )
        conn.commit()

        for msg_id in ids:
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (msg_id,)).fetchone()
            if row:
                updated.append(message_row_to_dict(row))

    return updated


def touch_chat(chat_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE chats
            SET unread_count = 0
            WHERE id = ?
            """,
            (chat_id,),
        )
        conn.commit()
