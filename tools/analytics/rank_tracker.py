from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "rank_tracker",
    "description": "Track keyword rankings over time. Compare current positions against historical data to identify trends, gains, and losses. Can also check a keyword's current position by estimating from SERP knowledge.",
    "parameters": {
        "type": "object",
        "properties": {
            "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords to check rankings for"},
            "market": {"type": "string", "enum": ["us", "cn", "uk", "au"], "description": "Target market", "default": "us"},
            "compare_previous": {"type": "boolean", "description": "Compare with previous position data from memory", "default": True},
        },
        "required": ["keywords"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(keywords: list[str], market: str = "us", compare_previous: bool = True) -> str:
        if not llm_client:
            return _mock_rank_report(keywords, market)

        from llm.types import Message

        kw_list = "\n".join(f"  • {kw}" for kw in keywords)

        prompt = f"""You are an SEO rank tracking specialist.

Keywords to Track ({market.upper()} market):
{kw_list}

Compare with previous data: {"Yes" if compare_previous else "No"}

Provide a rank tracking report:

1. For each keyword, estimate:
   - Current estimated position (1-100)
   - Change from previous period (↑/↓/→) with estimated position delta
   - URL that is ranking (pattern, not real URL)
   - SERP feature occupying (featured snippet, video, local pack, etc.)

2. **Summary Statistics**:
   - Keywords in top 3 / top 10 / top 50
   - Average position change
   - Biggest winner (most improved keyword)
   - Biggest loser (most declined keyword)

3. **Opportunities**:
   - Keywords ranking #4-15 (striking distance)
   - New keywords appearing (not tracked before)

Use realistic estimates based on your knowledge of the SEO landscape. Mark clearly which numbers are estimates based on typical patterns vs. would require actual GSC API access."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_rank_report(keywords: list[str], market: str) -> str:
    lines = [f"# Rank Tracking Report ({market.upper()})\n"]
    lines.append("| Keyword | Position | Change | URL Pattern |")
    lines.append("|---------|----------|--------|-------------|")

    positions = [3, 7, 12, 22, 8, 15]
    for i, kw in enumerate(keywords):
        pos = positions[i % len(positions)]
        change = ["↑2", "↓1", "→", "↑5", "↓3", "new"][i % 6]
        lines.append(f"| {kw} | #{pos} | {change} | /blog/{kw.replace(' ', '-').lower()} |")

    lines.append(f"\n## Summary")
    lines.append(f"  • Top 3: 1 keyword")
    lines.append(f"  • Top 10: 3 keywords")
    lines.append(f"  • Striking distance (#4-15): 2 keywords")
    return "\n".join(lines)
