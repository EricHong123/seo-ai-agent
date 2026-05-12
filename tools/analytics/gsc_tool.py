"""GSC Tool — agent-facing wrapper for Google Search Console data."""

from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "gsc_data",
    "description": "Fetch Google Search Console data: query performance (clicks, impressions, CTR, position), index coverage summary, and sitemap status. Use this to analyze organic search performance, find keyword opportunities, identify indexing issues, and track ranking changes.",
    "parameters": {
        "type": "object",
        "properties": {
            "data_type": {
                "type": "string",
                "enum": ["search_analytics", "index_coverage", "sitemaps"],
                "description": "Type of GSC data to fetch",
            },
            "dimensions": {
                "type": "array",
                "items": {"type": "string", "enum": ["query", "page", "country", "device", "searchAppearance"]},
                "description": "Dimensions for search analytics (default: ['query'])",
            },
            "days": {
                "type": "integer",
                "description": "Number of days to look back (default: 28)",
                "default": 28,
            },
            "query_filter": {
                "type": "string",
                "description": "Filter queries containing this text",
            },
            "row_limit": {
                "type": "integer",
                "description": "Max rows to return",
                "default": 50,
            },
        },
        "required": ["data_type"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(
        data_type: str,
        dimensions: list[str] | None = None,
        days: int = 28,
        query_filter: str = "",
        row_limit: int = 50,
    ) -> str:
        from datetime import datetime, timedelta
        import json

        try:
            from tools.analytics.gsc_client import GSCClient
        except ImportError:
            return "GSC client not available. Install google-auth and PyJWT."

        client = GSCClient()

        if data_type == "search_analytics":
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            filters = None
            if query_filter:
                filters = [{"dimension": "query", "operator": "contains", "expression": query_filter}]

            data = await client.search_analytics(
                start_date=start,
                end_date=end,
                dimensions=dimensions or ["query"],
                row_limit=row_limit,
                filters=filters,
            )

            rows = data.get("rows", [])
            if not rows:
                return "No search analytics data found."

            note = data.get("_note", "")
            lines = ["# GSC Search Analytics\n"]
            if note:
                lines.append(f"> {note}\n")

            # Build table
            dims = dimensions or ["query"]
            lines.append("| " + " | ".join(d.title() for d in dims + ["Clicks", "Impressions", "CTR", "Position"]) + " |")
            lines.append("|" + "|".join(["---"] * (len(dims) + 4)) + "|")

            for row in rows[:row_limit]:
                keys = row.get("keys", [])
                clicks = row.get("clicks", 0)
                impressions = row.get("impressions", 0)
                ctr = row.get("ctr", 0)
                pos = row.get("position", 0)
                key_str = " / ".join(str(k) for k in keys)
                lines.append(f"| {key_str} | {clicks:,} | {impressions:,} | {ctr:.1%} | {pos:.1f} |")

            # Top insights
            if rows:
                high_impression_low_ctr = [r for r in rows if r.get("impressions", 0) > 1000 and r.get("ctr", 0) < 0.03]
                striking_distance = [r for r in rows if 4 <= r.get("position", 99) <= 15]

                if high_impression_low_ctr:
                    lines.append(f"\n**Low CTR alerts** ({len(high_impression_low_ctr)} queries with >1K impressions but <3% CTR): Consider rewriting titles/meta descriptions.")
                if striking_distance:
                    lines.append(f"\n**Striking distance** ({len(striking_distance)} queries at position 4-15): Optimize content to reach top 3.")

            return "\n".join(lines)

        elif data_type == "index_coverage":
            data = await client.index_coverage()
            note = data.get("_note", "")
            lines = ["# GSC Index Coverage\n"]
            if note:
                lines.append(f"> {note}\n")

            if data.get("total_pages"):
                lines.append(f"| Metric | Count |")
                lines.append(f"|--------|-------|")
                lines.append(f"| Total Pages | {data['total_pages']} |")
                lines.append(f"| Indexed | {data['indexed']} |")
                lines.append(f"| Errors | {data['errors']} |")
                lines.append(f"| Warnings | {data['warnings']} |")
                lines.append(f"| Excluded | {data['excluded']} |")
                if data.get("error_samples"):
                    lines.append(f"\n**Error samples**: {', '.join(data['error_samples'])}")

            elif data.get("rows"):
                lines.append(f"Fetched {len(data['rows'])} pages from search analytics.")
            else:
                lines.append(f"Response: {json.dumps(data, indent=2)[:500]}")

            return "\n".join(lines)

        elif data_type == "sitemaps":
            data = await client.sitemaps()
            note = data.get("_note", "")
            lines = ["# GSC Sitemaps\n"]
            if note:
                lines.append(f"> {note}\n")

            sitemaps = data.get("sitemap", [])
            if sitemaps:
                lines.append("| Path | Type | Submitted | Errors | Warnings |")
                lines.append("|------|------|-----------|--------|----------|")
                for s in sitemaps:
                    lines.append(f"| {s.get('path', '')} | {s.get('type', '')} | {s.get('lastSubmitted', '')[:10]} | {s.get('errors', 0)} | {s.get('warnings', 0)} |")

            return "\n".join(lines)

        return f"Unknown data_type: {data_type}"

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
