"""MCP Resources: expose SEO data as readable context for the LLM."""

from knowledge_base.kb_manager import KnowledgeBase
from memory.structured.keyword_memory import get_all_keywords, get_keyword_history
from memory.structured.content_memory import get_recent_articles
from memory.user_profile import get_profile


async def get_kb_overview(project_id: str = "default") -> str:
    kb = KnowledgeBase()
    records = await kb.list_files(project_id)
    if not records:
        return "Knowledge base is empty."

    lines = [f"# Knowledge Base ({len(records)} documents)\n"]
    for r in records:
        lines.append(f"- **{r['filename']}** ({r['file_type']}, {r['chunk_count']} chunks)")
        lines.append(f"  Tags: {r.get('tags', '[]')}")
        lines.append(f"  Ingested: {r.get('ingested_at', '')[:19]}")
    return "\n".join(lines)


async def get_keyword_overview(project_id: str = "default") -> str:
    keywords = await get_all_keywords(project_id)
    if not keywords:
        return "No tracked keywords."

    lines = [f"# Tracked Keywords ({len(keywords)})\n"]
    lines.append("| Keyword | Volume | Position |")
    lines.append("|---------|--------|----------|")
    for kw in keywords[:20]:
        lines.append(f"| {kw['keyword']} | {kw.get('volume', '-')} | {kw.get('position', '-')} |")
    return "\n".join(lines)


async def get_article_overview(project_id: str = "default") -> str:
    articles = await get_recent_articles(project_id)
    if not articles:
        return "No articles written yet."

    lines = [f"# Recent Articles ({len(articles)})\n"]
    for a in articles:
        lines.append(f"- **{a['title']}** ({a['status']}) — keyword: {a.get('primary_keyword', '')}")
    return "\n".join(lines)


async def get_user_profile_resource(user_id: str = "default") -> str:
    profile = await get_profile(user_id)
    lines = ["# User Profile\n"]
    lines.append(f"- Tone: {profile['preferred_tone']}")
    lines.append(f"- Audience: {profile['target_audience']}")
    lines.append(f"- Language: {profile['language']}")
    lines.append(f"- Taboo Topics: {', '.join(profile['taboo_topics']) or 'none'}")
    return "\n".join(lines)


MCP_RESOURCES = {
    "kb://overview": get_kb_overview,
    "seo://keywords": get_keyword_overview,
    "seo://articles": get_article_overview,
    "user://profile": get_user_profile_resource,
}
