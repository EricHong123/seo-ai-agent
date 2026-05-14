"""KB file registry — now backed by shared SQLAlchemy engine (was raw sqlite3)."""

import json
import uuid
from datetime import datetime, timezone

from memory.structured.models import KBFile, get_session, init_db


def is_duplicate(file_hash: str) -> bool:
    session = get_session()
    row = session.query(KBFile).filter_by(file_hash=file_hash).first()
    session.close()
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
    init_db()
    file_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    session = get_session()
    record = KBFile(
        id=file_id,
        filename=filename,
        file_hash=file_hash,
        file_type=file_type,
        file_size_bytes=file_size_bytes,
        source=source,
        tags=json.dumps(tags or []),
        chunk_count=chunk_count,
        ingested_at=now,
        last_accessed_at=now,
        project_id=project_id,
    )
    session.add(record)
    session.commit()
    session.close()
    return file_id


def touch_record(file_id: str):
    session = get_session()
    record = session.query(KBFile).filter_by(id=file_id).first()
    if record:
        record.last_accessed_at = datetime.now(timezone.utc)
        session.commit()
    session.close()


def delete_record(file_id: str):
    session = get_session()
    session.query(KBFile).filter_by(id=file_id).delete()
    session.commit()
    session.close()


def list_records(project_id: str = "default") -> list[dict]:
    session = get_session()
    rows = (
        session.query(KBFile)
        .filter_by(project_id=project_id)
        .order_by(KBFile.ingested_at.desc())
        .all()
    )
    result = [
        {
            "id": r.id, "filename": r.filename, "file_hash": r.file_hash,
            "file_type": r.file_type, "file_size_bytes": r.file_size_bytes,
            "source": r.source, "tags": r.tags, "chunk_count": r.chunk_count,
            "ingested_at": r.ingested_at.isoformat() if r.ingested_at else None,
            "last_accessed_at": r.last_accessed_at.isoformat() if r.last_accessed_at else None,
            "project_id": r.project_id,
        }
        for r in rows
    ]
    session.close()
    return result


def get_by_filename(filename: str, project_id: str = "default") -> dict | None:
    session = get_session()
    row = session.query(KBFile).filter_by(filename=filename, project_id=project_id).first()
    result = _row_to_dict(row)
    session.close()
    return result


def get_by_id(file_id: str) -> dict | None:
    session = get_session()
    row = session.query(KBFile).filter_by(id=file_id).first()
    result = _row_to_dict(row)
    session.close()
    return result


def _row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return {
        "id": row.id, "filename": row.filename, "file_hash": row.file_hash,
        "file_type": row.file_type, "file_size_bytes": row.file_size_bytes,
        "source": row.source, "tags": row.tags, "chunk_count": row.chunk_count,
        "ingested_at": row.ingested_at.isoformat() if row.ingested_at else None,
        "last_accessed_at": row.last_accessed_at.isoformat() if row.last_accessed_at else None,
        "project_id": row.project_id,
    }
