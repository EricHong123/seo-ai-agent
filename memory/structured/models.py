import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, event, Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Session

from config.settings import settings


class Base(DeclarativeBase):
    pass


# ── Business models ────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    target_audience = Column(String, default="")
    brand_voice = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class KeywordRanking(Base):
    __tablename__ = "keyword_rankings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, nullable=False)
    keyword = Column(String, nullable=False)
    position = Column(Integer, nullable=True)
    search_volume = Column(Integer, default=0)
    competition = Column(String, default="unknown")
    cpc = Column(Float, default=0.0)
    market = Column(String, default="us")
    tracked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Article(Base):
    __tablename__ = "articles"
    id = Column(String, primary_key=True)
    project_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, default="")
    content_hash = Column(String, nullable=False)
    primary_keyword = Column(String, default="")
    secondary_keywords = Column(Text, default="[]")
    word_count = Column(Integer, default=0)
    seo_score = Column(Integer, default=0)
    status = Column(String, default="draft")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)


class StepLog(Base):
    __tablename__ = "step_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    step_type = Column(String, nullable=False)
    tool_name = Column(String, nullable=True)
    input_summary = Column(Text, default="")
    output_summary = Column(Text, default="")
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    success = Column(Integer, default=1)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(String, primary_key=True, default="default")
    preferred_tone = Column(String, default="professional")
    target_audience = Column(String, default="general")
    language = Column(String, default="en")
    taboo_topics = Column(Text, default="[]")
    style_preferences = Column(Text, default="{}")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


# ── KB File Registry (merged from file_registry.py) ─────

class KBFile(Base):
    __tablename__ = "kb_files"
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=False, unique=True, index=True)
    file_type = Column(String, nullable=False, default="unknown")
    file_size_bytes = Column(Integer, default=0)
    source = Column(String, nullable=False, default="user_upload")
    tags = Column(Text, default="[]")
    chunk_count = Column(Integer, default=0)
    ingested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_accessed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    project_id = Column(String, nullable=False, default="default")


# ── Engine singleton ────────────────────────────────────

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        db_path = settings.db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        _engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )

        @event.listens_for(_engine, "connect")
        def _set_wal(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


_initialized = False


def init_db():
    """Create all tables. Idempotent — only runs once per process."""
    global _initialized
    if _initialized:
        return
    engine = _get_engine()
    Base.metadata.create_all(engine)
    _initialized = True


def get_session() -> Session:
    return Session(_get_engine())
