import sqlite3
from datetime import datetime
from config import DB_PATH


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id      INTEGER PRIMARY KEY,
                username     TEXT,
                frequency    TEXT    DEFAULT 'daily',
                send_hour    INTEGER DEFAULT 9,
                send_minute  INTEGER DEFAULT 0,
                utc_offset   INTEGER DEFAULT 0,
                is_active    INTEGER DEFAULT 1,
                next_send_utc TEXT,
                created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def upsert_user(chat_id: int, username: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (chat_id, username) VALUES (?, ?)",
            (chat_id, username),
        )
        conn.commit()


def get_user(chat_id: int) -> sqlite3.Row | None:
    with _conn() as conn:
        return conn.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,)).fetchone()


def update_frequency(chat_id: int, frequency: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE users SET frequency = ? WHERE chat_id = ?", (frequency, chat_id))
        conn.commit()


def update_time(chat_id: int, hour: int, minute: int) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE users SET send_hour = ?, send_minute = ? WHERE chat_id = ?",
            (hour, minute, chat_id),
        )
        conn.commit()


def update_utc_offset(chat_id: int, offset: int) -> None:
    with _conn() as conn:
        conn.execute("UPDATE users SET utc_offset = ? WHERE chat_id = ?", (offset, chat_id))
        conn.commit()


def update_next_send(chat_id: int, next_send: datetime) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE users SET next_send_utc = ? WHERE chat_id = ?",
            (next_send.isoformat(), chat_id),
        )
        conn.commit()


def set_active(chat_id: int, active: bool) -> None:
    with _conn() as conn:
        conn.execute("UPDATE users SET is_active = ? WHERE chat_id = ?", (int(active), chat_id))
        conn.commit()


def get_due_users(now: datetime) -> list[sqlite3.Row]:
    with _conn() as conn:
        return conn.execute(
            """
            SELECT * FROM users
            WHERE is_active = 1
              AND next_send_utc IS NOT NULL
              AND next_send_utc <= ?
            """,
            (now.isoformat(),),
        ).fetchall()
