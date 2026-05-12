#!/usr/bin/env python3
"""SEO AI Agent — CLI Interface"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from agent.orchestrator import SEOAgent, AgentContext
from knowledge_base.kb_manager import KnowledgeBase
from knowledge_base.embeddings import EmbeddingService

console = Console()


async def _handle_chat(agent: SEOAgent, task: str, project_id: str, mock: bool = False):
    ctx = AgentContext(project_id=project_id)
    label = "Agent 思考中 (mock mode)..." if mock else "Agent 思考中..."
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description=label, total=None)
        result = await agent.run(task, context=ctx)
    console.print(Markdown(result))


async def _handle_ingest(kb: KnowledgeBase, path: str, project_id: str):
    path_obj = Path(path)
    if path.startswith(("http://", "https://")):
        console.print(f"[cyan]正在抓取 URL: {path}[/cyan]")
        result = await kb.ingest_file(path, project_id=project_id)
    elif not path_obj.exists():
        console.print(f"[red]文件不存在: {path}[/red]")
        return
    else:
        console.print(f"[cyan]正在解析: {path_obj.name}[/cyan]")
        result = await kb.ingest_file(str(path_obj.absolute()), project_id=project_id)

    if result.get("status") == "duplicate":
        console.print(f"[yellow]⚠️ 文件已存在，跳过[/yellow]")
    elif result.get("status") == "ok":
        console.print(f"[green]✓ 已存入知识库[/green]")
        table = Table(title="文件详情")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="white")
        table.add_row("文件名", result.get("filename", ""))
        table.add_row("分块数", str(result.get("chunk_count", 0)))
        table.add_row("Token 数", str(result.get("token_count", 0)))
        table.add_row("标签", ", ".join(result.get("tags", [])))
        console.print(table)
    else:
        console.print(f"[red]✗ 失败: {result}[/red]")


async def _handle_list(kb: KnowledgeBase, project_id: str):
    records = await kb.list_files(project_id)
    if not records:
        console.print("[dim]知识库为空[/dim]")
        return
    table = Table(title="知识库文档")
    table.add_column("文件名", style="white")
    table.add_column("类型", style="cyan")
    table.add_column("分块", justify="right")
    table.add_column("标签", style="green")
    table.add_column("时间", style="dim")
    for r in records:
        tags = r.get("tags", "[]")
        table.add_row(
            r["filename"],
            r["file_type"],
            str(r["chunk_count"]),
            tags,
            r["ingested_at"][:19] if r.get("ingested_at") else "",
        )
    console.print(table)


async def _handle_search(kb: KnowledgeBase, query: str, project_id: str, top_k: int):
    results = await kb.search(query, project_id=project_id, top_k=top_k)
    if not results:
        console.print("[dim]未找到相关文档[/dim]")
        return
    console.print(f"[bold]找到 {len(results)} 个相关片段:[/bold]\n")
    for i, r in enumerate(results):
        src = r.get("metadata", {}).get("filename", "unknown")
        score = r.get("score", 0)
        content = r.get("content", "")[:400]
        console.print(Panel(
            content,
            title=f"[{i+1}] {src} (相关性: {score:.0%})",
            border_style="blue",
        ))


async def _handle_delete(kb: KnowledgeBase, filename: str, project_id: str):
    records = await kb.list_files(project_id)
    match = None
    for r in records:
        if filename.lower() in r["filename"].lower():
            match = r
            break
    if not match:
        console.print(f"[red]未找到匹配 '{filename}' 的文档[/red]")
        return
    await kb.delete_file(match["id"], project_id)
    console.print(f"[green]✓ 已删除: {match['filename']}[/green]")


@click.group()
@click.option("--project", "-p", default="default", help="Project ID")
@click.option("--mock/--no-mock", default=False, help="Run in demo mode without LLM API key")
@click.pass_context
def cli(ctx, project, mock):
    ctx.ensure_object(dict)
    ctx.obj["project_id"] = project
    ctx.obj["mock"] = mock


@cli.command()
@click.option("--project", "-p", default="default")
@click.option("--mock/--no-mock", default=False)
@click.pass_context
def chat(ctx, project, mock):
    """Start interactive chat with the SEO Agent"""
    mock = mock or ctx.obj.get("mock", False)
    console.print(Panel(
        "[bold]SEO AI Agent[/bold]\n"
        "知识库 · 关键词研究 · SERP 分析 · 竞品审计 · 文章撰写 · SEO 评分\n\n"
        + ("[dim]Mock 模式 — 无需 API Key[/dim]\n" if mock else "") +
        "命令: [cyan]/kb[/cyan] 管理知识库 | [cyan]/quit[/cyan] 退出 | 直接输入任务开始",
        border_style="green",
    ))

    async def _chat_loop():
        agent = SEOAgent(mock=mock)
        while True:
            try:
                user_input = click.prompt("\nYou", prompt_suffix=" > ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]再见[/dim]")
                break

            if not user_input:
                continue
            if user_input.lower() in ("/quit", "/exit", "/q"):
                console.print("[dim]再见[/dim]")
                break
            if user_input.lower().startswith("/kb"):
                await _kb_menu(project)
                continue

            await _handle_chat(agent, user_input, project, mock)

    asyncio.run(_chat_loop())


async def _kb_menu(project_id: str):
    kb = KnowledgeBase()
    embed = EmbeddingService()
    kb.embed = embed

    console.print("\n[bold]知识库管理[/bold]")
    console.print("  [cyan]list[/cyan] — 列出所有文档")
    console.print("  [cyan]ingest <文件/URL>[/cyan] — 添加文档")
    console.print("  [cyan]search <关键词>[/cyan] — 搜索文档")
    console.print("  [cyan]delete <文件名>[/cyan] — 删除文档")
    console.print("  [cyan]back[/cyan] — 返回")

    try:
        cmd = click.prompt("\nkb", prompt_suffix=" > ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    parts = cmd.split(maxsplit=1)
    action = parts[0].lower() if parts else ""

    if action == "list":
        await _handle_list(kb, project_id)
    elif action == "ingest" and len(parts) > 1:
        await _handle_ingest(kb, parts[1], project_id)
    elif action == "search" and len(parts) > 1:
        await _handle_search(kb, parts[1], project_id)
    elif action == "delete" and len(parts) > 1:
        await _handle_delete(kb, parts[1], project_id)
    elif action == "back":
        return
    else:
        console.print("[red]未知命令[/red]")


@cli.command()
@click.argument("task", nargs=-1)
@click.option("--project", "-p", default="default")
@click.option("--mock/--no-mock", default=False)
@click.pass_context
def run(ctx, task, project, mock):
    """Run a single SEO task"""
    mock = mock or ctx.obj.get("mock", False)
    task_text = " ".join(task)
    if not task_text:
        console.print("[red]请输入任务描述[/red]")
        return

    async def _run():
        agent = SEOAgent(mock=mock)
        ctx2 = AgentContext(project_id=project)
        result = await agent.run(task_text, context=ctx2)
        console.print(Markdown(result))

    asyncio.run(_run())


@cli.group()
@click.option("--project", "-p", default="default")
@click.pass_context
def kb(ctx, project):
    """Manage the knowledge base"""
    ctx.obj["project_id"] = project


@kb.command("ingest")
@click.argument("path")
@click.pass_context
def kb_ingest(ctx, path):
    """Add a file or URL to the knowledge base"""
    async def _run():
        kb = KnowledgeBase()
        await _handle_ingest(kb, path, ctx.obj["project_id"])
    asyncio.run(_run())


@kb.command("list")
@click.pass_context
def kb_list(ctx):
    """List all documents in the knowledge base"""
    async def _run():
        kb = KnowledgeBase()
        await _handle_list(kb, ctx.obj["project_id"])
    asyncio.run(_run())


@kb.command("search")
@click.argument("query")
@click.option("--top-k", "-k", default=5)
@click.pass_context
def kb_search(ctx, query, top_k):
    """Search the knowledge base"""
    async def _run():
        kb = KnowledgeBase()
        await _handle_search(kb, query, ctx.obj["project_id"], top_k)
    asyncio.run(_run())


@kb.command("delete")
@click.argument("filename")
@click.pass_context
def kb_delete(ctx, filename):
    """Delete a document from the knowledge base"""
    async def _run():
        kb = KnowledgeBase()
        await _handle_delete(kb, filename, ctx.obj["project_id"])
    asyncio.run(_run())


if __name__ == "__main__":
    cli()
