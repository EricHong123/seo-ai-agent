from datetime import datetime, timezone

from memory.structured.models import StepLog, get_session


async def log_step(
    project_id: str,
    task_id: str,
    step_type: str,
    tool_name: str | None = None,
    input_summary: str = "",
    output_summary: str = "",
    tokens_used: int = 0,
    latency_ms: int = 0,
    success: bool = True,
    error_message: str | None = None,
):
    session = get_session()
    log = StepLog(
        project_id=project_id,
        task_id=task_id,
        step_type=step_type,
        tool_name=tool_name,
        input_summary=input_summary[:500],
        output_summary=output_summary[:500],
        tokens_used=tokens_used,
        latency_ms=latency_ms,
        success=1 if success else 0,
        error_message=error_message[:500] if error_message else None,
        created_at=datetime.now(timezone.utc),
    )
    session.add(log)
    session.commit()
    session.close()


async def get_recent_steps(project_id: str, limit: int = 20) -> list[dict]:
    session = get_session()
    rows = (
        session.query(StepLog)
        .filter_by(project_id=project_id)
        .order_by(StepLog.created_at.desc())
        .limit(limit)
        .all()
    )
    result = [
        {
            "step_type": r.step_type,
            "tool_name": r.tool_name,
            "input_summary": r.input_summary,
            "output_summary": r.output_summary,
            "tokens_used": r.tokens_used,
            "success": bool(r.success),
        }
        for r in rows
    ]
    session.close()
    return result


async def get_token_usage(project_id: str) -> dict:
    session = get_session()
    rows = (
        session.query(StepLog)
        .filter_by(project_id=project_id)
        .all()
    )
    total_input = sum(r.tokens_used for r in rows)
    total_steps = len(rows)
    session.close()
    return {"total_tokens": total_input, "total_steps": total_steps}
