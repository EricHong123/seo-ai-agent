from fastapi import APIRouter

from memory.structured.keyword_memory import get_all_keywords, get_keyword_history
from memory.structured.step_memory import get_token_usage, get_recent_steps

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/keywords")
async def keywords(project_id: str = "default"):
    return await get_all_keywords(project_id)


@router.get("/keywords/{keyword}/history")
async def keyword_history(keyword: str, project_id: str = "default"):
    return await get_keyword_history(project_id, keyword)


@router.get("/usage")
async def token_usage(project_id: str = "default"):
    return await get_token_usage(project_id)


@router.get("/steps")
async def recent_steps(project_id: str = "default", limit: int = 20):
    return await get_recent_steps(project_id, limit)
