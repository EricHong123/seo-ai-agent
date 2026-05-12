from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class TaskRequest(BaseModel):
    task: str = Field(..., description="Task description in natural language")
    project_id: str = Field("default")
    user_id: str = Field("default")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: str | None = None
    error: str | None = None


class ArticleCreate(BaseModel):
    title: str
    content: str
    primary_keyword: str = ""
    secondary_keywords: list[str] = Field(default_factory=list)
    project_id: str = "default"


class ArticleResponse(BaseModel):
    id: str
    title: str
    primary_keyword: str
    status: str
    word_count: int
    seo_score: int
    created_at: str | None = None


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    target_audience: str = ""
    brand_voice: str = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str | None = None


class KBFileUpload(BaseModel):
    path: str = Field(..., description="File path or URL to ingest")
    project_id: str = "default"


class KBFileResponse(BaseModel):
    file_id: str
    filename: str
    status: str
    chunk_count: int
    tags: list[str]


class KBListResponse(BaseModel):
    files: list[dict]


class KBDeleteRequest(BaseModel):
    filename: str
    project_id: str = "default"


class UserProfileUpdate(BaseModel):
    preferred_tone: str | None = None
    target_audience: str | None = None
    language: str | None = None
    taboo_topics: list[str] | None = None
    style_preferences: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    tools_count: int
