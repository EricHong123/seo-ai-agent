"""Google Search Console API integration.

Uses a service account JSON key file for authentication.
The service account must be added to the GSC property.

Usage:
    GSCClient(site_url="https://www.example.com", credentials_file="key.json")
"""

import json
from datetime import datetime, timedelta
from config.settings import settings


class GSCClient:
    """Lightweight GSC client using the Google API via httpx + OAuth2 service account."""

    def __init__(self, site_url: str = "", credentials_file: str = ""):
        self.site_url = site_url or settings.gsc_site_url
        self.credentials_file = credentials_file or settings.google_credentials_file
        self._token = None
        self._token_expiry = None

    @property
    def is_configured(self) -> bool:
        return bool(self.site_url and self.credentials_file)

    async def _get_token(self):
        """Get OAuth2 access token using service account JWT."""
        import time as _time
        if self._token and self._token_expiry and _time.time() < self._token_expiry - 60:
            return self._token

        import jwt
        import httpx

        with open(self.credentials_file) as f:
            creds = json.load(f)

        now = int(_time.time())
        assertion = jwt.encode({
            "iss": creds["client_email"],
            "scope": "https://www.googleapis.com/auth/webmasters.readonly",
            "aud": creds["token_uri"],
            "exp": now + 3600,
            "iat": now,
        }, creds["private_key"], algorithm="RS256")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(creds["token_uri"], data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            })
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expiry = now + data.get("expires_in", 3600)
            return self._token

    async def _request(self, endpoint: str, body: dict | None = None) -> dict:
        import httpx
        token = await self._get_token()
        url = f"https://www.googleapis.com/webmasters/v3/sites/{self.site_url}/{endpoint}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30) as client:
            if body is not None:
                resp = await client.post(url, headers=headers, json=body)
            else:
                resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def search_analytics(
        self,
        start_date: str = "",
        end_date: str = "",
        dimensions: list[str] | None = None,
        row_limit: int = 100,
        filters: list[dict] | None = None,
    ) -> dict:
        """Query GSC search analytics.

        dimensions: ["query", "page", "country", "device", "searchAppearance"]
        filters: [{"dimension": "query", "operator": "contains", "expression": "brand"}]
        """
        if not self.is_configured:
            return _mock_search_analytics()

        body = {
            "startDate": start_date or (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d"),
            "endDate": end_date or datetime.now().strftime("%Y-%m-%d"),
            "dimensions": dimensions or ["query"],
            "rowLimit": min(row_limit, 25000),
        }
        if filters:
            body["dimensionFilterGroups"] = [{"filters": filters}]

        return await self._request("searchAnalytics/search", body)

    async def index_coverage(self) -> dict:
        """Get index coverage summary."""
        if not self.is_configured:
            return _mock_index_coverage()

        # GSC API doesn't have a direct index coverage endpoint via v3.
        # We use the sitemap + URL inspection approach.
        body = {
            "startDate": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
            "endDate": datetime.now().strftime("%Y-%m-%d"),
            "dimensions": ["page"],
            "rowLimit": 1000,
        }
        try:
            return await self._request("searchAnalytics/search", body)
        except Exception:
            return {"error": "Could not fetch index data", "pages": []}

    async def sitemaps(self) -> dict:
        """List submitted sitemaps and their status."""
        if not self.is_configured:
            return _mock_sitemaps()
        return await self._request("sitemaps")


def _mock_search_analytics() -> dict:
    return {
        "rows": [
            {"keys": ["best standing desk"], "clicks": 3200, "impressions": 45000, "ctr": 0.071, "position": 4.2},
            {"keys": ["standing desk review"], "clicks": 1800, "impressions": 28000, "ctr": 0.064, "position": 6.8},
            {"keys": ["electric standing desk"], "clicks": 950, "impressions": 15000, "ctr": 0.063, "position": 8.1},
            {"keys": ["standing desk for home office"], "clicks": 620, "impressions": 12000, "ctr": 0.052, "position": 5.5},
            {"keys": ["best standing desk 2026"], "clicks": 410, "impressions": 8500, "ctr": 0.048, "position": 3.1},
        ],
        "responseAggregationType": "byProperty",
        "_note": "Mock data. Configure GSC credentials for real data.",
    }


def _mock_index_coverage() -> dict:
    return {
        "total_pages": 486,
        "indexed": 412,
        "errors": 18,
        "warnings": 31,
        "excluded": 25,
        "error_samples": ["/products/old-version (404)", "/tag/obsolete (noindex)"],
        "_note": "Mock data. Configure GSC credentials for real data.",
    }


def _mock_sitemaps() -> dict:
    return {
        "sitemap": [
            {"path": "https://example.com/sitemap.xml", "type": "sitemapIndex", "lastSubmitted": "2026-05-01", "isPending": False, "warnings": 0, "errors": 0},
            {"path": "https://example.com/post-sitemap.xml", "type": "sitemap", "lastSubmitted": "2026-05-10", "isPending": False, "warnings": 2, "errors": 0},
        ],
        "_note": "Mock data. Configure GSC credentials for real data.",
    }
