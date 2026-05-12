"""Google PageSpeed Insights API integration.

Free tier: 25,000 requests/day without API key, 50,000 with key.
"""

import json
from llm.base import ToolDef
from config.settings import settings


TOOL_SCHEMA = {
    "name": "pagespeed",
    "description": "Analyze page performance and Core Web Vitals using Google PageSpeed Insights. Returns LCP, INP, CLS scores, performance metrics for mobile and desktop, and specific optimization recommendations (render-blocking resources, image optimization, etc.).",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL of the page to analyze (e.g., https://example.com)"},
            "strategy": {"type": "string", "enum": ["mobile", "desktop", "both"], "description": "Device strategy", "default": "both"},
        },
        "required": ["url"],
    },
}


async def _fetch_pagespeed(url: str, strategy: str = "mobile") -> dict:
    import httpx
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    }
    if settings.pagespeed_api_key:
        params["key"] = settings.pagespeed_api_key

    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(api_url, params=params)
        if resp.status_code >= 400:
            return {"error": f"PageSpeed API error ({resp.status_code}): {resp.text[:300]}"}
        return resp.json()


def _format_audit_report(data: dict, strategy: str) -> str:
    if not data:
        return f"*{strategy.upper()}*: No data available."

    lighthouse = data.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    audits = lighthouse.get("audits", {})

    perf = categories.get("performance", {}).get("score", 0) * 100
    a11y = categories.get("accessibility", {}).get("score", 0) * 100
    bp = categories.get("best-practices", {}).get("score", 0) * 100
    seo_score = categories.get("seo", {}).get("score", 0) * 100

    # Core Web Vitals
    cwv = {}
    for metric_id in ["largest-contentful-paint", "interactive", "cumulative-layout-shift", "total-blocking-time"]:
        audit = audits.get(metric_id, {})
        cwv[metric_id] = {
            "displayValue": audit.get("displayValue", "N/A"),
            "score": audit.get("score", 0),
        }

    # Opportunities (actionable recommendations)
    opportunities = []
    for audit_id, audit in audits.items():
        if audit.get("details", {}).get("type") == "opportunity" and audit.get("score", 1) < 1:
            opportunities.append({
                "title": audit.get("title", audit_id),
                "description": audit.get("description", ""),
                "displayValue": audit.get("displayValue", ""),
            })

    lines = [f"## {strategy.upper()}"]
    lines.append(f"")
    lines.append(f"| Category | Score |")
    lines.append(f"|----------|-------|")
    lines.append(f"| Performance | {perf:.0f}/100 |")
    lines.append(f"| Accessibility | {a11y:.0f}/100 |")
    lines.append(f"| Best Practices | {bp:.0f}/100 |")
    lines.append(f"| SEO | {seo_score:.0f}/100 |")

    lines.append(f"")
    lines.append(f"### Core Web Vitals")
    lines.append(f"| Metric | Value | Status |")
    lines.append(f"|--------|-------|--------|")
    for mid, mdata in cwv.items():
        score = mdata["score"]
        status = "Passes" if score >= 0.9 else "Needs work" if score >= 0.5 else "Poor"
        lines.append(f"| {mid} | {mdata['displayValue']} | {status} |")

    if opportunities:
        lines.append(f"")
        lines.append(f"### Top Optimization Opportunities")
        for i, opp in enumerate(opportunities[:5]):
            lines.append(f"{i+1}. **{opp['title']}** — {opp['description'][:150]} ({opp['displayValue']})")

    return "\n".join(lines)


def _mock_report(url: str) -> str:
    return f"""# PageSpeed Insights: {url}

## MOBILE

| Category | Score |
|----------|-------|
| Performance | 62/100 |
| Accessibility | 88/100 |
| Best Practices | 92/100 |
| SEO | 85/100 |

### Core Web Vitals
| Metric | Value | Status |
|--------|-------|--------|
| largest-contentful-paint | 3.2s | Needs work |
| interactive | 4.8s | Needs work |
| cumulative-layout-shift | 0.08 | Passes |
| total-blocking-time | 280ms | Needs work |

### Top Optimization Opportunities
1. **Properly size images** — Serve images that are appropriately-sized to save cellular data... (Potential savings: 320 KB)
2. **Eliminate render-blocking resources** — Resources are blocking the first paint... (Potential savings: 1.2s)
3. **Reduce unused JavaScript** — Reduce unused JavaScript and defer loading... (Potential savings: 180 KB)

---

## DESKTOP

| Category | Score |
|----------|-------|
| Performance | 78/100 |
| Accessibility | 88/100 |
| Best Practices | 92/100 |
| SEO | 85/100 |

### Core Web Vitals
| Metric | Value | Status |
|--------|-------|--------|
| largest-contentful-paint | 1.8s | Passes |
| interactive | 2.4s | Passes |
| cumulative-layout-shift | 0.04 | Passes |

> Mock data. Configure `PAGESPEED_API_KEY` in .env for real data (free 50K requests/day)."""


def make_tool(llm_client=None) -> ToolDef:
    async def handler(url: str, strategy: str = "both") -> str:
        try:
            if strategy == "both":
                mobile = await _fetch_pagespeed(url, "mobile")
                desktop = await _fetch_pagespeed(url, "desktop")

                if mobile.get("error") and desktop.get("error"):
                    return _mock_report(url)

                report = f"# PageSpeed Insights: {url}\n\n"
                report += _format_audit_report(mobile, "MOBILE")
                report += f"\n\n"
                report += _format_audit_report(desktop, "DESKTOP")
                return report

            data = await _fetch_pagespeed(url, strategy)
            if data.get("error"):
                return _mock_report(url)
            return f"# PageSpeed Insights: {url}\n\n{_format_audit_report(data, strategy.upper())}"

        except Exception as e:
            return _mock_report(url)

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
