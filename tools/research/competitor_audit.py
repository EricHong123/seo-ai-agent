from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "competitor_audit",
    "description": "Audit competitor content for a given keyword or topic. Analyzes competitor page structure, headings, keywords used, and content strategy. Use the competitor URLs you found from serp_analyzer.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "The topic or keyword to audit competitors for"},
            "competitor_urls": {"type": "array", "items": {"type": "string"}, "description": "List of competitor URLs to audit (from SERP analysis)"},
            "depth": {"type": "string", "enum": ["quick", "detailed"], "description": "Analysis depth", "default": "detailed"},
        },
        "required": ["topic"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(topic: str, competitor_urls: list[str] | None = None, depth: str = "detailed") -> str:
        if not llm_client:
            return _mock_competitor_report(topic, competitor_urls or [])

        from llm.types import Message

        urls_str = "\n".join(f"  • {u}" for u in (competitor_urls or [])) if competitor_urls else "  (analyze typical competitors for this topic)"

        prompt = f"""You are a competitive content analyst specializing in SEO.

Topic: "{topic}"
Competitor URLs:
{urls_str}
Depth: {depth}

Provide a detailed competitive audit:

1. **Content structure comparison** — how each competitor structures their page (H1, H2s, H3s pattern)
2. **Keyword usage** — primary/secondary keywords, keyword density patterns
3. **Content gaps** — what they COVER and what they MISS
4. **Content quality metrics** — readability, uniqueness, data/statistics usage, multimedia
5. **Backlink profile indicators** — what type of content attracts links in this niche
6. **Your competitive advantage** — specific recommendations to outrank them

Be tactical. Give actionable recommendations, not generic advice."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_competitor_report(topic: str, urls: list[str]) -> str:
    return f"""# Competitive Audit: "{topic}"

## Content Structure
Competitors follow a similar pattern:
- H1: "{topic}" or "Best {topic} 2026"
- H2s: Features, Benefits, Top Picks, FAQ
- Missing: comparison data, expert opinions, original research

## Keyword Gaps
Covered: {topic}, best {topic}, {topic} guide
Missing: {topic} for beginners, {topic} vs alternatives, {topic} under $100

## Recommendations
1. Include original comparison data (table/chart)
2. Add expert quotes or real user testimonials
3. Create a dedicated FAQ section targeting PAA questions
4. Target 3,000+ words with original research angle"""
