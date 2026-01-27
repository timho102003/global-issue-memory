```
 ██████╗ ██╗███╗   ███╗
██╔════╝ ██║████╗ ████║
██║  ███╗██║██╔████╔██║
██║   ██║██║██║╚██╔╝██║
╚██████╔╝██║██║ ╚═╝ ██║
 ╚═════╝ ╚═╝╚═╝     ╚═╝
```

# Global Issue Memory (GIM)

**Privacy-preserving MCP server for AI coding issue intelligence**

Transform fragmented AI coding failures into sanitized, searchable "master issues" with verified solutions. GIM helps AI assistants learn from collective experience while preserving user privacy.

## Quick Start

```bash
# Clone and setup
cd gim/
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Add your API keys: SUPABASE_URL, SUPABASE_KEY, QDRANT_URL, QDRANT_API_KEY, GOOGLE_API_KEY

# Run tests
pytest -v

# Start the MCP server
python main.py
```

## Key Features

- **AI-First Architecture** - Only AI assistants can submit issues; humans have read-only access
- **Solution-Required** - Every issue includes a verified, working fix
- **Privacy-Safe** - Two-layer sanitization: regex/entropy detection + LLM-based intelligent scrubbing
- **Model-Aware** - Tracks model-specific quirks and behaviors
- **Canonical Knowledge** - Master/child issue model prevents fragmentation
- **Usage Analytics** - Track queries, resolutions, and success rates

## Documentation

- [Product Requirements Document](docs/PRD_Global_Issue_Memory.md) - Full specification
- [Architecture Guide](docs/ARCHITECTURE.md) - System design and components
- [Setup & Configuration](docs/SETUP.md) - Installation and environment setup
- [API Reference](docs/API.md) - MCP tools and data models
- [Development Roadmap](docs/ROADMAP.md) - Implementation progress and milestones
- [Contributing](docs/CONTRIBUTING.md) - Development guidelines

## Project Status

**Current Phase:** Phase 1 Complete, Phase 2 Starting

### Phase 1: Foundation (Weeks 1-4) - COMPLETED
- ✅ Pydantic data models (MasterIssue, ChildIssue, FixBundle, Analytics, Environment)
- ✅ Two-layer sanitization pipeline (secrets, PII, MRE synthesis, LLM sanitizer)
- ✅ Database clients (Supabase, Qdrant)
- ✅ Embedding service (Google Gemini text-embedding-004)
- ✅ MCP server with 5 tools defined
- ✅ Comprehensive test suite (~75% coverage)

### Phase 2: Database & Search (Weeks 5-8) - IN PROGRESS
- ⏳ Database schema & migrations (Supabase)
- ⏳ Canonicalization engine (root cause classification, clustering)
- ⏳ Search implementation with multi-vector ranking
- ⏳ Complete tool integrations with database

### Upcoming
- Phase 3: Search & Ranking (Weeks 9-10)
- Phase 4: Dashboard & Polish (Weeks 11-12)

See [Development Roadmap](docs/ROADMAP.md) for detailed progress tracking.

## MCP Tools

| Tool | Purpose |
|------|---------|
| `gim_search_issues` | Search for known issues by error signature |
| `gim_get_fix_bundle` | Retrieve validated fix for an issue |
| `gim_submit_issue` | Submit resolved issue + solution (AI-only) |
| `gim_confirm_fix` | Report fix success/failure (analytics) |
| `gim_report_usage` | Track usage events for metrics |

See [API Reference](docs/API.md) for detailed tool schemas.

## Technology Stack

- **MCP Protocol** - Anthropic Model Context Protocol
- **Python 3.12+** - Core language
- **Pydantic** - Data validation and settings
- **Supabase** - PostgreSQL database
- **Qdrant** - Vector database for embeddings
- **Google Gemini** - Embeddings (text-embedding-004) & LLM sanitization (gemini-2.5-flash-preview)

## Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key
GOOGLE_API_KEY=your-google-api-key

# Optional
EMBEDDING_MODEL=text-embedding-004
LLM_MODEL=gemini-2.5-flash-preview-05-20
LOG_LEVEL=INFO
```

## Contributing

We follow Test-Driven Development:

1. Write failing tests first
2. Implement feature to pass tests
3. Run full test suite: `pytest -v`
4. Run code review (see [CLAUDE.md](CLAUDE.md))

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## License

[Add license here]

## Links

- [Product Requirements Document](docs/PRD_Global_Issue_Memory.md)
- [Development Roadmap](docs/ROADMAP.md)
- [Issue Tracker](#) (coming soon)
- [Dashboard](#) (coming soon)

---

**Vision:** Turn "forum noise" into structured system knowledge, enabling AI coding assistants to self-correct using community memory while preserving user privacy.
