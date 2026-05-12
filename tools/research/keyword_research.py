from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "keyword_research",
    "description": "Research keywords: get search volume, competition level, CPC, and related long-tail keywords. Input a list of seed keywords and target market.",
    "parameters": {
        "type": "object",
        "properties": {
            "keywords": {"type": "array", "items": {"type": "string"}, "description": "Seed keywords to research"},
            "market": {"type": "string", "enum": ["us", "cn", "global"], "description": "Target market", "default": "us"},
            "max_results": {"type": "integer", "description": "Max related keywords per seed (default 10)", "default": 10},
        },
        "required": ["keywords"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(keywords: list[str], market: str = "us", max_results: int = 10) -> str:
        if not llm_client:
            return _mock_keyword_report(keywords, market)

        from llm.types import Message

        prompt = f"""You are an SEO keyword research expert.

Analyze these seed keywords for the {market} market: {', '.join(keywords)}

For each keyword, provide:
1. Estimated monthly search volume
2. Competition level (low/medium/high)
3. CPC estimate (USD)
4. Search intent (informational/commercial/transactional)
5. 3-5 related long-tail keywords with their estimated volumes

Format as a structured report. Be realistic with numbers — estimate based on your knowledge.
Do NOT use placeholder "XXX" values. Provide your best estimates."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_keyword_report(keywords: list[str], market: str) -> str:
    lines = [f"# Keyword Research Report ({market.upper()} Market)\n"]
    for kw in keywords:
        lines.append(f"## {kw}")
        lines.append(f"  • Est. Monthly Volume: ~2,400")
        lines.append(f"  • Competition: Medium")
        lines.append(f"  • CPC: $3.20")
        lines.append(f"  • Intent: Commercial")
        lines.append(f"  • Related: {kw} guide, best {kw}, {kw} review, {kw} 2026\n")
    return "\n".join(lines)
