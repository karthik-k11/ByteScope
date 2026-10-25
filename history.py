import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def initialize_history(database_path):
    database = Path(database_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                size INTEGER NOT NULL,
                detected_type TEXT NOT NULL,
                report_json TEXT NOT NULL
            )
            """
        )


def save_analysis(database_path, report):
    initialize_history(database_path)
    analysis_id = uuid4().hex
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO analyses (id, created_at, name, size, detected_type, report_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_id,
                datetime.now(timezone.utc).isoformat(),
                report["name"],
                report["size"],
                report["detected_type"],
                json.dumps(report, ensure_ascii=True),
            ),
        )
    return analysis_id


def list_analyses(database_path, limit=50):
    initialize_history(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, created_at, name, size, detected_type
            FROM analyses ORDER BY created_at DESC, rowid DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_analysis(database_path, analysis_id):
    initialize_history(database_path)
    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT report_json FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None
