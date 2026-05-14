import json
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam, ToolParam

from config.settings import settings
from llm.base import LLMResponse, ToolDef
from llm.types import Message, ToolCall
from llm.protocol import LLMClient


class ClaudeClient(LLMClient):
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model

    def _build_tools(self, tools: list[ToolDef]) -> list[ToolParam]:
        return [t.to_anthropic_schema() for t in tools]

    def _build_messages(self, messages: list[Message]) -> list[MessageParam]:
        result: list[MessageParam] = []
        for m in messages:
            if m.role == "system":
                result.append({"role": "user", "content": m.content})
            elif m.role == "user":
                result.append({"role": "user", "content": m.content})
            elif m.role == "assistant":
                content: list[dict] = []
                if m.content:
                    content.append({"type": "text", "text": m.content})
                if m.tool_calls:
                    for tc in m.tool_calls:
                        content.append({
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.args,
                        })
                result.append({"role": "assistant", "content": content})
            elif m.role == "tool":
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.tool_call_id or "",
                        "content": m.content,
                    }],
                })
        return result

    def _parse_response(self, response) -> LLMResponse:
        tool_calls: list[ToolCall] = []
        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    args=block.input if isinstance(block.input, dict) else {},
                ))

        usage = {
            "input_tokens": response.usage.input_tokens if response.usage else 0,
            "output_tokens": response.usage.output_tokens if response.usage else 0,
        }

        return LLMResponse(
            content=text,
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "end_turn",
            usage=usage,
        )

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": settings.max_tokens,
            "messages": self._build_messages(messages),
        }
        if tools:
            kwargs["tools"] = self._build_tools(tools)
        if system:
            kwargs["system"] = system

        response = await self.client.messages.create(**kwargs)
        return self._parse_response(response)
