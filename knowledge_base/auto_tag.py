TAG_PROMPT = """Analyze this document and return tags as a JSON array of strings.
Choose from: brand_guide, competitor_analysis, keyword_report, article, style_guide,
industry_report, technical_doc, marketing, legal, other.
Also include: language (en/zh), year if applicable, document format description.

Document excerpt:
{excerpt}

Return ONLY a valid JSON array like: ["brand_guide", "zh", "tone-of-voice", "2026"]"""


async def auto_tag(text: str, llm_client=None) -> list[str]:
    excerpt = text[:2000]
    if llm_client:
        from llm.types import Message
        import json as _json
        response = await llm_client.chat(
            messages=[Message(role="user", content=TAG_PROMPT.format(excerpt=excerpt))],
        )
        try:
            return _json.loads(response.content.strip())
        except (_json.JSONDecodeError, ValueError):
            pass
    return _rule_based_tags(text)


def _rule_based_tags(text: str) -> list[str]:
    tags: list[str] = []
    t = text.lower()

    zh_chars = sum(1 for c in text if "一" <= c <= "鿿")
    tags.append("zh" if zh_chars > len(text) * 0.3 else "en")

    if any(kw in t for kw in ["brand", "tone of voice", "品牌", "语气"]):
        tags.append("brand_guide")
    if any(kw in t for kw in ["competitor", "竞品", "对手"]):
        tags.append("competitor_analysis")
    if any(kw in t for kw in ["keyword", "search volume", "关键词"]):
        tags.append("keyword_report")
    if any(kw in t for kw in ["article", "blog", "文章", "博客"]):
        tags.append("article")
    if any(kw in t for kw in ["style guide", "design", "配色", "字体"]):
        tags.append("style_guide")

    return tags or ["other"]
