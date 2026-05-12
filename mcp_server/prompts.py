"""MCP Prompts: reusable prompt templates for common SEO tasks."""

MCP_PROMPTS = {
    "seo-article": {
        "description": "Write a complete SEO-optimized article",
        "arguments": [
            {"name": "topic", "description": "Article topic", "required": True},
            {"name": "keywords", "description": "Comma-separated target keywords", "required": True},
            {"name": "tone", "description": "Writing tone", "required": False},
        ],
        "template": """Write a comprehensive SEO-optimized article about {topic}.

Target Keywords: {keywords}
Tone: {tone or 'professional'}
Target Length: 2000-2500 words

Workflow:
1. Use kb_search to check for relevant brand guidelines and competitor data
2. Use keyword_research to validate keywords and find related terms
3. Use serp_analyzer to see what's currently ranking
4. Use competitor_audit to identify content gaps
5. Use outline_generator to create a structured outline
6. Write the article using copywriter
7. Use seo_scorer to audit and improve
8. Use fact_checker to verify claims
9. Use kb_ingest to store the final article

Follow all brand guidelines found in the knowledge base.""",
    },
    "seo-audit": {
        "description": "Perform a complete SEO audit of content",
        "arguments": [
            {"name": "content", "description": "Content to audit", "required": True},
            {"name": "keyword", "description": "Primary target keyword", "required": True},
        ],
        "template": """Audit this content for SEO quality:

Target Keyword: {keyword}

Content:
{content}

Run through:
1. seo_scorer — overall SEO score
2. readability — readability analysis
3. internal_linker — linking opportunities
4. schema_markup — structured data recommendations
5. Provide prioritized fixes.""",
    },
    "keyword-discovery": {
        "description": "Discover and analyze keywords for a topic",
        "arguments": [
            {"name": "topic", "description": "Topic or niche to explore", "required": True},
            {"name": "market", "description": "Target market (us/cn)", "required": False},
        ],
        "template": """Research keywords for: {topic}
Market: {market or 'us'}

Use keyword_research to find primary and long-tail keywords.
Use serp_analyzer on the top 3 keywords to understand the competitive landscape.
Provide a prioritized keyword list with volume, difficulty, and intent.""",
    },
}
