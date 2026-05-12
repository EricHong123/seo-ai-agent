import uuid
from fastapi import APIRouter, HTTPException

from interfaces.api.schemas import ArticleCreate, ArticleResponse
from memory.structured.content_memory import save_article, get_recent_articles, get_articles_by_keyword

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("", response_model=ArticleResponse)
async def create_article(body: ArticleCreate):
    article_id = str(uuid.uuid4())[:8]
    art_id = await save_article(
        article_id=article_id,
        project_id=body.project_id,
        title=body.title,
        content=body.content,
        primary_keyword=body.primary_keyword,
        secondary_keywords=body.secondary_keywords,
        word_count=len(body.content.split()),
    )
    return ArticleResponse(
        id=art_id,
        title=body.title,
        primary_keyword=body.primary_keyword,
        status="draft",
        word_count=len(body.content.split()),
        seo_score=0,
    )


@router.get("", response_model=list[ArticleResponse])
async def list_articles(project_id: str = "default", keyword: str | None = None):
    if keyword:
        articles = await get_articles_by_keyword(project_id, keyword)
    else:
        articles = await get_recent_articles(project_id)
    return [
        ArticleResponse(
            id=a["id"],
            title=a["title"],
            primary_keyword=a.get("primary_keyword", ""),
            status=a.get("status", "draft"),
            word_count=a.get("word_count", 0),
            seo_score=a.get("seo_score", 0),
            created_at=a.get("created_at"),
        )
        for a in articles
    ]
