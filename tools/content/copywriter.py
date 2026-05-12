from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "copywriter",
    "description": "Write SEO-optimized content. Can write full articles, individual sections, or rewrite existing text. Parameters control tone, target audience, and keyword placement.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Article topic or section heading"},
            "keywords": {"type": "array", "items": {"type": "string"}, "description": "Primary and secondary keywords to include"},
            "outline": {"type": "string", "description": "Content outline or structure to follow"},
            "tone": {"type": "string", "enum": ["professional", "conversational", "authoritative", "beginner-friendly"], "description": "Writing tone"},
            "target_audience": {"type": "string", "description": "Who this is written for (e.g., 'beginner developers', 'small business owners')"},
            "target_length": {"type": "string", "description": "Target word count, e.g., '2000 words' or '500-800 words'"},
            "brand_context": {"type": "string", "description": "Brand guidelines or voice notes from KB (injected automatically if available)"},
        },
        "required": ["topic", "keywords"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(
        topic: str,
        keywords: list[str],
        outline: str = "",
        tone: str = "professional",
        target_audience: str = "general readers",
        target_length: str = "1000-1500 words",
        brand_context: str = "",
    ) -> str:
        if not llm_client:
            return _mock_copy(topic, keywords, tone)

        from llm.types import Message

        brand_section = f"\n\nBrand Voice & Guidelines:\n{brand_context}" if brand_context else ""
        outline_section = f"\n\nContent Outline:\n{outline}" if outline else ""

        prompt = f"""You are a professional SEO content writer.

Write SEO-optimized content for:
- Topic: {topic}
- Keywords: {', '.join(keywords)}
- Tone: {tone}
- Target Audience: {target_audience}
- Target Length: {target_length}{outline_section}{brand_section}

Requirements:
- Use proper heading hierarchy (H2, H3)
- Naturally incorporate keywords without stuffing
- Include an engaging introduction hook
- Use short paragraphs for readability
- End with a clear conclusion and CTA if appropriate
- Use data/stats where possible (cite sources)
- Include internal linking opportunities (note as [link: topic])

Write the complete content ready to publish. Quality over speed — make it genuinely useful."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_copy(topic: str, keywords: list[str], tone: str) -> str:
    return f"""# {topic}

> A comprehensive guide for anyone looking to understand {topic.lower()}.

## Introduction

Finding the right information about {topic.lower()} can be overwhelming. That's why we've put together this complete guide.

## What You'll Learn
- What {topic} is and why it matters
- Key factors to consider when choosing
- Expert recommendations for 2026

[Content continues...]

*This is a placeholder. Connect an LLM for full content generation.*"""
