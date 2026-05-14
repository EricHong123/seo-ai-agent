import json
import httpx

from config.settings import settings
from llm.base import LLMResponse, ToolDef
from llm.types import Message, ToolCall
from llm.protocol import LLMClient


class DeepSeekClient(LLMClient):
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"

    def _build_tools(self, tools: list[ToolDef]) -> list[dict]:
        return [t.to_openai_schema() for t in tools]

    def _build_messages(self, messages: list[Message]) -> list[dict]:
        result: list[dict] = []
        for m in messages:
            if m.role == "system":
                result.append({"role": "system", "content": m.content})
            elif m.role == "user":
                result.append({"role": "user", "content": m.content})
            elif m.role == "assistant":
                msg: dict = {"role": "assistant", "content": m.content or None}
                if m.tool_calls:
                    msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.args, ensure_ascii=False),
                            },
                        }
                        for tc in m.tool_calls
                    ]
                result.append(msg)
            elif m.role == "tool":
                result.append({
                    "role": "tool",
                    "tool_call_id": m.tool_call_id or "",
                    "content": m.content,
                })
        return result

    def _parse_response(self, data: dict) -> LLMResponse:
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "") or ""

        tool_calls: list[ToolCall] = []
        for tc in message.get("tool_calls", []) or []:
            func = tc.get("function", {})
            args = {}
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                pass
            tool_calls.append(ToolCall(
                id=tc.get("id", ""),
                name=func.get("name", ""),
                args=args,
            ))

        usage = data.get("usage", {})
        return LLMResponse(
            content=text,
            tool_calls=tool_calls,
            stop_reason=choice.get("finish_reason", "stop"),
            usage={
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            },
        )

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        system: str | None = None,
    ) -> LLMResponse:
        msgs = self._build_messages(messages)
        if system:
            msgs.insert(0, {"role": "system", "content": system})

        body: dict = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": settings.max_tokens,
        }
        if tools:
            body["tools"] = self._build_tools(tools)

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            if response.status_code >= 400:
                raise Exception(f"DeepSeek API error ({response.status_code}): {response.text[:500]}")
            return self._parse_response(response.json())
