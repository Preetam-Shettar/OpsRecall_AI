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
                severity TEXT DEFAULT 'medium',
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incident_actions (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'read_only',
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                assigned_engineer TEXT,
                command_hint TEXT,
                completion_notes TEXT,
                blocked_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incident_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT NOT NULL,
                actor TEXT DEFAULT 'OpsRecall AI',
                actor_type TEXT DEFAULT 'ai',
                related_action_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_actions_incident ON incident_actions(incident_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timeline_incident ON incident_timeline(incident_id)")

        # Migrate any missing columns if incidents table was created previously with older schema
        cursor = conn.execute("PRAGMA table_info(incidents)")
        inc_columns = [row["name"] for row in cursor.fetchall()]
        if "severity" not in inc_columns:
            conn.execute("ALTER TABLE incidents ADD COLUMN severity TEXT DEFAULT 'medium'")

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
