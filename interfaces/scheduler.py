"""Scheduled tasks: weekly rank tracking, reporting, KB maintenance."""

from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from agent.orchestrator import SEOAgent, AgentContext
from knowledge_base.kb_manager import KnowledgeBase
from memory.structured.step_memory import log_step
from memory.structured.content_memory import get_recent_articles
from memory.structured.keyword_memory import get_all_keywords

scheduler = AsyncIOScheduler()


async def weekly_rank_check(project_id: str = "default"):
    """Run weekly keyword rank tracking for all tracked keywords."""
    keywords = await get_all_keywords(project_id)
    if not keywords:
        return

    kw_list = [kw["keyword"] for kw in keywords[:10]]
    agent = SEOAgent()
    ctx = AgentContext(project_id=project_id)

    await agent.run(
        f"Track rankings for these keywords: {', '.join(kw_list)}. "
        f"Use rank_tracker to check positions and compare with previous data. "
        f"Store results in memory.",
        context=ctx,
    )

    await log_step(
        project_id=project_id,
        task_id="scheduler-weekly",
        step_type="scheduled",
        tool_name="weekly_rank_check",
        input_summary=f"Tracked {len(kw_list)} keywords",
    )


async def weekly_report(project_id: str = "default"):
    """Generate a weekly SEO report."""
    agent = SEOAgent()
    ctx = AgentContext(project_id=project_id)

    articles = await get_recent_articles(project_id, limit=10)
    article_titles = [a.get("title", "") for a in articles]

    await agent.run(
        "Generate a weekly SEO performance report. "
        f"Recent articles: {', '.join(article_titles[:5]) if article_titles else 'none'}. "
        "Use report_generator with report_type='weekly'. Summarize key metrics and recommendations.",
        context=ctx,
    )


async def kb_cleanup():
    """Log KB size — reminder to review outdated documents."""
    kb = KnowledgeBase()
    records = await kb.list_files()
    await log_step(
        project_id="system",
        task_id="scheduler-cleanup",
        step_type="scheduled",
        tool_name="kb_cleanup",
        input_summary=f"KB has {len(records)} documents",
    )


def start_scheduler():
    # Weekly rank check — Monday at 9:07 AM
    scheduler.add_job(
        weekly_rank_check,
        CronTrigger(day_of_week="mon", hour=9, minute=7),
        id="weekly_rank_check",
        replace_existing=True,
    )

    # Weekly report — Monday at 9:15 AM
    scheduler.add_job(
        weekly_report,
        CronTrigger(day_of_week="mon", hour=9, minute=15),
        id="weekly_report",
        replace_existing=True,
    )

    # KB cleanup reminder — daily at 8:03 AM
    scheduler.add_job(
        kb_cleanup,
        CronTrigger(hour=8, minute=3),
        id="kb_cleanup",
        replace_existing=True,
    )

    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)
