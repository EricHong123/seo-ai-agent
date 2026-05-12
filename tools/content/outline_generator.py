from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "outline_generator",
    "description": "Generate a detailed SEO-optimized content outline. Takes keyword research + SERP analysis + competitor data and produces a structured outline with H2/H3 headings, target word counts per section, and keyword placement recommendations.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Article topic / target keyword"},
            "serp_insights": {"type": "string", "description": "Key findings from SERP analysis (heading patterns, word counts, content types ranking)"},
            "competitor_insights": {"type": "string", "description": "Key findings from competitor audit (gaps, strengths, angle opportunities)"},
            "target_keywords": {"type": "array", "items": {"type": "string"}, "description": "Primary + secondary keywords to target"},
            "target_length": {"type": "string", "description": "Target word count, e.g., '2500 words'"},
            "content_angle": {"type": "string", "description": "Unique angle or hook to differentiate from competitors"},
        },
        "required": ["topic", "target_keywords"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(
        topic: str,
        target_keywords: list[str],
        serp_insights: str = "",
        competitor_insights: str = "",
        target_length: str = "2000-2500 words",
        content_angle: str = "",
    ) -> str:
        if not llm_client:
            return _mock_outline(topic, target_keywords)

        from llm.types import Message

        angle = f"\nUnique Angle: {content_angle}" if content_angle else ""
        serp = f"\nSERP Insights:\n{serp_insights}" if serp_insights else ""
        comp = f"\nCompetitor Insights:\n{competitor_insights}" if competitor_insights else ""

        prompt = f"""You are an expert SEO content strategist.

Create a detailed content outline for:
Topic: {topic}
Target Keywords: {', '.join(target_keywords)}
Target Length: {target_length}{angle}{serp}{comp}

Output a structured outline with:

1. **Title** — SEO-optimized, includes primary keyword, compelling hook
2. **Meta Description** — 150-160 chars, includes primary keyword + value proposition
3. **URL Slug** — clean, keyword-rich
4. **H2 Sections** (5-8 sections) — each with:
   - Target word count
   - Primary/secondary keywords to use
   - Key points to cover
   - Internal linking opportunities
5. **H3 Sub-sections** under key H2s
6. **FAQ Section** — 3-5 questions targeting PAA/featured snippet opportunities
7. **CTA** — natural call-to-action aligned with search intent
8. **Differentiation Notes** — how this outline beats the current top-ranking content

Format as a clean, actionable outline ready for a writer to execute."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_outline(topic: str, keywords: list[str]) -> str:
    return f"""# Content Outline: {topic}

**Title**: {topic}: The Complete 2026 Guide
**Meta**: Everything you need to know about {topic} in 2026. Expert advice, comparisons, and recommendations.

## H2: What Is {topic}? (200 words)
- Keywords: {keywords[0] if keywords else topic}, {topic} explained
- Define the topic clearly for beginners

## H2: Top 5 {topic} Picks for 2026 (500 words)
- Keywords: best {topic}, {topic} reviews
- Comparison table recommended

## H2: How to Choose the Right {topic} (300 words)
- Keywords: how to choose {topic}, {topic} buying guide

## H2: {topic} vs Alternatives (300 words)
- Keywords: {topic} vs, {topic} alternatives

## H2: Expert Tips (200 words)

## H2: FAQ (200 words)

**Total Target**: ~2,200 words"""
