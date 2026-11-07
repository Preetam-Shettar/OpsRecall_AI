import sqlite3
from pathlib import Path

from app.config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                service TEXT,
                environment TEXT,
                description TEXT,
                logs TEXT,
                sanitized_logs TEXT,
                status TEXT DEFAULT 'new',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                analysis_json TEXT,
                feedback_json TEXT,
                resolution_json TEXT,
                metadata_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_id TEXT DEFAULT 'opsrecall-incidents',
                incident_id TEXT,
                service TEXT,
                content TEXT NOT NULL,
                context TEXT,
                outcome TEXT DEFAULT 'resolved',
                verified INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Migrate any missing columns if memories table was created previously with older schema
        cursor = conn.execute("PRAGMA table_info(memories)")
        columns = [row["name"] for row in cursor.fetchall()]
        for col, col_type in [
            ("bank_id", "TEXT DEFAULT 'opsrecall-incidents'"),
            ("incident_id", "TEXT"),
            ("service", "TEXT"),
            ("outcome", "TEXT DEFAULT 'resolved'"),
            ("verified", "INTEGER DEFAULT 1"),
        ]:
            if col not in columns:
                conn.execute(f"ALTER TABLE memories ADD COLUMN {col} {col_type}")
