from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable, Coroutine

from llm.types import Message, ToolCall

ToolSchema = dict[str, Any]
ToolHandler = Callable[..., Coroutine[Any, Any, str]]


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler | None = None

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters.get("properties", {}),
                    "required": self.parameters.get("required", []),
                },
            },
        }

    def to_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters.get("properties", {}),
                "required": self.parameters.get("required", []),
            },
        }


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"
    usage: dict[str, int] = field(default_factory=dict)
