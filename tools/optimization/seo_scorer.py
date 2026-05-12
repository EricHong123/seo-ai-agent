from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "seo_scorer",
    "description": "Score and audit SEO quality of content. Checks title tags, meta description, heading structure, keyword density, readability, internal links, and provides optimization recommendations.",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The full article/content to analyze"},
            "target_keyword": {"type": "string", "description": "Primary target keyword"},
            "secondary_keywords": {"type": "array", "items": {"type": "string"}, "description": "Secondary keywords to check for"},
        },
        "required": ["content", "target_keyword"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(content: str, target_keyword: str, secondary_keywords: list[str] | None = None) -> str:
        if not llm_client:
            return _mock_seo_score(content, target_keyword)

        from llm.types import Message

        sec = ", ".join(secondary_keywords) if secondary_keywords else "none specified"
        excerpt = content[:4000]

        prompt = f"""You are an SEO quality auditor. Score the following content out of 100.

Target Keyword: "{target_keyword}"
Secondary Keywords: {sec}

Content (first 4000 chars):
---
{excerpt}
---

Provide a structured SEO audit:

1. **Overall Score**: X/100
2. **Title Tag**: Score & feedback (is target keyword present? compelling?)
3. **Meta Description**: (if present) Score & feedback
4. **Heading Structure**: H1/H2/H3 usage, keyword placement in headings
5. **Keyword Density**: Primary keyword % and secondary keyword coverage
6. **Readability**: Grade level, paragraph length, sentence variety
7. **Content Depth**: Does it adequately cover the topic? Missing subtopics?
8. **Internal/External Links**: Are there linking opportunities?
9. **Top 3 Priority Fixes**: Most impactful improvements ranked

Be specific and actionable. Don't be afraid to give low scores for real issues."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_seo_score(content: str, target_keyword: str) -> str:
    kw_count = content.lower().count(target_keyword.lower())
    word_count = len(content.split())
    density = (kw_count / max(word_count, 1)) * 100

    return f"""# SEO Score: {target_keyword}

**Overall**: 72/100

| Factor | Score | Notes |
|--------|-------|-------|
| Title Tag | 8/10 | Keyword present |
| Meta Description | - | Not found in content |
| Heading Structure | 7/10 | H1 + 3 H2s found |
| Keyword Density | {min(int(density*10), 10)}/10 | {density:.1f}% density |
| Readability | 7/10 | Grade 9 level |

**Top 3 Priority Fixes**:
1. Add a meta description (150-160 chars) with primary keyword
2. Increase keyword density to 1-2% (currently {density:.1f}%)
3. Add 2-3 H3 subheadings under each H2"""
