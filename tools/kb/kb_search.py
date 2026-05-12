from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "kb_search",
    "description": "Search your knowledge base for relevant documents, brand guides, competitor analyses, or historical articles. Call this whenever you're unsure if you have relevant stored knowledge, or when the user references something you should already know about.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language search query"},
            "top_k": {"type": "integer", "description": "Number of results to return", "default": 5},
            "filter_type": {
                "type": "string",
                "enum": ["all", "article", "brand_guide", "report", "competitor"],
                "description": "Filter by document type",
                "default": "all",
            },
        },
        "required": ["query"],
    },
}


def make_tool(kb_manager) -> ToolDef:
    async def handler(query: str, top_k: int = 5, filter_type: str = "all") -> str:
        ftype = None if filter_type == "all" else filter_type
        results = await kb_manager.search(query, top_k=top_k, file_type_filter=ftype)
        if not results:
            return "知识库中没有找到相关文档。"

        lines: list[str] = [f"从知识库找到 {len(results)} 个相关片段:"]
        for i, r in enumerate(results):
            src = r.get("metadata", {}).get("filename", "unknown")
            score = r.get("score", 0)
            content = r.get("content", "")[:300]
            lines.append(f"\n--- [{i+1}] {src} (相关性: {score:.0%}) ---")
            lines.append(content)

        return "\n".join(lines)

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
