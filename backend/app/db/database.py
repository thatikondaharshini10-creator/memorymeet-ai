"""Database connection and metadata persistence setup (SQLite)."""
import sqlite3
import os
from typing import List, Dict, Any, Optional
from ..core.config import settings

DB_FILE = settings.DATABASE_URL.replace("sqlite:///", "")


def get_db_connection():
    """Provides a raw sqlite3 connection with dictionary row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema for basic meeting metadata if needed."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_FILE)) or ".", exist_ok=True)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transcript TEXT,
                summary TEXT,
                status TEXT DEFAULT 'pending'
            )
        """)
        conn.commit()


def save_meeting(title: str, transcript: str, summary: str, status: str = "completed") -> int:
    """Inserts a processed meeting record into SQLite and returns the row ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO meetings (title, transcript, summary, status)
            VALUES (?, ?, ?, ?)
            """,
            (title, transcript, summary, status)
        )
        conn.commit()
        return cursor.lastrowid


def get_all_meetings() -> List[Dict[str, Any]]:
    """Retrieves all past meeting records sorted by creation date descending."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, created_at, summary, status FROM meetings ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_meeting_by_id(meeting_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves full details of a specific meeting."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
