from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass
class ToolResult:
    call_id: str
    name: str
    output: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
