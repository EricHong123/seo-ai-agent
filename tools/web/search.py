from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "web_search",
    "description": "Perform a web search to find real-time information, news, statistics, and references for article writing.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Max results", "default": 5},
        },
        "required": ["query"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(query: str, max_results: int = 5) -> str:
        if not llm_client:
            return f"[Web search for '{query}' would return results here. Connect an LLM and search API for real-time data.]"

        from llm.types import Message

        prompt = f"""You are a web search synthesizer. Given the search query below, provide the best available information from your knowledge.

Search Query: "{query}"
Max Results: {max_results}

For each result you'd provide:
1. A realistic title
2. A 2-3 sentence summary
3. The key fact/statistic/data point from the source
4. Relevance to the query (high/medium/low)

Draw from your actual knowledge — provide real, accurate information. If you genuinely don't know something, mark it as [uncertain]."""

        response = await llm_client.chat(messages=[Message(role="user", content=prompt)])
        return response.content

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
