# SEO AI Agent

An autonomous AI Agent for end-to-end SEO workflows — keyword research, SERP analysis, competitor auditing, content writing, on-page optimization, rank tracking, and performance reporting. Powered by LLM tool-calling with long-term memory, a self-building knowledge base, and Auto-RAG.

**79 Python files · 4,430 lines · Built without heavy agent frameworks**

## Architecture

```
User (CLI / Web UI / MCP)
         │
         ▼
┌─────────────────────┐
│  Agent Orchestrator │  ← Tool-calling loop + Auto-RAG
│  • LLM 推理选 Tool   │
│  • 自动知识库检索     │
│  • 结果自动入库       │
└──┬────┬─────────┬───┘
   │    │         │
┌──▼┐ ┌─▼────┐ ┌─▼──────────┐
│KB │ │Memory│ │Tool Registry│
│知识库│ │长期记忆│ │15+ Tools    │
└──┬┘ └──┬───┘ └──┬─────────┘
   │     │        │
   │  ┌──▼────────▼──────────┐
   │  │  SQLite + ChromaDB   │
   │  │  结构化 + 语义双存储   │
   │  └──────────────────────┘
   │
┌──▼─────────────────────────┐
│     Tool Modules (15+)      │
│  KB │ Research │ Content    │
│  Optimization │ Analytics  │
│  Publishing │ Web          │
└────────────────────────────┘
```

### Why no LangChain / CrewAI / AutoGen?

SEO workflows are inherently linear (research → write → publish → track), not complex multi-agent debate scenarios. A bare tool-calling loop is simpler, more debuggable, and avoids framework lock-in. The orchestrator is ~200 lines of Python.

## Features

### Core Agent
- **Tool-Calling Loop**: LLM decides which tool to invoke based on task context
- **Auto-RAG**: Automatically searches the knowledge base before every task and injects relevant context into the system prompt
- **Auto-Ingest**: Tool outputs (SERP analyses, competitor audits, keyword reports) are automatically stored in the knowledge base
- **Final Synthesis**: After tool execution, the LLM synthesizes a comprehensive final answer from all collected data

### Knowledge Base (★ Core Differentiator)
- **Zero-config ingestion**: Drop files in conversation — PDF, DOCX, HTML, Markdown, TXT, URLs — auto-parsed, chunked, embedded, and indexed
- **SHA256 deduplication**: Same file never stored twice
- **Auto-tagging**: LLM-powered document classification (brand_guide, competitor_analysis, keyword_report, etc.)
- **Per-project isolation**: Each project has an independent knowledge base
- **Graceful degradation**: Falls back to in-memory vector store when ChromaDB is unavailable (Python 3.14+ compatible)

### Long-Term Memory
- **Structured (SQLite)**: Keyword rankings history, article versions, step execution logs, user profiles, project metadata
- **Semantic (ChromaDB)**: Article embeddings for "have I written about this before?" deduplication
- **User Profile**: Remembers preferred tone, target audience, language, and taboo topics across sessions

### SEO Tools (15+)

| Category | Tools |
|----------|-------|
| **Knowledge Base** | `kb_search`, `kb_ingest`, `kb_list`, `kb_delete` |
| **Research** | `keyword_research`, `serp_analyzer`, `competitor_audit` |
| **Content** | `outline_generator`, `copywriter`, `fact_checker` |
| **Optimization** | `seo_scorer`, `readability`, `internal_linker`, `schema_markup` |
| **Analytics** | `rank_tracker`, `report_generator` |
| **Web** | `web_search` |

Every tool has a mock/fallback implementation — the system works without API keys for demo and testing.

### Interfaces

| Interface | Description |
|-----------|-------------|
| **Web UI** | Full SPA with chat, KB management, project switching, SSE streaming |
| **CLI** | `chat` (interactive), `run` (single task), `kb` (ingest/list/search/delete) |
| **REST API** | FastAPI with 15+ endpoints, SSE streaming for agent tasks |
| **MCP Server** | IDE integration — use from Claude Code, VS Code, Cursor |

### LLM Support
- **Claude API** (Anthropic SDK) — Sonnet 4.6 for best long-form content
- **DeepSeek API** (OpenAI-compatible) — DeepSeek V4 Flash for Chinese/domestic use
- **Mock client** — Demo mode without any API key, simulates tool-calling workflow
- Automatic fallback: no API key → mock mode

## Quick Start

### 1. Install

```bash
git clone https://github.com/ericzxb/seo-ai-agent.git
cd seo-ai-agent
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API key:
#   DEEPSEEK_API_KEY=sk-...   (for DeepSeek)
#   ANTHROPIC_API_KEY=sk-ant-...  (for Claude)
#   DEFAULT_LLM=deepseek       (or "claude")
```

### 3. Run

**Web UI** (recommended):
```bash
PYTHONPATH=. python3 -m uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000
```

**CLI**:
```bash
# Interactive chat
PYTHONPATH=. python3 interfaces/cli.py chat

# Single task
PYTHONPATH=. python3 interfaces/cli.py run "分析 best standing desk 2026 的 SERP"

# Knowledge base management
PYTHONPATH=. python3 interfaces/cli.py kb ingest brand-guide.pdf
PYTHONPATH=. python3 interfaces/cli.py kb list
PYTHONPATH=. python3 interfaces/cli.py kb search "brand guidelines"
```

**Docker**:
```bash
docker compose up -d
```

## Project Structure

```
seo-ai-agent/
├── agent/                          # Agent orchestration
│   ├── orchestrator.py             # Main loop: Auto-RAG → reasoning → tools → synthesize
│   ├── system_prompt.py            # Dynamic prompt with persona + memory + KB injection
│   ├── tool_registry.py            # Tool registration and execution
│   └── planner.py                  # Task planning and termination logic
│
├── tools/                          # 15+ modular SEO tools
│   ├── kb/                         # kb_search, kb_ingest, kb_list, kb_delete
│   ├── research/                   # keyword_research, serp_analyzer, competitor_audit
│   ├── content/                    # outline_generator, copywriter, fact_checker
│   ├── optimization/               # seo_scorer, readability, internal_linker, schema_markup
│   ├── analytics/                  # rank_tracker, report_generator
│   └── web/                        # web_search
│
├── knowledge_base/                 # Self-building knowledge base
│   ├── kb_manager.py               # Ingest + search + delete orchestrator
│   ├── embeddings.py               # OpenAI embeddings with hash-based fallback
│   ├── vector_store.py             # ChromaDB with in-memory fallback
│   ├── file_registry.py            # SQLite file registry with SHA256 dedup
│   ├── auto_tag.py                 # LLM-powered document auto-tagging
│   └── ingestion/                  # Parsers: PDF, DOCX, HTML, Markdown, TXT, URL
│
├── memory/                         # Long-term memory system
│   ├── structured/                 # SQLite: projects, keywords, articles, step_logs
│   └── semantic/                   # ChromaDB: article embeddings for dedup
│
├── llm/                            # LLM clients
│   ├── claude_client.py            # Anthropic SDK
│   ├── deepseek_client.py          # DeepSeek (OpenAI-compatible)
│   └── mock_client.py              # Demo mode — no API key needed
│
├── interfaces/                     # User interfaces
│   ├── cli.py                      # CLI: chat, run, kb commands
│   ├── api/                        # FastAPI REST API + SSE streaming
│   │   ├── main.py                 # App entry + /api/agent/run SSE endpoint
│   │   ├── schemas.py              # Pydantic models
│   │   └── routes/                 # projects, tasks, articles, analytics, kb
│   ├── web/                        # Web UI (single-page HTML/CSS/JS)
│   └── scheduler.py                # Background: weekly rank tracking + reports
│
├── mcp_server/                     # MCP IDE integration
│   ├── server.py                   # FastMCP server (15 tools + 4 resources + 3 prompts)
│   ├── resources.py                # KB overview, keywords, articles, user profile
│   └── prompts.py                  # seo-article, seo-audit, keyword-discovery templates
│
├── config/
│   └── settings.py                 # Pydantic Settings (.env driven)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## API Endpoints

### Agent
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agent/run` | Run agent task (SSE streaming) |

### Projects
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/projects` | List all projects |
| `POST` | `/projects` | Create project |
| `GET` | `/projects/{id}` | Get project details |
| `DELETE` | `/projects/{id}` | Delete project |

### Knowledge Base
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/kb/files` | List KB documents |
| `POST` | `/kb/ingest` | Ingest file or URL |
| `GET` | `/kb/search` | Semantic search |
| `DELETE` | `/kb/files` | Delete document |

### Articles
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/articles` | List articles (filter by project/keyword) |
| `POST` | `/articles` | Save article |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analytics/keywords` | Tracked keywords |
| `GET` | `/analytics/keywords/{kw}/history` | Keyword rank history |
| `GET` | `/analytics/usage` | Token usage stats |
| `GET` | `/analytics/steps` | Agent step logs |

API documentation available at `/docs` (Swagger UI) and `/redoc`.

## Design Principles

- **No heavy frameworks**: Bare tool-calling loop. The orchestrator is transparent and debuggable.
- **Graceful degradation**: Every component has a fallback — ChromaDB → in-memory, OpenAI embeddings → hash-based, LLM → mock client.
- **Immutable data**: All functions return new objects, never mutate in place.
- **Self-describing tools**: Each tool carries its own name, description, and JSON Schema. The LLM reads descriptions to decide which tool fits.
- **Project isolation**: Knowledge base, memory, and tool outputs are scoped to projects.
- **Minimalist UI**: White/black/gray palette, fine lines, no shadows or gradients. Content-first.

## Configuration

All settings via `.env` or environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `OPENAI_API_KEY` | OpenAI API key (embeddings) | — |
| `DEFAULT_LLM` | LLM provider: `claude` or `deepseek` | `claude` |
| `MAX_TOKENS` | Max response tokens | `8192` |
| `DB_URL` | SQLite database URL | `sqlite+aiosqlite:///data/memory.db` |
| `CHROMA_PERSIST_DIR` | ChromaDB persistence directory | `data/chroma` |

## Verification

```bash
# 1. Health check
curl http://127.0.0.1:8000/health

# 2. Ingest a file to KB
curl -X POST http://127.0.0.1:8000/kb/ingest \
  -H 'Content-Type: application/json' \
  -d '{"path": "/path/to/brand-guide.pdf", "project_id": "default"}'

# 3. Run an agent task (SSE stream)
curl -X POST http://127.0.0.1:8000/api/agent/run \
  -H 'Content-Type: application/json' \
  -d '{"task": "分析 best standing desk 2026 的 SERP", "project_id": "default"}'

# 4. CLI demo mode (no API key)
PYTHONPATH=. python3 interfaces/cli.py run --mock "分析 best standing desk 的 SERP"

# 5. All syntax checks pass
find . -name "*.py" | xargs python3 -c "import py_compile; import sys; [py_compile.compile(f.strip(), doraise=True) for f in sys.stdin]"
```

## License

MIT
