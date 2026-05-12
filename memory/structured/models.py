import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Session, relationship

from config.settings import settings


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    target_audience = Column(String, default="")
    brand_voice = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class KeywordRanking(Base):
    __tablename__ = "keyword_rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, nullable=False)
    keyword = Column(String, nullable=False)
    position = Column(Integer, nullable=True)
    search_volume = Column(Integer, default=0)
    competition = Column(String, default="unknown")  # low/medium/high
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
    secondary_keywords = Column(Text, default="[]")  # JSON array
    word_count = Column(Integer, default=0)
    seo_score = Column(Integer, default=0)
    status = Column(String, default="draft")  # draft/published/archived
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)


class StepLog(Base):
    __tablename__ = "step_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, nullable=False)
    task_id = Column(String, nullable=False)
    step_type = Column(String, nullable=False)  # tool_call / reasoning / kb_search / kb_ingest
    tool_name = Column(String, nullable=True)
    input_summary = Column(Text, default="")
    output_summary = Column(Text, default="")
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    success = Column(Integer, default=1)  # 1 = success, 0 = error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, default="default")
    preferred_tone = Column(String, default="professional")  # professional/conversational/authoritative
    target_audience = Column(String, default="general")
    language = Column(String, default="en")  # en/zh
    taboo_topics = Column(Text, default="[]")  # JSON array
    style_preferences = Column(Text, default="{}")  # JSON object
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


def init_db():
    engine = create_engine(settings.db_url.replace("+aiosqlite", ""))
    Base.metadata.create_all(engine)
    return engine


def get_session() -> Session:
    engine = create_engine(settings.db_url.replace("+aiosqlite", ""))
    return Session(engine)
