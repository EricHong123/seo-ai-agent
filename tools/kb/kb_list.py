from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "kb_list",
    "description": "List all documents currently stored in your knowledge base. Use this to see what you already know before starting a new task.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}


def make_tool(kb_manager) -> ToolDef:
    async def handler() -> str:
        records = await kb_manager.list_files()
        if not records:
            return "知识库中还没有文档。"

        lines = [f"知识库共有 {len(records)} 个文档:"]
        for r in records:
            tags = r.get("tags", "[]")
            lines.append(f"  • {r['filename']} ({r['file_type']}) — {r['chunk_count']} chunks — {tags}")
        return "\n".join(lines)

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
