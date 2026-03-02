"""SQLite-backed deduplication store for sent articles."""
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "sent_articles.db"
RETENTION_DAYS = 7

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sent_articles (
    url      TEXT PRIMARY KEY,
    title    TEXT,
    sent_at  TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()
    return conn


def is_sent(url: str) -> bool:
    """Return True if the article URL has already been sent."""
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM sent_articles WHERE url = ?", (url,)).fetchone()
        return row is not None


def mark_sent(url: str, title: str) -> None:
    """Record an article URL as sent (idempotent)."""
    now = datetime.now(tz=timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sent_articles (url, title, sent_at) VALUES (?, ?, ?)",
            (url, title, now),
        )
        conn.commit()


def cleanup_old_records() -> int:
    """Delete records older than RETENTION_DAYS. Returns number of rows deleted."""
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM sent_articles WHERE sent_at < ?", (cutoff,))
        conn.commit()
        deleted = cursor.rowcount
    if deleted:
        logger.info("Cleaned up %d old sent_articles records", deleted)
    return deleted
