from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "schema_markup",
    "description": "Generate Schema.org structured data (JSON-LD) for content. Supports Article, FAQ, HowTo, Product, Review, BreadcrumbList, and Organization schemas.",
    "parameters": {
        "type": "object",
        "properties": {
            "content_type": {"type": "string", "enum": ["Article", "FAQ", "HowTo", "Product", "Review", "BreadcrumbList"], "description": "Type of schema to generate"},
            "data": {"type": "object", "description": "Key data for the schema: title, description, author, datePublished, faq questions, steps, etc."},
        },
        "required": ["content_type", "data"],
    },
}

import json


SCHEMA_TEMPLATES = {
    "Article": lambda d: {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": d.get("title", ""),
        "description": d.get("description", ""),
        "author": {"@type": "Person", "name": d.get("author", "Author Name")},
        "datePublished": d.get("datePublished", "2026-01-01"),
        "dateModified": d.get("dateModified", d.get("datePublished", "2026-01-01")),
        "mainEntityOfPage": {"@type": "WebPage", "@id": d.get("url", "")},
        "publisher": {"@type": "Organization", "name": d.get("publisher", "Site Name")},
    },
    "FAQ": lambda d: {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q.get("question", ""),
             "acceptedAnswer": {"@type": "Answer", "text": q.get("answer", "")}}
            for q in d.get("faqs", [])
        ],
    },
    "HowTo": lambda d: {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": d.get("title", ""),
        "description": d.get("description", ""),
        "step": [
            {"@type": "HowToStep", "name": s.get("name", f"Step {i+1}"),
             "text": s.get("text", "")}
            for i, s in enumerate(d.get("steps", []))
        ],
    },
    "BreadcrumbList": lambda d: {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i+1, "name": item.get("name", ""),
             "item": item.get("url", "")}
            for i, item in enumerate(d.get("items", []))
        ],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(content_type: str, data: dict) -> str:
        template_fn = SCHEMA_TEMPLATES.get(content_type)
        if not template_fn:
            return f"Unsupported schema type: {content_type}. Supported: {', '.join(SCHEMA_TEMPLATES.keys())}"

        schema = template_fn(data)
        json_ld = json.dumps(schema, indent=2, ensure_ascii=False)

        return f"""```html
<script type="application/ld+json">
{json_ld}
</script>
```

## Testing
Validate this markup at: https://validator.schema.org/
Test rich results at: https://search.google.com/test/rich-results"""

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
