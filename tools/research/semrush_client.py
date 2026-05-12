"""SEMrush API integration.

Uses SEMrush API key for domain analytics, keyword research, and competitor analysis.
"""

import json
import httpx
from config.settings import settings


class SEMrushClient:
    """Lightweight SEMrush API client."""

    BASE_URL = "https://api.semrush.com/"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.semrush_api_key

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def _query(self, params: dict) -> dict:
        params["key"] = self.api_key
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()

            # SEMrush returns TSV-like text, not JSON
            text = resp.text.strip()
            if not text:
                return {"rows": [], "columns": []}

            lines = text.split("\n")
            if len(lines) < 2:
                return {"rows": [], "columns": lines[0].split(";") if lines else []}

            columns = lines[0].split(";")
            rows = []
            for line in lines[1:]:
                vals = line.split(";")
                rows.append(dict(zip(columns, vals)))

            return {"columns": columns, "rows": rows}

    async def domain_analytics(self, domain: str, database: str = "us") -> dict:
        """Get organic search data for a domain."""
        if not self.is_configured:
            return _mock_domain_analytics(domain)
        return await self._query({
            "type": "domain_ranks",
            "domain": domain,
            "database": database,
            "display_limit": 10,
        })

    async def domain_organic_keywords(self, domain: str, database: str = "us", limit: int = 20) -> dict:
        """Get top organic keywords for a domain."""
        if not self.is_configured:
            return _mock_organic_keywords(domain)
        return await self._query({
            "type": "domain_organic",
            "domain": domain,
            "database": database,
            "display_limit": limit,
        })

    async def keyword_overview(self, phrase: str, database: str = "us") -> dict:
        """Get keyword metrics: volume, difficulty, CPC, competition."""
        if not self.is_configured:
            return _mock_keyword(phrase)
        return await self._query({
            "type": "phrase_this",
            "phrase": phrase,
            "database": database,
            "display_limit": 1,
        })

    async def keyword_suggestions(self, phrase: str, database: str = "us", limit: int = 20) -> dict:
        """Get related keyword suggestions."""
        if not self.is_configured:
            return _mock_suggestions(phrase)
        return await self._query({
            "type": "phrase_related",
            "phrase": phrase,
            "database": database,
            "display_limit": limit,
        })

    async def competitor_gap(self, domain: str, competitors: list[str], database: str = "us") -> dict:
        """Find keywords that competitors rank for but the target domain doesn't."""
        if not self.is_configured:
            return _mock_gap(domain, competitors)
        params = {
            "type": "domain_organic",
            "domain": domain,
            "database": database,
            "display_limit": 20,
        }
        # SEMrush doesn't have a direct "gap" endpoint; we compare manually
        all_keywords = {}
        all_keywords[domain] = await self._query({**params, "domain": domain})
        for comp in competitors:
            all_keywords[comp] = await self._query({**params, "domain": comp})
        return {"gap_analysis": _process_gap_analysis(domain, all_keywords)}

    async def backlinks(self, domain: str, database: str = "us", limit: int = 20) -> dict:
        """Get backlink data for a domain."""
        if not self.is_configured:
            return _mock_backlinks(domain)
        return await self._query({
            "type": "backlinks_refdomains",
            "domain": domain,
            "database": database,
            "display_limit": limit,
        })


def _process_gap_analysis(target: str, data: dict) -> dict:
    gap_kws = []
    target_kws = {r["Keyword"] for r in data.get(target, {}).get("rows", [])}
    for comp, comp_data in data.items():
        if comp == target:
            continue
        comp_kws = {r["Keyword"] for r in comp_data.get("rows", [])}
        missing = list(comp_kws - target_kws)[:10]
        gap_kws.append({"competitor": comp, "missing_keywords": missing})
    return {"gap_keywords": gap_kws}


# Mock data
def _mock_domain_analytics(domain: str) -> dict:
    return {
        "rows": [{"Domain": domain, "OrganicTraffic": "125000", "OrganicKeywords": "8500", "TrafficCost": "42000"}],
        "columns": ["Domain", "OrganicTraffic", "OrganicKeywords", "TrafficCost"],
        "_note": "Mock data. Configure SEMRUSH_API_KEY for real data.",
    }

def _mock_organic_keywords(domain: str) -> dict:
    return {"rows": [
        {"Keyword": "best standing desk", "Position": "4", "SearchVolume": "22000", "CPC": "1.75", "Traffic": "3200"},
        {"Keyword": "standing desk review", "Position": "7", "SearchVolume": "15000", "CPC": "1.40", "Traffic": "1800"},
        {"Keyword": "electric standing desk", "Position": "3", "SearchVolume": "49500", "CPC": "2.40", "Traffic": "8900"},
        {"Keyword": "standing desk converter", "Position": "8", "SearchVolume": "12000", "CPC": "1.60", "Traffic": "1400"},
        {"Keyword": "standing desk for home office", "Position": "5", "SearchVolume": "8800", "CPC": "1.20", "Traffic": "950"},
    ], "columns": ["Keyword", "Position", "SearchVolume", "CPC", "Traffic"], "_note": "Mock data."}

def _mock_keyword(phrase: str) -> dict:
    return {"rows": [{"Keyword": phrase, "SearchVolume": "28000", "CPC": "1.80", "Competition": "0.75", "NumberofResults": "125000000", "Trend": "0.12"}], "columns": ["Keyword", "SearchVolume", "CPC", "Competition", "NumberofResults", "Trend"], "_note": "Mock data."}

def _mock_suggestions(phrase: str) -> dict:
    return {"rows": [
        {"Keyword": f"best {phrase}", "SearchVolume": "22000", "CPC": "1.75", "Competition": "0.72"},
        {"Keyword": f"{phrase} review", "SearchVolume": "15000", "CPC": "1.40", "Competition": "0.65"},
        {"Keyword": f"{phrase} 2026", "SearchVolume": "8500", "CPC": "1.10", "Competition": "0.45"},
        {"Keyword": f"{phrase} for back pain", "SearchVolume": "8100", "CPC": "1.30", "Competition": "0.28"},
        {"Keyword": f"{phrase} buying guide", "SearchVolume": "6800", "CPC": "1.95", "Competition": "0.55"},
    ], "columns": ["Keyword", "SearchVolume", "CPC", "Competition"], "_note": "Mock data."}

def _mock_gap(domain: str, competitors: list[str]) -> dict:
    return {"gap_analysis": {"gap_keywords": [{"competitor": c, "missing_keywords": [f"keyword-{i}" for i in range(5)]} for c in competitors]}, "_note": "Mock data."}

def _mock_backlinks(domain: str) -> dict:
    return {"rows": [{"Domain": f"ref{i}.com", "Backlinks": str(500-i*40), "AuthorityScore": str(70-i*5)} for i in range(5)], "columns": ["Domain", "Backlinks", "AuthorityScore"], "_note": "Mock data."}
