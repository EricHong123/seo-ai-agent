"""FastMCP Server for SEO AI Agent.

Usage:
    python mcp_server/server.py
    # Or via fastmcp:
    fastmcp run mcp_server/server.py

Integrates with Claude Code, VS Code, Cursor, and any MCP-compatible editor.
"""

import json
import asyncio
from fastmcp import FastMCP

from config.settings import settings
from mcp_server.prompts import MCP_PROMPTS

mcp = FastMCP(settings.mcp_server_name)

# Lazy-initialized agent
_agent = None


async def _get_agent():
    global _agent
    if _agent is None:
        from agent.orchestrator import SEOAgent
        _agent = SEOAgent()
        await _agent._init()
    return _agent


# ---- Tools: dynamically registered from agent registry ----

@mcp.tool(name="kb_search", description="Search your knowledge base for relevant documents, brand guides, competitor analyses, or historical articles.")
async def kb_search(query: str, top_k: int = 5, filter_type: str = "all") -> str:
    agent = await _get_agent()
    return await agent.registry.execute("kb_search", {"query": query, "top_k": top_k, "filter_type": filter_type})


@mcp.tool(name="kb_ingest", description="Store important information into your knowledge base.")
async def kb_ingest(content: str, filename: str, source: str = "manual") -> str:
    agent = await _get_agent()
    return await agent.registry.execute("kb_ingest", {"content": content, "filename": filename, "source": source})


@mcp.tool(name="kb_list", description="List all documents currently stored in your knowledge base.")
async def kb_list() -> str:
    agent = await _get_agent()
    return await agent.registry.execute("kb_list", {})


@mcp.tool(name="kb_delete", description="Delete a document from your knowledge base.")
async def kb_delete(filename: str) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("kb_delete", {"filename": filename})


@mcp.tool(name="keyword_research", description="Research keywords: get search volume, competition level, CPC, and related long-tail keywords.")
async def keyword_research(keywords: list[str], market: str = "us", max_results: int = 10) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("keyword_research", {"keywords": keywords, "market": market, "max_results": max_results})


@mcp.tool(name="serp_analyzer", description="Analyze the current SERP for a given keyword. Returns top-ranking pages, structure, featured snippets, PAA.")
async def serp_analyzer(keyword: str, market: str = "us") -> str:
    agent = await _get_agent()
    return await agent.registry.execute("serp_analyzer", {"keyword": keyword, "market": market})


@mcp.tool(name="competitor_audit", description="Audit competitor content for a given keyword or topic.")
async def competitor_audit(topic: str, competitor_urls: list[str] | None = None, depth: str = "detailed") -> str:
    agent = await _get_agent()
    return await agent.registry.execute("competitor_audit", {"topic": topic, "competitor_urls": competitor_urls, "depth": depth})


@mcp.tool(name="copywriter", description="Write SEO-optimized content. Can write full articles, individual sections, or rewrite existing text.")
async def copywriter(
    topic: str,
    keywords: list[str],
    outline: str = "",
    tone: str = "professional",
    target_audience: str = "general readers",
    target_length: str = "1000-1500 words",
    brand_context: str = "",
) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("copywriter", {
        "topic": topic, "keywords": keywords, "outline": outline,
        "tone": tone, "target_audience": target_audience,
        "target_length": target_length, "brand_context": brand_context,
    })


@mcp.tool(name="seo_scorer", description="Score and audit SEO quality of content. Checks titles, headings, keywords, readability, and provides recommendations.")
async def seo_scorer(content: str, target_keyword: str, secondary_keywords: list[str] | None = None) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("seo_scorer", {
        "content": content, "target_keyword": target_keyword,
        "secondary_keywords": secondary_keywords,
    })


@mcp.tool(name="outline_generator", description="Generate a detailed SEO-optimized content outline.")
async def outline_generator(
    topic: str, target_keywords: list[str], serp_insights: str = "",
    competitor_insights: str = "", target_length: str = "2000-2500 words", content_angle: str = "",
) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("outline_generator", {
        "topic": topic, "target_keywords": target_keywords,
        "serp_insights": serp_insights, "competitor_insights": competitor_insights,
        "target_length": target_length, "content_angle": content_angle,
    })


@mcp.tool(name="fact_checker", description="Fact-check content for accuracy. Verifies statistics, claims, dates, and technical statements.")
async def fact_checker(content: str, claims_to_verify: list[str] | None = None) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("fact_checker", {"content": content, "claims_to_verify": claims_to_verify})


@mcp.tool(name="readability", description="Analyze content readability: grade level, sentence variety, passive voice, reading time.")
async def readability(content: str, target_grade: int = 8) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("readability", {"content": content, "target_grade": target_grade})


@mcp.tool(name="internal_linker", description="Analyze content and suggest internal linking opportunities.")
async def internal_linker(content: str, existing_pages: list[str] | None = None, primary_keyword: str = "") -> str:
    agent = await _get_agent()
    return await agent.registry.execute("internal_linker", {
        "content": content, "existing_pages": existing_pages, "primary_keyword": primary_keyword,
    })


@mcp.tool(name="schema_markup", description="Generate Schema.org structured data (JSON-LD) for content.")
async def schema_markup(content_type: str, data: dict) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("schema_markup", {"content_type": content_type, "data": data})


@mcp.tool(name="rank_tracker", description="Track keyword rankings over time with position changes and trend analysis.")
async def rank_tracker(keywords: list[str], market: str = "us", compare_previous: bool = True) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("rank_tracker", {
        "keywords": keywords, "market": market, "compare_previous": compare_previous,
    })


@mcp.tool(name="report_generator", description="Generate SEO performance reports: weekly, monthly, keyword changes, content performance.")
async def report_generator(report_type: str, project_id: str = "default", date_range: str = "last 7 days") -> str:
    agent = await _get_agent()
    return await agent.registry.execute("report_generator", {
        "report_type": report_type, "project_id": project_id, "date_range": date_range,
    })


@mcp.tool(name="web_search", description="Perform web search for real-time information, news, statistics, and references.")
async def web_search(query: str, max_results: int = 5) -> str:
    agent = await _get_agent()
    return await agent.registry.execute("web_search", {"query": query, "max_results": max_results})


# ---- Resources ----

@mcp.resource("kb://overview")
async def kb_overview() -> str:
    from mcp_server.resources import get_kb_overview
    return await get_kb_overview()


@mcp.resource("seo://keywords")
async def keywords_overview() -> str:
    from mcp_server.resources import get_keyword_overview
    return await get_keyword_overview()


@mcp.resource("seo://articles")
async def articles_overview() -> str:
    from mcp_server.resources import get_article_overview
    return await get_article_overview()


@mcp.resource("user://profile")
async def user_profile_resource() -> str:
    from mcp_server.resources import get_user_profile_resource
    return await get_user_profile_resource()


# ---- Prompts ----

for _name, _def in MCP_PROMPTS.items():
    _template = _def["template"]
    _desc = _def["description"]

    def _make_prompt(template_str, desc):
        async def prompt_fn(**kwargs):
            filled = template_str
            for key, value in kwargs.items():
                filled = filled.replace(f"{{{key}}}", str(value))
            return filled
        prompt_fn.__name__ = desc.replace(" ", "_")[:50]
        return prompt_fn

    mcp.prompt(name=_name, description=_desc)(_make_prompt(_template, _desc))


if __name__ == "__main__":
    mcp.run()
