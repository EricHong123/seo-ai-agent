import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse

from interfaces.api.routes import projects, tasks, articles, analytics, kb_routes

app = FastAPI(title="SEO AI Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(articles.router)
app.include_router(analytics.router)
app.include_router(kb_routes.router)

# Mount web UI static files
web_dir = Path(__file__).parent.parent / "web"
web_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@app.get("/")
async def index():
    """Serve the web UI"""
    index_path = web_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "SEO AI Agent API", "docs": "/docs", "web_ui": "coming soon"}


@app.get("/health")
async def health():
    from agent.tool_registry import registry
    return {
        "status": "ok",
        "version": "0.1.0",
        "tools_count": len(registry.list_tools()),
    }


@app.post("/api/agent/run")
async def agent_run(request: Request):
    """Run an agent task with SSE streaming of progress."""
    body = await request.json()
    task = body.get("task", "")
    project_id = body.get("project_id", "default")

    if not task:
        return {"error": "task is required"}

    async def event_stream():
        from agent.orchestrator import SEOAgent, AgentContext
        from agent.system_prompt import build_system_prompt
        from llm.types import Message
        from config.settings import settings

        agent = SEOAgent()
        await agent._init()
        ctx = AgentContext(project_id=project_id)

        # Build system prompt
        from memory.user_profile import get_profile
        from memory.structured.keyword_memory import get_all_keywords
        from memory.structured.content_memory import get_recent_articles
        from memory.structured.step_memory import get_token_usage

        persona = await get_profile(ctx.user_id)
        articles = await get_recent_articles(ctx.project_id)
        keywords = await get_all_keywords(ctx.project_id)
        usage = await get_token_usage(ctx.project_id)

        memory_data = {
            "recent_articles": ", ".join(a.get("title", "") for a in articles[:5]) if articles else "none",
            "tracked_keywords": ", ".join(k.get("keyword", "") for k in keywords[:10]) if keywords else "none",
            "total_steps": usage.get("total_steps", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

        # Auto-RAG
        kb_context = ""
        kb_results = await agent.kb.search(task, project_id=ctx.project_id, top_k=settings.kb_default_top_k)
        if kb_results:
            lines = []
            for r in kb_results:
                src = r.get("metadata", {}).get("filename", "unknown")
                content = r.get("content", "")[:400]
                lines.append(f"  [{src}] {content}")
            kb_context = "\n".join(lines)

        system = build_system_prompt(persona=persona, memory=memory_data, kb_context=kb_context)

        messages: list[Message] = [Message(role="user", content=task)]
        max_iterations = 25
        iteration = 0

        yield f"data: {json.dumps({'type': 'start', 'task': task[:100], 'kb_context': kb_context[:200]})}\n\n"

        while iteration < max_iterations:
            iteration += 1
            tools = agent.registry.list_tools()

            response = await agent.llm.chat(messages=messages, tools=tools, system=system)

            if response.tool_calls:
                yield f"data: {json.dumps({'type': 'thinking', 'content': response.content[:300] if response.content else '', 'tools': [tc.name for tc in response.tool_calls]})}\n\n"

            if not response.tool_calls:
                messages.append(Message(role="assistant", content=response.content))
                yield f"data: {json.dumps({'type': 'done', 'content': response.content})}\n\n"
                yield "data: [DONE]\n\n"
                return

            messages.append(Message(role="assistant", content=response.content, tool_calls=response.tool_calls))

            for tc in response.tool_calls:
                result_text = await agent.registry.execute(tc.name, tc.args)
                messages.append(Message(role="tool", content=result_text[:4000], tool_call_id=tc.id))
                yield f"data: {json.dumps({'type': 'tool_result', 'tool': tc.name, 'result': result_text[:300]})}\n\n"

                # Auto-ingest
                if tc.name in ("competitor_audit", "serp_analyzer", "keyword_research", "rank_tracker", "report_generator"):
                    if len(result_text) > 200 and "Error" not in result_text:
                        await agent.kb.ingest_text(result_text, source="tool_output", filename=f"{tc.name}_{ctx.task_id}", project_id=project_id)

                from memory.structured.step_memory import log_step
                await log_step(
                    project_id=ctx.project_id, task_id=ctx.task_id,
                    step_type="tool_call", tool_name=tc.name,
                    input_summary=json.dumps(tc.args, ensure_ascii=False),
                    output_summary=result_text[:500],
                    success="Error" not in result_text,
                )

        yield f"data: {json.dumps({'type': 'error', 'content': 'Max iterations reached'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
