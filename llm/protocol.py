"""LLM client Protocol — enforces consistent interface across all providers."""

from typing import Protocol, runtime_checkable
from llm.base import LLMResponse, ToolDef
from llm.types import Message


@runtime_checkable
class LLMClient(Protocol):
    """Protocol all LLM clients must implement.

    This replaces the informal union type ClaudeClient | DeepSeekClient | MockLLMClient.
    All clients MUST accept these parameters and return LLMResponse.
    """

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        """Send a chat request and return the response.

        Args:
            messages: Conversation history (user, assistant, tool roles).
            tools: Available tool definitions. None or empty = no tools.
            system: System prompt. If None, no system message is sent.

        Returns:
            LLMResponse with content, optional tool_calls, stop_reason, and usage.
        """
        ...
