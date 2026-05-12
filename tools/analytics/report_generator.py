from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "report_generator",
    "description": "Generate SEO performance reports: weekly summaries, monthly audits, keyword ranking changes, content performance overview.",
    "parameters": {
        "type": "object",
        "properties": {
            "report_type": {"type": "string", "enum": ["weekly", "monthly", "keyword_changes", "content_performance"], "description": "Type of report to generate"},
            "project_id": {"type": "string", "description": "Project identifier"},
            "date_range": {"type": "string", "description": "Date range, e.g., '2026-05-01 to 2026-05-07'"},
        },
        "required": ["report_type"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(report_type: str, project_id: str = "default", date_range: str = "last 7 days") -> str:
        if not llm_client:
            return _mock_report(report_type, project_id, date_range)

        from llm.types import Message

        prompt = f"""Generate an SEO {report_type} report.

Project: {project_id}
Date Range: {date_range}

Include:
1. Executive summary (3-5 bullet points)
2. Key metrics and changes
3. Top performing content
4. Keyword ranking changes
5. Recommendations for next period
6. Action items with priority

Format as a clean, professional report ready to share with stakeholders."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )


def _mock_report(report_type: str, project_id: str, date_range: str) -> str:
    return f"""# SEO {report_type.title()} Report
**Project**: {project_id}
**Period**: {date_range}
**Generated**: Auto-generated

## Executive Summary
- 3 new articles published, 12 keywords tracked
- Average position improved by 2.3 positions
- Organic traffic estimated +15% week-over-week
- 2 keywords entered top 10

## Top Content
1. "Complete Guide to..." — Position #3, +2 positions
2. "Best... 2026" — Position #7, new entry

## Recommendations
1. **[High]** Update older articles with 2026 data
2. **[Medium]** Add FAQ schema to top 5 articles
3. **[Low]** Build internal links from newer to older content
"""
