"""Bridge: converts agent ToolDefs into MCP tools that wrap the same handlers."""

import json
from llm.base import ToolDef


def build_mcp_tools(registry) -> list[dict]:
    """Convert all registered tools to MCP-compatible tool schemas with handler wrappers."""
    tools = []
    for tool_def in registry.list_tools():
        if not tool_def.handler:
            continue

        # Capture tool_def in closure
        handler = tool_def.handler

        async def mcp_handler(**kwargs):
            result = await handler(**kwargs)
            return result

        tools.append({
            "name": tool_def.name,
            "description": tool_def.description,
            "inputSchema": {
                "type": "object",
                "properties": tool_def.parameters.get("properties", {}),
                "required": tool_def.parameters.get("required", []),
            },
            "handler": mcp_handler,
        })
    return tools
