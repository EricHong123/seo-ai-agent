"""SEMrush Tool — agent-facing wrapper for SEMrush API data."""

from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "semrush",
    "description": "Fetch SEMrush data: domain analytics (organic traffic, keywords, traffic cost), keyword overview (volume, difficulty, CPC, trend), keyword suggestions (related phrases), competitor gap analysis (keywords competitors rank for that you don't), and backlink data (referring domains, authority scores). Use this for data-driven keyword research, competitor intelligence, and link profile analysis.",
    "parameters": {
        "type": "object",
        "properties": {
            "data_type": {
                "type": "string",
                "enum": ["domain_analytics", "domain_keywords", "keyword_overview", "keyword_suggestions", "competitor_gap", "backlinks"],
                "description": "Type of SEMrush data to fetch",
            },
            "target": {
                "type": "string",
                "description": "Domain, keyword phrase, or URL depending on data_type",
            },
            "database": {
                "type": "string",
                "description": "SEMrush database region (us, uk, de, fr, es, etc.)",
                "default": "us",
            },
            "competitors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Competitor domains for gap analysis (required for competitor_gap)",
            },
            "limit": {
                "type": "integer",
                "description": "Max results",
                "default": 20,
            },
        },
        "required": ["data_type", "target"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(
        data_type: str,
        target: str,
        database: str = "us",
        competitors: list[str] | None = None,
        limit: int = 20,
    ) -> str:
        try:
            from tools.research.semrush_client import SEMrushClient
        except ImportError:
            return "SEMrush client not available."

        client = SEMrushClient()

        if data_type == "domain_analytics":
            data = await client.domain_analytics(target, database)
            rows = data.get("rows", [])
            note = data.get("_note", "")
            lines = [f"# SEMrush Domain Analytics: {target}\n"]
            if note:
                lines.append(f"> {note}\n")
            if rows:
                r = rows[0]
                lines.append(f"| Metric | Value |")
                lines.append(f"|--------|-------|")
                lines.append(f"| Organic Traffic (est.) | {r.get('OrganicTraffic', '-')} |")
                lines.append(f"| Organic Keywords | {r.get('OrganicKeywords', '-')} |")
                lines.append(f"| Traffic Cost (est.) | \${r.get('TrafficCost', '-')} |")
            return "\n".join(lines)

        elif data_type == "domain_keywords":
            data = await client.domain_organic_keywords(target, database, limit)
            rows = data.get("rows", [])
            note = data.get("_note", "")
            lines = [f"# Top Keywords: {target}\n"]
            if note:
                lines.append(f"> {note}\n")
            if rows:
                lines.append("| Keyword | Position | Volume | CPC | Traffic |")
                lines.append("|---------|----------|--------|-----|---------|")
                for r in rows[:limit]:
                    lines.append(f"| {r.get('Keyword', '')} | #{r.get('Position', '-')} | {r.get('SearchVolume', '-')} | \${r.get('CPC', '-')} | {r.get('Traffic', '-')} |")
            return "\n".join(lines)

        elif data_type == "keyword_overview":
            data = await client.keyword_overview(target, database)
            rows = data.get("rows", [])
            note = data.get("_note", "")
            lines = [f"# Keyword Overview: {target}\n"]
            if note:
                lines.append(f"> {note}\n")
            if rows:
                r = rows[0]
                lines.append(f"| Metric | Value |")
                lines.append(f"|--------|-------|")
                for col in data.get("columns", []):
                    lines.append(f"| {col} | {r.get(col, '-')} |")
            return "\n".join(lines)

        elif data_type == "keyword_suggestions":
            data = await client.keyword_suggestions(target, database, limit)
            rows = data.get("rows", [])
            note = data.get("_note", "")
            lines = [f"# Related Keywords: {target}\n"]
            if note:
                lines.append(f"> {note}\n")
            if rows:
                lines.append("| Keyword | Volume | CPC | Competition |")
                lines.append("|---------|--------|-----|-------------|")
                for r in rows[:limit]:
                    lines.append(f"| {r.get('Keyword', '')} | {r.get('SearchVolume', '-')} | \${r.get('CPC', '-')} | {r.get('Competition', '-')} |")
            return "\n".join(lines)

        elif data_type == "competitor_gap":
            if not competitors:
                return "Error: 'competitors' parameter is required for competitor_gap analysis."
            data = await client.competitor_gap(target, competitors, database)
            gap_data = data.get("gap_analysis", {})
            note = data.get("_note", "")
            lines = [f"# Competitor Gap Analysis: {target}\n"]
            if note:
                lines.append(f"> {note}\n")
            for item in gap_data.get("gap_keywords", []):
                comp = item.get("competitor", "")
                kws = item.get("missing_keywords", [])
                lines.append(f"**{comp}** ranks for {len(kws)} keywords you don't:")
                lines.append(", ".join(kws[:15]))
                lines.append("")
            return "\n".join(lines)

        elif data_type == "backlinks":
            data = await client.backlinks(target, database, limit)
            rows = data.get("rows", [])
            note = data.get("_note", "")
            lines = [f"# Backlinks: {target}\n"]
            if note:
                lines.append(f"> {note}\n")
            if rows:
                lines.append("| Referring Domain | Backlinks | Authority |")
                lines.append("|------------------|-----------|-----------|")
                for r in rows[:limit]:
                    lines.append(f"| {r.get('Domain', '')} | {r.get('Backlinks', '-')} | {r.get('AuthorityScore', '-')} |")
            return "\n".join(lines)

        return f"Unknown data_type: {data_type}"

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
