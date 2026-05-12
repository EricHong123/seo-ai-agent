import uuid


def generate_task_id() -> str:
    return str(uuid.uuid4())[:8]


def is_terminal(messages: list, llm_response) -> bool:
    """Check if the agent should stop: no more tool calls needed."""
    if not llm_response.tool_calls:
        return llm_response.stop_reason == "end_turn"

    if llm_response.stop_reason == "end_turn":
        return True

    return False


def extract_final_output(messages: list) -> str:
    """Extract the final text output from the message history."""
    for m in reversed(messages):
        if m.role == "assistant" and m.content:
            return m.content
    return "No output generated."
