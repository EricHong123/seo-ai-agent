import time
import json
from dataclasses import dataclass, field

from llm import get_llm_client, LLMClient
from llm.base import ToolDef
from llm.types import Message, ToolCall, ToolResult
from agent.tool_registry import ToolRegistry
from agent.system_prompt import build_system_prompt
from agent.planner import generate_task_id, is_terminal, extract_final_output
from knowledge_base.kb_manager import KnowledgeBase
from knowledge_base.embeddings import EmbeddingService
from memory.structured.keyword_memory import get_all_keywords
from memory.structured.content_memory import get_recent_articles
from memory.structured.step_memory import log_step, get_token_usage
from memory.semantic.article_recall import ArticleMemory
from memory.user_profile import get_profile
from memory.structured.models import init_db
from config.settings import settings

# Tool factories
from tools.kb.kb_search import make_tool as make_kb_search
from tools.kb.kb_ingest import make_tool as make_kb_ingest
from tools.kb.kb_list import make_tool as make_kb_list
from tools.kb.kb_delete import make_tool as make_kb_delete
from tools.research.keyword_research import make_tool as make_keyword_research
from tools.research.serp_analyzer import make_tool as make_serp_analyzer
from tools.research.competitor_audit import make_tool as make_competitor_audit
from tools.content.copywriter import make_tool as make_copywriter
from tools.content.outline_generator import make_tool as make_outline_generator
from tools.content.fact_checker import make_tool as make_fact_checker
from tools.optimization.seo_scorer import make_tool as make_seo_scorer
from tools.optimization.readability import make_tool as make_readability
from tools.optimization.internal_linker import make_tool as make_internal_linker
from tools.optimization.schema_markup import make_tool as make_schema_markup
from tools.analytics.rank_tracker import make_tool as make_rank_tracker
from tools.analytics.report_generator import make_tool as make_report_generator
from tools.analytics.gsc_tool import make_tool as make_gsc_data
from tools.optimization.pagespeed import make_tool as make_pagespeed
from tools.research.semrush_tool import make_tool as make_semrush
from tools.web.search import make_tool as make_web_search
from tools.skills.generate_pptx import make_tool as make_generate_pptx
from tools.skills.generate_excel import make_tool as make_generate_excel
from tools.skills.export_utils import save_all_formats


@dataclass
class AgentContext:
    project_id: str = "default"
    user_id: str = "default"
    task_id: str = field(default_factory=generate_task_id)


class SEOAgent:
    def __init__(self, mock: bool = False):
        self.mock = mock
        self.embed_service = EmbeddingService()
        self.kb = KnowledgeBase(embed_service=self.embed_service)
        self.article_memory = ArticleMemory(embed_service=self.embed_service)
        self.registry = ToolRegistry()
        self.llm: LLMClient | None = None
        init_db()

    async def _init(self):
        if self.llm is None:
            self.llm = await get_llm_client(mock=self.mock)
        self._register_tools()

    def _register_tools(self):
        # KB tools
        self.registry.register(make_kb_search(self.kb))
        self.registry.register(make_kb_ingest(self.kb))
        self.registry.register(make_kb_list(self.kb))
        self.registry.register(make_kb_delete(self.kb))
        # Research tools
        self.registry.register(make_keyword_research(self.llm))
        self.registry.register(make_serp_analyzer(self.llm))
        self.registry.register(make_competitor_audit(self.llm))
        # Content tools
        self.registry.register(make_outline_generator(self.llm))
        self.registry.register(make_copywriter(self.llm))
        self.registry.register(make_fact_checker(self.llm))
        # Optimization tools
        self.registry.register(make_seo_scorer(self.llm))
        self.registry.register(make_readability(self.llm))
        self.registry.register(make_internal_linker(self.llm))
        self.registry.register(make_schema_markup(self.llm))
        # Analytics tools
        self.registry.register(make_rank_tracker(self.llm))
        self.registry.register(make_report_generator(self.llm))
        self.registry.register(make_gsc_data(self.llm))
        # Third-party API tools
        self.registry.register(make_pagespeed(self.llm))
        self.registry.register(make_semrush(self.llm))
        # Skill tools
        self.registry.register(make_generate_pptx())
        self.registry.register(make_generate_excel())
        # Web tools
        self.registry.register(make_web_search(self.llm))

    async def run(self, task: str, context: AgentContext | None = None) -> str:
        await self._init()
        ctx = context or AgentContext()

        # Build system prompt with persona, memory, and KB context
        persona = await get_profile(ctx.user_id)
        recent_articles = await get_recent_articles(ctx.project_id)
        keywords = await get_all_keywords(ctx.project_id)
        usage = await get_token_usage(ctx.project_id)

        memory_data = {
            "recent_articles": ", ".join(
                a.get("title", "") for a in recent_articles[:5]
            ) if recent_articles else "none",
            "tracked_keywords": ", ".join(
                k.get("keyword", "") for k in keywords[:10]
            ) if keywords else "none",
            "total_steps": usage.get("total_steps", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

        # Auto-RAG: search KB before starting
        kb_context = ""
        kb_results = await self.kb.search(task, project_id=ctx.project_id, top_k=settings.kb_default_top_k)
        if kb_results:
            lines = []
            for r in kb_results:
                src = r.get("metadata", {}).get("filename", "unknown")
                content = r.get("content", "")[:400]
                lines.append(f"  [{src}] {content}")
            kb_context = "\n".join(lines)

        system = build_system_prompt(persona=persona, memory=memory_data, kb_context=kb_context)

        messages: list[Message] = [Message(role="user", content=task)]
        total_tokens = 0
        max_iterations = 20
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            tools = self.registry.list_tools()

            t0 = time.time()
            response = await self.llm.chat(
                messages=messages,
                tools=tools,
                system=system,
            )
            latency = int((time.time() - t0) * 1000)
            total_tokens += response.usage.get("input_tokens", 0) + response.usage.get("output_tokens", 0)

            if response.content:
                total_tokens += len(response.content) // 4  # rough token estimate

            if not response.tool_calls:
                messages.append(Message(role="assistant", content=response.content))
                if is_terminal(messages, response):
                    break
                continue

            # Process tool calls — append ONE assistant msg with both content and tool_calls
            messages.append(Message(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            ))

            for tc in response.tool_calls:
                t_t0 = time.time()
                result_text = await self.registry.execute(tc.name, tc.args)
                t_latency = int((time.time() - t_t0) * 1000)

                messages.append(Message(
                    role="tool",
                    content=result_text[:4000],
                    tool_call_id=tc.id,
                ))

                await log_step(
                    project_id=ctx.project_id,
                    task_id=ctx.task_id,
                    step_type="tool_call",
                    tool_name=tc.name,
                    input_summary=json.dumps(tc.args, ensure_ascii=False),
                    output_summary=result_text[:500],
                    tokens_used=response.usage.get("output_tokens", 0),
                    latency_ms=t_latency,
                    success="Error" not in result_text,
                )

                # Auto-ingest valuable results into KB (not file export — too noisy)
                if tc.name in ("competitor_audit", "serp_analyzer", "keyword_research",
                               "rank_tracker", "report_generator", "copywriter",
                               "outline_generator", "seo_scorer", "readability",
                               "fact_checker", "internal_linker", "schema_markup"):
                    if len(result_text) > 200 and "Error" not in result_text:
                        await self.kb.ingest_text(
                            result_text,
                            source="tool_output",
                            filename=f"{tc.name}_{ctx.task_id}",
                            project_id=ctx.project_id,
                        )

            if is_terminal(messages, response):
                break

        # Final synthesis: use only the last few messages to avoid token bloat
        recent = messages[-8:]  # Last 4 tool cycles max
        synthesis_prompt = (
            "Synthesize a comprehensive final answer from the tool results above. "
            "Include all key data, findings, and recommendations. "
            "Provide the actual numbers and content — not a summary of what you did."
        )
        recent.append(Message(role="user", content=synthesis_prompt))
        final_response = await self.llm.chat(
            messages=recent,
            tools=[],
            system=system,
        )
        # Save final output as downloadable file
        if len(final_response.content) > 100:
            save_all_formats(final_response.content, prefix="final-report")
        return final_response.content
