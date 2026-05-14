# SEO AI Agent

Autonomous AI Agent for end-to-end SEO workflows — keyword research, SERP analysis, competitor auditing, content writing, on-page optimization, rank tracking, and performance reporting. Powered by LLM tool-calling with long-term memory, a self-building knowledge base, Auto-RAG, and multi-format export.

**22 tools · 12 tests · LanceDB vector store · Docker-ready · Python 3.12+**

## Architecture

```
User (CLI / Web UI / MCP / API)
         │
    ┌────▼────────────────────────────┐
    │  Middleware: CORS → Rate → Auth │
    └────┬────────────────────────────┘
         │
    ┌────▼────────────────────────────┐
    │     FastAPI (main.py)           │
    │  • REST API (8 route groups)    │
    │  • SSE streaming                │
    │  • Skill commands (/pptx /excel)│
    └────┬────────────────────────────┘
         │
    ┌────▼────────────────────────────┐
    │     Agent Orchestrator          │
    │  • Tool-calling loop            │
    │  • Auto-RAG (KB → context)      │
    │  • Progress callbacks (SSE)     │
    │  • Auto multi-format export     │
    └──┬──┬──────┬──┬─────────────────┘
       │  │      │  │
  ┌────▼┐ │ ┌────▼─▼──────┐  ┌──────────────┐
  │ KB  │ │ │Tool Registry│  │   Memory     │
  │4工具│ │ │  22 Tools   │  │ SQLite+WAL   │
  └──┬──┘ │ └─────┬───────┘  └──────┬───────┘
     │    │       │                 │
  ┌──▼────▼───────▼─────────────────▼───────┐
  │          Storage Layer                   │
  │  LanceDB (ANN vector) + SQLite (WAL)    │
  │  Embedding cache · Profile cache        │
  └─────────────────────────────────────────┘
```

### Why no heavy frameworks?

SEO workflows are linear (research → write → publish → track). A bare tool-calling loop (~200 lines) is simpler, more debuggable, and avoids LangChain/CrewAI lock-in.

## Features

### Agent Core
- **Tool-Calling Loop**: LLM selects tools based on task context, executes, feeds results back
- **Auto-RAG**: Automatically searches KB before every task, injects relevant context into system prompt
- **Auto-Ingest**: Tool outputs (SERP analyses, keyword reports, content) auto-stored in KB
- **Progress Callbacks**: SSE streaming with per-step events (start / thinking / tool_result / done)
- **Final Synthesis**: LLM synthesizes comprehensive answer from all tool results
- **Multi-format Auto-export**: Every final output saves as MD + DOCX + PPTX + XLSX simultaneously

### Knowledge Base (★ Differentiator)
- **Zero-config ingestion**: Drop PDF, DOCX, HTML, MD, TXT, URLs — auto-parsed, chunked, embedded, indexed
- **SHA256 deduplication**: Same file never stored twice
- **Auto-tagging**: LLM-powered document classification
- **Per-project isolation**: Each project has independent KB
- **LanceDB backend**: Pure Python vector DB with ANN indexing, Python 3.14+ compatible
- **Graceful fallback**: In-memory vector store when LanceDB unavailable

### Long-Term Memory
- **Structured (SQLite + WAL)**: Keywords, articles, step logs, user profiles, projects, KB file registry
- **Semantic (LanceDB)**: Article embeddings for "have I written about this?" dedup
- **User Profile**: Remembers tone, audience, language, taboo topics across sessions
- **Global connection pool**: Single SQLAlchemy engine with pool_size=5, WAL journal mode

### Production Features
- **Health/Readiness endpoints**: Dependency-aware probes for Docker/K8s
- **Rate limiting**: Token bucket per-endpoint (2/s agent, 5/s upload, 10/s reads)
- **API key auth**: Bearer token, dev-mode when unconfigured
- **Structured logging**: loguru — colored console + rotating JSON file
- **Path traversal protection**: File download/delete endpoints sanitized
- **CORS restricted**: Localhost origins only, specific methods/headers
- **Settings allowlist**: Only known env keys accepted, control chars stripped
- **Upload limits**: 50MB per file, path sanitization on filename + project_id

### 22 SEO Tools

| Category | Tools |
|----------|-------|
| **Knowledge Base** | `kb_search`, `kb_ingest`, `kb_list`, `kb_delete` |
| **Research** | `keyword_research`, `serp_analyzer`, `competitor_audit`, `semrush` |
| **Content** | `outline_generator`, `copywriter`, `fact_checker` |
| **Optimization** | `seo_scorer`, `readability`, `internal_linker`, `schema_markup`, `pagespeed` |
| **Analytics** | `rank_tracker`, `report_generator`, `gsc_data` |
| **Skills/Export** | `generate_pptx`, `generate_excel` |
| **Web** | `web_search` |

All tools have mock fallbacks — system works without API keys for demo/testing.

### Interfaces

| Interface | Description |
|-----------|-------------|
| **Web UI** | Full SPA — chat, KB management, project switching, file browser, settings, SSE streaming |
| **CLI** | `chat`, `run`, `kb ingest/list/search/delete` |
| **REST API** | 8 route groups, 30+ endpoints, SSE streaming, Swagger UI at `/docs` |
| **MCP Server** | IDE integration (Claude Code, VS Code, Cursor) |
| **Skills** | `/pptx`, `/excel`, `/browser` chat commands |

### LLM Support
- **DeepSeek** (OpenAI-compatible) — V4 Flash, default
- **Claude API** (Anthropic SDK) — Sonnet 4.6
- **Mock client** — Demo mode, simulates tool-calling workflow
- **Unified Protocol**: `LLMClient` Protocol enforces consistent `chat(messages, tools, system)` interface

## Quick Start

### 1. Install

```bash
git clone https://github.com/EricHong123/seo-ai-agent.git
cd seo-ai-agent
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env:
#   DEEPSEEK_API_KEY=sk-...       (required for LLM)
#   ANTHROPIC_API_KEY=sk-ant-...  (optional, Claude)
#   OPENAI_API_KEY=sk-...         (optional, embeddings)
#   API_KEY=your-secret           (optional, enables auth)
#   SEMRUSH_API_KEY=...           (optional, mock mode works)
```

### 3. Run

```bash
# Web UI (recommended)
PYTHONPATH=. python3 -m uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000

# CLI
PYTHONPATH=. python3 interfaces/cli.py chat

# Docker
docker compose up -d
```

## API Reference

### Health
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check with dependency probes |
| `GET` | `/ready` | Readiness probe (Kubernetes) |

### Agent
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/agent/run` | Optional | Run agent task (SSE streaming) |

### Projects
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/projects` | List projects |
| `POST` | `/projects` | Create project |
| `DELETE` | `/projects/{id}` | Delete project |

### Knowledge Base
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/kb/files` | List KB documents |
| `POST` | `/kb/ingest` | Ingest file by path/URL |
| `POST` | `/kb/upload` | Upload file directly |
| `GET` | `/kb/search` | Semantic search |
| `DELETE` | `/kb/files` | Delete document |

### Skills & Exports
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/skills/pptx` | Generate PowerPoint |
| `POST` | `/api/skills/excel` | Generate Excel |
| `POST` | `/api/skills/browser` | Browser screenshot |
| `GET` | `/api/skills/files` | List generated files |
| `GET` | `/api/skills/files/{name}` | Download file |
| `DELETE` | `/api/skills/files/{name}` | Delete file |

### Settings
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/settings` | Yes | Get config (keys masked) |
| `PUT` | `/settings` | Yes | Update config (allowlist) |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analytics/keywords` | Tracked keywords |
| `GET` | `/analytics/usage` | Token usage stats |
| `GET` | `/analytics/steps` | Agent step logs |

Full Swagger UI: `http://127.0.0.1:8000/docs`

## Project Structure

```
seo-ai-agent/
├── agent/                          # Orchestration
│   ├── orchestrator.py             # Main loop (+ progress callbacks)
│   ├── system_prompt.py            # SEO Specialist identity
│   ├── tool_registry.py            # Tool registration/execution
│   └── planner.py                  # Task planning + termination
│
├── tools/                          # 22 modular tools
│   ├── kb/                         # Knowledge base CRUD
│   ├── research/                   # keyword, SERP, competitor, SEMrush
│   ├── content/                    # outline, copywriter, fact_check
│   ├── optimization/               # SEO scorer, readability, linker, schema, PageSpeed
│   ├── analytics/                  # rank tracker, report gen, GSC
│   ├── skills/                     # PPTX/Excel generation, export utils
│   └── web/                        # web_search
│
├── knowledge_base/                 # Self-building KB
│   ├── kb_manager.py               # Ingest + search + delete
│   ├── embeddings.py               # OpenAI embeddings (cached)
│   ├── vector_store.py             # LanceDB (primary) + Simple fallback
│   ├── file_registry.py            # SQLAlchemy-backed file index
│   ├── auto_tag.py                 # LLM auto-tagging
│   └── ingestion/                  # PDF, DOCX, HTML, MD, TXT, URL parsers
│
├── memory/                         # Long-term memory
│   ├── structured/models.py        # Engine singleton + WAL + all tables
│   ├── structured/                 # Keywords, articles, step logs
│   ├── semantic/article_recall.py  # Article dedup (LanceDB)
│   └── user_profile.py             # User preferences (cached)
│
├── llm/                            # LLM abstraction
│   ├── protocol.py                 # LLMClient Protocol (enforced interface)
│   ├── claude_client.py            # Anthropic SDK
│   ├── deepseek_client.py          # DeepSeek (OpenAI-compatible)
│   └── mock_client.py              # Demo mode
│
├── interfaces/
│   ├── api/                        # FastAPI
│   │   ├── main.py                 # App entry + SSE + health
│   │   ├── middleware.py           # Rate limit + Auth
│   │   ├── schemas.py              # Pydantic models
│   │   └── routes/                 # 8 route groups
│   ├── cli.py                      # CLI (Click + Rich)
│   ├── web/index.html              # Web UI SPA
│   └── scheduler.py                # Weekly tasks
│
├── config/
│   ├── settings.py                 # Pydantic Settings (.env)
│   ├── cache.py                    # TTL cache layer
│   └── logger.py                   # loguru setup
│
├── mcp_server/                     # MCP IDE integration
├── tests/                          # pytest (12 tests)
├── requirements.txt
├── pyproject.toml
├── Dockerfile                      # 3.12-slim + healthcheck
├── docker-compose.yml
└── .env.example
```

## Design Principles

- **No heavy frameworks**: Bare tool-calling loop, transparent and debuggable
- **Unified interface**: `LLMClient` Protocol — all clients share the same contract
- **Graceful degradation**: LanceDB → in-memory, Embeddings → hash-based, LLM → Mock client
- **Immutable data**: All functions return new objects, never mutate in place
- **Self-describing tools**: Each tool carries name + description + JSON Schema
- **Project isolation**: KB, memory, and outputs scoped to projects
- **Secure by default**: CORS restricted, settings allowlisted, path traversal blocked
- **Production-ready**: Health probes, rate limiting, auth middleware, structured logging

## Configuration

All settings via `.env` or env vars:

| Variable | Description | Default |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `OPENAI_API_KEY` | OpenAI API key (embeddings) | — |
| `DEFAULT_LLM` | Provider: `claude` or `deepseek` | `deepseek` |
| `API_KEY` | Auth token (unset = dev mode) | — |
| `MAX_TOKENS` | Max response tokens | `8192` |
| `SEMRUSH_API_KEY` | SEMrush API key | — |
| `PAGESPEED_API_KEY` | PageSpeed Insights key | — |
| `GSC_SITE_URL` | Google Search Console site | — |
| `GOOGLE_CREDENTIALS_FILE` | GSC service account JSON | — |

## Testing

```bash
# Run all tests
PYTHONPATH=. python3 -m pytest tests/ -v

# 12 tests:
#   export_utils: MD, DOCX, PPTX, XLSX, all 4 formats, sections, tables (7)
#   orchestrator: simple task, keyword task, progress callback, context, tools (5)
```

## CI Health

```bash
# Quick verification
curl http://127.0.0.1:8000/health
# {"status":"ok","checks":{"database":true,"vector_store":true,"llm":true}}

curl http://127.0.0.1:8000/ready
# {"status":"ready"}
```

## License

MIT
