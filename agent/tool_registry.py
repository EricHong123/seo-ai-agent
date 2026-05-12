from typing import Any

from llm.base import ToolDef


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDef] = {}

    def register(self, tool: ToolDef):
        self._tools[tool.name] = tool

    def register_many(self, tools: list[ToolDef]):
        for t in tools:
            self.register(t)

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDef]:
        return list(self._tools.values())

    def list_schemas(self) -> list[dict]:
        return [t.to_anthropic_schema() for t in self._tools.values()]

    async def execute(self, name: str, args: dict[str, Any]) -> str:
        tool = self._tools.get(name)
        if not tool or not tool.handler:
            return f"Error: tool '{name}' not found or has no handler"
        try:
            return await tool.handler(**args)
        except Exception as e:
            return f"Error executing '{name}': {e}"


registry = ToolRegistry()
