import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config.settings import settings


DB_PATH = settings.kb_dir / "registry.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS kb_files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size_bytes INTEGER DEFAULT 0,
            source TEXT NOT NULL DEFAULT 'user_upload',
            tags TEXT DEFAULT '[]',
            chunk_count INTEGER DEFAULT 0,
            ingested_at TEXT NOT NULL,
            last_accessed_at TEXT NOT NULL,
            project_id TEXT NOT NULL DEFAULT 'default'
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_file_hash ON kb_files(file_hash);
    """)
    c.commit()
    c.close()


def is_duplicate(file_hash: str) -> bool:
    c = _conn()
    row = c.execute("SELECT 1 FROM kb_files WHERE file_hash = ?", (file_hash,)).fetchone()
    c.close()
    return row is not None


def add_record(
    filename: str,
    file_hash: str,
    file_type: str,
    source: str,
    chunk_count: int,
    project_id: str = "default",
    file_size_bytes: int = 0,
    tags: list[str] | None = None,
) -> str:
    file_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    c = _conn()
    c.execute(
        """INSERT INTO kb_files (id, filename, file_hash, file_type, file_size_bytes, source, tags, chunk_count, ingested_at, last_accessed_at, project_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (file_id, filename, file_hash, file_type, file_size_bytes, source, json.dumps(tags or []), chunk_count, now, now, project_id),
    )
    c.commit()
    c.close()
    return file_id


def touch_record(file_id: str):
    now = datetime.now(timezone.utc).isoformat()
    c = _conn()
    c.execute("UPDATE kb_files SET last_accessed_at = ? WHERE id = ?", (now, file_id))
    c.commit()
    c.close()


def delete_record(file_id: str):
    c = _conn()
    c.execute("DELETE FROM kb_files WHERE id = ?", (file_id,))
    c.commit()
    c.close()


def list_records(project_id: str = "default") -> list[dict]:
    c = _conn()
    rows = c.execute(
        "SELECT * FROM kb_files WHERE project_id = ? ORDER BY ingested_at DESC",
        (project_id,),
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_by_filename(filename: str, project_id: str = "default") -> dict | None:
    c = _conn()
    row = c.execute(
        "SELECT * FROM kb_files WHERE filename = ? AND project_id = ?",
        (filename, project_id),
    ).fetchone()
    c.close()
    return dict(row) if row else None


def get_by_id(file_id: str) -> dict | None:
    c = _conn()
    row = c.execute("SELECT * FROM kb_files WHERE id = ?", (file_id,)).fetchone()
    c.close()
    return dict(row) if row else None
