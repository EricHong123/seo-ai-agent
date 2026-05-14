from llm.base import LLMResponse, ToolDef
from llm.types import Message
from llm.claude_client import ClaudeClient
from llm.deepseek_client import DeepSeekClient
from llm.mock_client import MockLLMClient
from config.settings import settings


async def get_llm_client(mock: bool = False):
    if mock:
        return MockLLMClient()
    if settings.default_llm == "deepseek":
        if not settings.deepseek_api_key:
            return MockLLMClient()
        return DeepSeekClient()
    if not settings.anthropic_api_key:
        return MockLLMClient()
    return ClaudeClient()


from llm.protocol import LLMClient  # Re-export the Protocol
