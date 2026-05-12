from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "serp_analyzer",
    "description": "Analyze the current Search Engine Results Page (SERP) for a given keyword. Returns top-ranking pages, their structure, featured snippets, People Also Ask questions, and ranking insights.",
    "parameters": {
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "Target keyword to analyze SERP for"},
            "market": {"type": "string", "enum": ["us", "cn"], "description": "Search market", "default": "us"},
        },
        "required": ["keyword"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(keyword: str, market: str = "us") -> str:
        if not llm_client:
            return _mock_serp_report(keyword, market)

        from llm.types import Message

        prompt = f"""You are an SEO SERP analysis expert.

Analyze the SERP for the keyword "{keyword}" in the {market} market.

Provide a detailed analysis including:

1. **Top 5 ranking pages** — title, URL pattern (domain style, not real URLs), content type (blog post/listicle/guide/product page)
2. **Featured snippet** — what format (paragraph/list/table), what content appears
3. **People Also Ask** — 5-8 real PAA questions for this keyword
4. **SERP features** — images, videos, knowledge panel, local pack, shopping
5. **Content gap opportunities** — what the top pages are missing, what angle you could take
6. **Average word count** of top-ranking content

Be realistic and specific. Base your analysis on what would actually appear for this keyword."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_serp_report(keyword: str, market: str) -> str:
    return f"""# SERP Analysis: "{keyword}" ({market.upper()})

## Top 5 Ranking Pages
1. **"{keyword}: The Complete Guide"** — /blog/complete-guide (Guide, 3,200 words)
2. **"Best {keyword} 2026"** — /best/2026 (Listicle, 2,800 words)
3. **"{keyword} Review"** — /review (Review, 1,900 words)
4. **"How to Choose {keyword}"** — /how-to (How-to, 2,400 words)
5. **"{keyword} on Wikipedia"** — wiki (Encyclopedia, 4,500 words)

## Featured Snippet
Paragraph type: "{keyword} is a ..."

## People Also Ask
- What is {keyword}?
- How much does {keyword} cost?
- Is {keyword} worth it?
- {keyword} vs alternatives?

## Content Gap
- No comparison data or test results in top results
- Missing beginner's guide angle
- Low image/video integration in top 3"""
