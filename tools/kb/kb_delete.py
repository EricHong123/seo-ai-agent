from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "kb_delete",
    "description": "Delete a document from your knowledge base. Use this when the user tells you to forget something or remove outdated information.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "The filename to delete (partial match supported)"},
        },
        "required": ["filename"],
    },
}


def make_tool(kb_manager) -> ToolDef:
    async def handler(filename: str) -> str:
        records = await kb_manager.list_files()
        match = None
        for r in records:
            if filename.lower() in r["filename"].lower():
                match = r
                break

        if not match:
            return f"未找到匹配 '{filename}' 的文档。"

        await kb_manager.delete_file(match["id"])
        return f"✓ 已从知识库删除: {match['filename']}"

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
