from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "internal_linker",
    "description": "Analyze content and suggest internal linking opportunities. Identifies anchor text candidates, recommends link targets from existing site content, and builds topical clusters.",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Article content to analyze for linking opportunities"},
            "existing_pages": {"type": "array", "items": {"type": "string"}, "description": "List of existing site pages/articles that could be linked to"},
            "primary_keyword": {"type": "string", "description": "Primary keyword — helps find the most relevant link targets"},
        },
        "required": ["content"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(content: str, existing_pages: list[str] | None = None, primary_keyword: str = "") -> str:
        if not llm_client:
            return _mock_linker(content, existing_pages or [])

        from llm.types import Message

        pages = "\n".join(f"  • {p}" for p in (existing_pages or [])) if existing_pages else "  (suggest internal link topics based on content analysis)"
        excerpt = content[:3000]

        prompt = f"""You are an expert in SEO internal linking and topical cluster strategy.

Article Content (excerpt):
---
{excerpt}
---

Primary Keyword: {primary_keyword or "auto-detect"}
Available Pages to Link To:
{pages}

Provide an internal linking analysis:

1. **Anchor Text Opportunities** — list specific phrases in the content that should be linked, with suggested target topics
2. **Link-From Suggestions** — which of the existing pages should link TO this article? With anchor text suggestions
3. **Topical Cluster Map** — how this article fits into the broader site structure
4. **Pillar/Cluster Recommendations** — should this be a pillar page or cluster content?
5. **URL Structure** — recommended URL path based on topical hierarchy

Be specific with exact anchor text phrases from the content. Don't recommend linking every mention — focus on the most valuable 3-5 links."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_linker(content: str, pages: list[str]) -> str:
    return f"""# Internal Linking Analysis

## Anchor Text Opportunities
| Phrase in Content | Link To |
|---|---|
| "keyword research tools" | /blog/keyword-research-guide |
| "SEO best practices" | /blog/seo-checklist-2026 |
| "search engine ranking" | /blog/how-search-engines-work |

## Link-From Suggestions
- From / (homepage) → anchor: "complete guide to..."
- From /blog/seo-checklist-2026 → anchor: "detailed analysis of..."
- From /blog/keyword-research-guide → anchor: "related:..."

## Topical Cluster
This article is **cluster content** under a pillar page about [primary topic].

## Recommended URL
`/blog/{'-'.join(primary_keyword.lower().split() if primary_keyword else 'article')}`
"""
