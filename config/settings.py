from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # LLM
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    openai_api_key: str = ""  # for embeddings
    default_llm: str = "claude"  # "claude" | "deepseek"
    llm_model: str = "claude-sonnet-4-6-20250514"
    max_tokens: int = 8192

    # Embeddings
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # Knowledge Base
    kb_dir: Path = Path("data/knowledge_base")
    kb_chunk_size: int = 500
    kb_chunk_overlap: int = 50
    kb_default_top_k: int = 5

    # Memory
    db_url: str = "sqlite+aiosqlite:///data/memory.db"

    # ChromaDB
    chroma_persist_dir: Path = Path("data/chroma")

    # Third-party SEO APIs
    google_credentials_file: str = ""  # Path to GSC service account JSON
    gsc_site_url: str = ""  # e.g. "https://www.example.com" or "sc_domain:example.com"
    pagespeed_api_key: str = ""  # Google PageSpeed Insights API key (optional, has free quota)
    semrush_api_key: str = ""

    # MCP
    mcp_server_name: str = "seo-ai-agent"

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_key: str = ""  # If set, protects /api/agent/run, /settings, /kb/upload

    # Project
    project_root: Path = Path(__file__).parent.parent


settings = Settings()
