from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "kb_ingest",
    "description": "Store important information into your knowledge base. Use this when the user explicitly tells you to remember something, or when you generate valuable content (article, analysis) worth keeping for future reference.",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The text content to store"},
            "filename": {"type": "string", "description": "Descriptive name for this piece of knowledge"},
            "source": {"type": "string", "description": "Where this came from", "default": "manual"},
        },
        "required": ["content", "filename"],
    },
}


def make_tool(kb_manager) -> ToolDef:
    async def handler(content: str, filename: str, source: str = "manual") -> str:
        result = await kb_manager.ingest_text(content, filename=filename, source=source)
        if result.get("status") == "duplicate":
            return f"⚠️ 内容重复，已跳过。（hash: {result.get('file_hash', '')[:12]}...）"

        return (
            f"✓ 已存入知识库。\n"
            f"  文件名: {filename}\n"
            f"  分块数: {result.get('chunk_count', 0)}\n"
            f"  Token 数: {result.get('token_count', 0)}\n"
            f"  标签: {', '.join(result.get('tags', []))}"
        )

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
