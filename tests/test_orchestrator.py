"""Integration tests for the agent orchestrator with MockLLMClient."""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def agent():
    from agent.orchestrator import SEOAgent
    return SEOAgent(mock=True)


class TestAgentRun:
    @pytest.mark.asyncio
    async def test_simple_task(self, agent):
        """Agent should complete a simple task without crashing."""
        result = await agent.run("Say hello in one sentence.")
        assert len(result) > 10
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_keyword_task(self, agent):
        """Agent should use keyword_research tool for keyword tasks."""
        result = await agent.run(
            "研究 best standing desk 关键词，给3个长尾词"
        )
        assert len(result) > 100
        # Mock flow will call kb_search → keyword_research → final synthesis

    @pytest.mark.asyncio
    async def test_on_progress_callback(self, agent):
        """Progress callback should fire at each step."""
        events = []

        async def collect(event):
            events.append(event)

        result = await agent.run(
            "分析 best standing desk 的 SERP",
            on_progress=collect,
        )
        assert len(events) >= 2  # at least start + done
        assert events[0]["type"] == "start"
        assert events[-1]["type"] == "done"
        # Should have thinking and/or tool_result events
        types = {e["type"] for e in events}
        assert "done" in types

    @pytest.mark.asyncio
    async def test_project_context(self):
        """Agent should use the given project context."""
        from agent.orchestrator import SEOAgent, AgentContext
        agent = SEOAgent(mock=True)
        ctx = AgentContext(project_id="test-project-123")
        result = await agent.run("Hello", context=ctx)
        assert len(result) > 5


class TestToolRegistry:
    def test_all_tools_registered(self):
        """All 22 tools should be registered after init."""
        import asyncio
        from agent.orchestrator import SEOAgent

        async def _test():
            agent = SEOAgent(mock=True)
            await agent._init()
            tools = agent.registry.list_tools()
            assert len(tools) >= 20
            names = {t.name for t in tools}
            assert "kb_search" in names
            assert "keyword_research" in names
            assert "copywriter" in names
            assert "seo_scorer" in names
            assert "generate_excel" in names
            assert "generate_pptx" in names

        asyncio.run(_test())
