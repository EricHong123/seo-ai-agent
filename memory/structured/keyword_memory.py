from datetime import datetime, timezone

from memory.structured.models import KeywordRanking, get_session


async def save_keyword(
    project_id: str,
    keyword: str,
    position: int | None = None,
    search_volume: int = 0,
    competition: str = "unknown",
    cpc: float = 0.0,
    market: str = "us",
):
    session = get_session()
    record = KeywordRanking(
        project_id=project_id,
        keyword=keyword,
        position=position,
        search_volume=search_volume,
        competition=competition,
        cpc=cpc,
        market=market,
        tracked_at=datetime.now(timezone.utc),
    )
    session.add(record)
    session.commit()
    session.close()


async def get_keyword_history(project_id: str, keyword: str, limit: int = 10) -> list[dict]:
    session = get_session()
    rows = (
        session.query(KeywordRanking)
        .filter_by(project_id=project_id, keyword=keyword)
        .order_by(KeywordRanking.tracked_at.desc())
        .limit(limit)
        .all()
    )
    result = [
        {
            "position": r.position,
            "search_volume": r.search_volume,
            "tracked_at": r.tracked_at.isoformat() if r.tracked_at else None,
        }
        for r in rows
    ]
    session.close()
    return result


async def get_all_keywords(project_id: str) -> list[dict]:
    session = get_session()
    rows = (
        session.query(KeywordRanking)
        .filter_by(project_id=project_id)
        .order_by(KeywordRanking.tracked_at.desc())
        .all()
    )
    seen = set()
    result = []
    for r in rows:
        if r.keyword not in seen:
            seen.add(r.keyword)
            result.append({"keyword": r.keyword, "volume": r.search_volume, "position": r.position})
    session.close()
    return result
