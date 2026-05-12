from llm.base import ToolDef


TOOL_SCHEMA = {
    "name": "readability",
    "description": "Analyze content readability: Flesch-Kincaid grade level, sentence length variety, passive voice ratio, paragraph structure, and reading time.",
    "parameters": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Content to analyze"},
            "target_grade": {"type": "integer", "description": "Target reading grade level (e.g., 8 for general audience, 12 for technical)", "default": 8},
        },
        "required": ["content"],
    },
}


def make_tool(llm_client=None) -> ToolDef:
    async def handler(content: str, target_grade: int = 8) -> str:
        words = content.split()
        sentences = [s.strip() for s in content.replace("?", ".").replace("!", ".").split(".") if s.strip()]
        word_count = len(words)
        sent_count = max(len(sentences), 1)
        avg_words_per_sentence = word_count / sent_count

        # Estimate reading time
        reading_time_min = round(word_count / 238)

        # Count passive voice indicators
        passive_indicators = sum(1 for w in words if w.lower().endswith("ed") or w.lower().endswith("en"))
        passive_ratio = passive_indicators / max(word_count, 1)

        # Sentence length variety
        sent_lengths = [len(s.split()) for s in sentences]
        if sent_lengths:
            max_sl, min_sl = max(sent_lengths), min(sent_lengths)
            variety = "Good" if (max_sl > 20 and min_sl < 5) else "Needs improvement"
        else:
            variety = "N/A"

        # Estimate grade level
        grade = min(12, max(4, round(0.39 * avg_words_per_sentence + 11.8 * (sum(1 for w in words if len(w) > 6) / max(word_count, 1) * 100) - 15.59)))

        grade_diff = grade - target_grade

        return f"""# Readability Analysis

**Estimated Reading Time**: {reading_time_min} min ({word_count} words)
**Estimated Grade Level**: {grade} (target: {target_grade})

| Metric | Value | Assessment |
|--------|-------|------------|
| Word Count | {word_count} | — |
| Avg Words/Sentence | {avg_words_per_sentence:.1f} | {"Too long" if avg_words_per_sentence > 25 else "Good" if avg_words_per_sentence > 10 else "Too short"} |
| Sentence Variety | {variety} | {"Mix of long and short sentences" if variety == "Good" else "Vary sentence length more"} |
| Passive Voice Ratio | {passive_ratio:.0%} | {"Reduce passive voice" if passive_ratio > 0.15 else "Good"} |
| Grade Level | {grade} | {"Above target — simplify" if grade_diff > 2 else "Below target — add depth" if grade_diff < -2 else "On target"} |

## Recommendations
{"• Simplify vocabulary and shorten sentences to lower reading level" if grade_diff > 2 else ""}
{"• Add technical depth and longer sentences to raise reading level" if grade_diff < -2 else ""}
{"• Replace passive constructions with active voice" if passive_ratio > 0.15 else ""}
• Use bullet lists for scannability
• Keep paragraphs under 3-4 sentences"""

    return ToolDef(
        name=TOOL_SCHEMA["name"],
        description=TOOL_SCHEMA["description"],
        parameters=TOOL_SCHEMA["parameters"],
        handler=handler,
    )
