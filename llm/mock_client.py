"""Mock LLM client for demo/testing without API keys.
Simulates tool-calling behavior by following a predetermined workflow."""

from llm.base import LLMResponse, ToolDef
from llm.types import Message, ToolCall

# Simple workflow patterns: the mock "knows" which tools to call for common tasks
WORKFLOW_PATTERNS = [
    (["serp", "分析", "analyze"], ["kb_search", "serp_analyzer"]),
    (["关键词", "keyword"], ["kb_search", "keyword_research"]),
    (["写", "write", "文章", "article", "content"], ["kb_search", "keyword_research", "serp_analyzer", "outline_generator", "copywriter", "seo_scorer"]),
    (["竞品", "competitor", "audit"], ["kb_search", "competitor_audit"]),
    (["排名", "rank", "track"], ["rank_tracker"]),
    (["报告", "report"], ["report_generator"]),
]


def _match_tools(task: str, available: list[str]) -> list[str]:
    """Match task keywords to appropriate tool sequence."""
    task_lower = task.lower()
    for keywords, tools in WORKFLOW_PATTERNS:
        if any(kw in task_lower for kw in keywords):
            return [t for t in tools if t in available]
    # Default: KB search first, then keyword research
    defaults = ["kb_search", "keyword_research"]
    return [t for t in defaults if t in available]


class MockLLMClient:
    def __init__(self):
        self.model = "mock"
        self._call_count = 0
        self._queued_tools: list[str] = []

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        self._call_count += 1
        tool_names = [t.name for t in (tools or [])]

        # First call: queue tools based on user's task
        if self._call_count == 1:
            last_user_msg = ""
            for m in reversed(messages):
                if m.role == "user":
                    last_user_msg = m.content
                    break
            self._queued_tools = _match_tools(last_user_msg, tool_names)

        # Check if the last message was a tool result
        last_msg = messages[-1] if messages else None
        is_tool_result = last_msg and last_msg.role == "tool"

        if self._queued_tools:
            next_tool = self._queued_tools.pop(0)

            # Find the tool to call
            for t in (tools or []):
                if t.name == next_tool:
                    # Build minimal args based on task context
                    args = self._build_args(next_tool, messages)
                    return LLMResponse(
                        content=f"Let me use {next_tool} to help with this task.",
                        tool_calls=[ToolCall(id=f"mock_{self._call_count}", name=next_tool, args=args)],
                        stop_reason="tool_use",
                        usage={"input_tokens": 100, "output_tokens": 50},
                    )
        else:
            # No more tools — synthesise a final response
            return LLMResponse(
                content=self._summary(messages),
                stop_reason="end_turn",
                usage={"input_tokens": 100, "output_tokens": 200},
            )

        # Fallback
        return LLMResponse(
            content="I've completed the task. The mock mode demonstrates the tool chain, but real content requires an LLM API key.",
            stop_reason="end_turn",
            usage={"input_tokens": 100, "output_tokens": 100},
        )

    def _build_args(self, tool_name: str, messages: list[Message]) -> dict:
        last_user = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user = m.content
                break

        if tool_name == "kb_search":
            return {"query": last_user[:200]}
        elif tool_name == "serp_analyzer":
            return {"keyword": last_user[:100], "market": "us"}
        elif tool_name == "keyword_research":
            return {"keywords": [last_user[:80]], "market": "us"}
        elif tool_name == "competitor_audit":
            return {"topic": last_user[:100]}
        elif tool_name == "copywriter":
            return {"topic": last_user[:100], "keywords": ["test"], "tone": "professional"}
        elif tool_name == "outline_generator":
            return {"topic": last_user[:100], "target_keywords": ["test"]}
        elif tool_name == "seo_scorer":
            return {"content": "test content", "target_keyword": "test"}
        elif tool_name == "fact_checker":
            return {"content": last_user[:500]}
        elif tool_name == "readability":
            return {"content": last_user[:500]}
        elif tool_name == "internal_linker":
            return {"content": last_user[:500]}
        elif tool_name == "schema_markup":
            return {"content_type": "Article", "data": {"title": last_user[:100]}}
        elif tool_name == "rank_tracker":
            return {"keywords": [last_user[:80]]}
        elif tool_name == "report_generator":
            return {"report_type": "weekly"}
        elif tool_name == "web_search":
            return {"query": last_user[:200]}
        elif tool_name == "kb_ingest":
            return {"content": "test", "filename": "test"}
        return {}

    def _summary(self, messages: list[Message]) -> str:
        """Build a summary of what tools were called and their results."""
        tools_called = []
        outputs = []
        for m in messages:
            if m.role == "tool" and m.tool_call_id:
                tools_called.append(m.tool_call_id)
                outputs.append(m.content[:200])

        lines = ["# Demo Mode — Tool Chain Summary\n"]
        lines.append("This is a **mock/demo run** without an LLM API key. Real runs produce actual SEO content.\n")
        lines.append("## Tools That Would Be Called")
        lines.append("The agent's tool-calling loop demonstrated the following workflow:\n")
        for i, output in enumerate(outputs):
            lines.append(f"{i+1}. Tool output preview: {output[:120]}...\n" if len(output) > 120 else f"{i+1}. {output}\n")

        lines.append("\n---")
        lines.append("*To use the full AI agent: set `ANTHROPIC_API_KEY` in `.env` and run without mock mode.*")
        return "\n".join(lines)
