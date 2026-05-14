"""Content pipeline routes — bridges SEO Agent output to social-auto-upload format.

SAU (social-auto-upload) can consume this endpoint via --content-url flag:
    sau douyin upload-video --content-url http://localhost:8000/api/content/export/latest
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/content", tags=["content"])

# In-memory store for latest task results
_latest_results: dict[str, dict] = {}


class ContentExport(BaseModel):
    title: str
    content: str
    tags: list[str]
    platform_hint: str = "article"  # "video" | "article" | "note"
    source_task: str = ""
    exported_at: str = ""


def store_task_result(project_id: str, task: str, result: str):
    """Called by SSE endpoint after agent completes a task."""
    title = _extract_title(result)
    tags = _extract_tags(result, task)

    _latest_results[project_id] = {
        "title": title,
        "content": result,
        "tags": tags,
        "platform_hint": _detect_platform(result),
        "source_task": task[:200],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    # Also save the last 10 globally
    _latest_results["latest"] = _latest_results[project_id]


def _extract_title(text: str) -> str:
    """Extract the first H1 heading as title."""
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("# ") and len(line) > 3:
            return line[2:].strip()[:150]
    # Fallback: first non-empty line
    for line in text.strip().split("\n"):
        if line.strip() and not line.startswith("|") and not line.startswith("```"):
            return line.strip()[:150]
    return "Untitled"


def _extract_tags(text: str, task: str = "") -> list[str]:
    """Extract hashtags and keywords as tags."""
    tags = []
    # Extract #hashtags
    hashtags = re.findall(r"#(\w[\w-]*)", text)
    tags.extend(hashtags[:10])

    # Extract keywords from tables (common SEO output format)
    kw_matches = re.findall(r"\|\s*\*{0,2}([\w\s-]{3,40})\*{0,2}\s*\|", text)
    for kw in kw_matches:
        kw = kw.strip().lower()
        if len(kw) > 2 and kw not in tags and len(tags) < 15:
            tags.append(kw)

    # Add task context words
    if not tags and task:
        words = re.findall(r"[\w一-鿿]{2,}", task)
        tags = words[:8]

    return tags[:15]


def _detect_platform(text: str) -> str:
    """Guess the best platform format based on content."""
    wc = len(text.split())
    if wc < 200:
        return "note"    # Short → 小红书/朋友圈图文
    if wc < 800:
        return "article" # Medium → 百家号/公众号
    return "video"       # Long → 视频脚本/抖音/B站


# ── Endpoints ──────────────────────────────────────────

@router.get("/export/{project_id}")
async def export_content(project_id: str = "latest", format: str = Query("json", enum=["json", "markdown", "sau"])):
    """Export the latest agent output in various formats.

    - json: Full structured content (default)
    - markdown: Raw markdown
    - sau: social-auto-upload compatible format (title, content, tags, cover)
    """
    if project_id not in _latest_results:
        raise HTTPException(404, f"No content found for project '{project_id}'. Run an agent task first.")

    data = _latest_results[project_id]

    if format == "markdown":
        return {"content": data["content"]}

    if format == "sau":
        # SAU-compatible format: flat fields for CLI consumption
        return {
            "title": data["title"],
            "description": data["content"][:1000],
            "tags": data["tags"],
            "platform_hint": data["platform_hint"],
            "source": "seo-ai-agent",
            "exported_at": data["exported_at"],
        }

    return ContentExport(**data)


@router.get("/export/{project_id}/file")
async def download_content(project_id: str = "latest"):
    """Download the latest output as a .md file."""
    if project_id not in _latest_results:
        raise HTTPException(404, f"No content found for project '{project_id}'.")

    from fastapi.responses import Response
    data = _latest_results[project_id]
    md = f"# {data['title']}\n\n{data['content']}"
    return Response(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={data['title'][:40]}.md"},
    )


@router.get("/export/list")
async def list_exports():
    """List all available exports."""
    projects = {k: {"title": v["title"], "exported_at": v["exported_at"]}
                for k, v in _latest_results.items() if k != "latest"}
    return {"projects": projects, "latest": _latest_results.get("latest", {}).get("title", "")}
