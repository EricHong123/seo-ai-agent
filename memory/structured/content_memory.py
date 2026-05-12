import hashlib
import json
from datetime import datetime, timezone

from memory.structured.models import Article, get_session


async def save_article(
    article_id: str,
    project_id: str,
    title: str,
    content: str,
    primary_keyword: str = "",
    secondary_keywords: list[str] | None = None,
    word_count: int = 0,
    seo_score: int = 0,
    status: str = "draft",
) -> str:
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    session = get_session()

    existing = session.query(Article).filter_by(content_hash=content_hash).first()
    if existing:
        session.close()
        return existing.id

    article = Article(
        id=article_id,
        project_id=project_id,
        title=title,
        content=content,
        content_hash=content_hash,
        primary_keyword=primary_keyword,
        secondary_keywords=json.dumps(secondary_keywords or []),
        word_count=word_count or len(content.split()),
        seo_score=seo_score,
        status=status,
        created_at=datetime.now(timezone.utc),
    )
    session.add(article)
    session.commit()
    article_id = article.id
    session.close()
    return article_id


async def get_articles_by_keyword(project_id: str, keyword: str, limit: int = 5) -> list[dict]:
    session = get_session()
    rows = (
        session.query(Article)
        .filter(
            Article.project_id == project_id,
            (Article.primary_keyword.contains(keyword)) |
            (Article.title.contains(keyword)),
        )
        .order_by(Article.created_at.desc())
        .limit(limit)
        .all()
    )
    result = [
        {
            "id": r.id,
            "title": r.title,
            "primary_keyword": r.primary_keyword,
            "word_count": r.word_count,
            "seo_score": r.seo_score,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    session.close()
    return result


async def get_recent_articles(project_id: str, limit: int = 10) -> list[dict]:
    session = get_session()
    rows = (
        session.query(Article)
        .filter_by(project_id=project_id)
        .order_by(Article.created_at.desc())
        .limit(limit)
        .all()
    )
    result = [
        {
            "id": r.id,
            "title": r.title,
            "primary_keyword": r.primary_keyword,
            "status": r.status,
        }
        for r in rows
    ]
    session.close()
    return result
