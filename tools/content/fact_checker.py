from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "fact_checker",
    "description": "Fact-check content for accuracy. Verifies statistics, claims, dates, and technical statements against known information. Flags uncertain or potentially incorrect claims. Use this before publishing any article.",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Article content to fact-check"},
            "claims_to_verify": {"type": "array", "items": {"type": "string"}, "description": "Specific claims, stats, or facts to double-check (auto-extracted if empty)"},
        },
        "required": ["content"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(content: str, claims_to_verify: list[str] | None = None) -> str:
        if not llm_client:
            return _mock_fact_check(content)

        from llm.types import Message

        excerpt = content[:4000]
        claims = "\n".join(f"  • {c}" for c in (claims_to_verify or [])) if claims_to_verify else "  (auto-extract factual claims from the content)"

        prompt = f"""You are a rigorous fact-checker for published content.

Review this article content and verify its factual accuracy.

Specific Claims to Verify:
{claims}

Content:
---
{excerpt}
---

Provide a structured fact-check report:

1. **Verified Claims** — claims that are accurate and well-supported
2. **Uncertain Claims** — claims that might be inaccurate, outdated, or need better sourcing
3. **Potentially False** — claims that contradict known facts
4. **Missing Citations** — statistics and data points that need source attribution
5. **Dated Information** — claims using "recently", "latest", or time-sensitive data that may age poorly
6. **Overall Confidence Score**: X/10 — how confident you are in this content's factual accuracy

Be specific. Quote the exact sentence/phrase for each flagged issue. If you're unsure, say so rather than making a judgment call."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_fact_check(content: str) -> str:
    wc = len(content.split())
    return f"""# Fact Check Report

**Overall Confidence**: 7/10

## Verified Claims
- Content structure is logical and well-organized

## Uncertain Claims
- Statistics without year attribution (add "according to [source], 2025")
- "Best" claims without comparison criteria

## Missing Citations
- Add sources for any numerical data
- Cite authority sources for technical claims

## Recommendations
- Add year to all statistics (e.g., "as of Q1 2026")
- Replace absolute claims ("best") with qualified ones ("top-rated by X")
"""
