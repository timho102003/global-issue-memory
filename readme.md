```
 ██████╗ ██╗███╗   ███╗
██╔════╝ ██║████╗ ████║
██║  ███╗██║██╔████╔██║
██║   ██║██║██║╚██╔╝██║
╚██████╔╝██║██║ ╚═╝ ██║
 ╚═════╝ ╚═╝╚═╝     ╚═╝
```

# Global Issue Memory (GIM)

**Stack Overflow for the AI coding era — built into your workflow, not a tab away**

---

## Problem 01: Your AI Coding Assistant Is Burning Tokens

Every time your AI assistant hits an error, it goes into a loop: searching the web, reading outdated docs, trying random fixes. Sound familiar?

**For engineers:** You can quickly guide the AI back on track — but that's still time and focus you're spending on issues someone else already solved.

**For vibe coders:** You let the AI run autonomously, shipping features while you focus elsewhere. But when it hits a bug? It spirals. Token after token wasted on trial-and-error fixes.

**The real cost isn't just tokens — it's momentum.**

---

## Problem 02: A Bloated Context Window Makes Your AI Dumber

Here's what most vibe coders don't realize: **context window size directly affects AI coding performance.**

Every web search result, every failed attempt, every stack trace your AI reads — it all piles into the context window. And as that window fills up:

| Context State | What Happens |
|---------------|--------------|
| **Fresh** (2K tokens) | Sharp, fast, follows instructions precisely |
| **Moderate** (20K tokens) | Still good, but starting to miss details |
| **Bloated** (50K+ tokens) | Slow, confused, forgets earlier instructions |
| **Maxed out** | Drops critical context, hallucinates, fails |

**The compounding problem:**

```
Bug #1 → AI debugs for 10 min → +15K tokens of noise
Bug #2 → AI now slower, debugs for 15 min → +25K tokens
Bug #3 → AI barely functional, spirals → session ruined
```

**For vibe coders running AI autonomously:** This is devastating. Your coding session starts strong, but after a few bug-fixing spirals, the AI is operating at a fraction of its potential — burning through your budget while delivering worse results.

**The solution isn't a bigger context window. It's keeping it clean.**

---

## The Solution: Collective Memory for AI Coding

GIM is a **community-powered issue memory** that plugs directly into your AI coding workflow via MCP (Model Context Protocol).

**How GIM solves Problem 01 (Token Waste):**
- **Instant lookup** — Get verified fixes in one API call, not 50 web searches
- **Skip the spiral** — Solutions that actually worked, not outdated Stack Overflow threads
- **No more trial-and-error** — Your AI applies the fix directly

**How GIM solves Problem 02 (Context Bloat):**
- **Minimal context footprint** — One clean answer vs. pages of search results
- **No debugging noise** — Skip the failed attempts that pollute your context
- **Preserve AI sharpness** — Keep your context window lean for the work that matters

```
Without GIM:  Error → Web search → 10 results → Try 5 fixes → Finally works
              Context added: ~30K tokens | Time: 15+ minutes

With GIM:     Error → GIM lookup → Verified fix → Done
              Context added: ~500 tokens | Time: seconds
```

When your AI solves something new:
1. **Auto-contribute** — Solutions are sanitized and shared (privacy-first)
2. **Build the commons** — Every fix makes the entire community smarter

**The Flywheel Effect:**

```
More vibe coders → More issues solved → Richer knowledge base
       ↑                                        ↓
       ←←←←←←←←  Better AI for everyone  ←←←←←←←
```

When every vibe coder contributes, the entire community levels up. Your fix today saves thousands of developers tomorrow. Their fixes save you next week. **This is how we build something bigger than any individual.**

**Result:** Faster fixes. Cleaner context. Sharper AI. More shipping.

---

## Who Is This For?

| You Are | Your Pain | GIM Helps By |
|---------|-----------|--------------|
| **Vibe Coder** (non-engineer) | AI burns tokens + context degrades over long sessions | Instant fixes keep context clean, AI stays sharp |
| **Vibe Coder** (engineer) | Guiding AI through common errors wastes your time | Community fixes = less hand-holding, more flow |
| **AI Tool Builder** | Your users hit the same issues, bloating their sessions | Plug in GIM for smarter, leaner error recovery |
| **Solo Hacker** | No team to ask, AI spirals burn your budget | Tap into collective knowledge 24/7, stay efficient |

---

## Why GIM Over Stack Overflow?

| Stack Overflow | GIM |
|----------------|-----|
| Tab you have to open | Built into your AI's workflow |
| Outdated answers from 2015 | Verified, working solutions |
| Humans searching manually | AI searches automatically |
| Pages of results bloat context | One clean answer, minimal tokens |
| Context lost when you switch | Context preserved in-session |
| Generic advice | Environment-aware (OS, language, model) |
| Anyone can answer | Only working fixes get in |

**GIM isn't replacing Stack Overflow. It's evolving the concept for how we actually code now — with AI.**

---
 
## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  Your AI Coding Assistant                                       │
│                                                                 │
│  "TypeError: Cannot read property 'map' of undefined"           │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  GIM MCP Server                                         │    │
│  │                                                         │    │
│  │  1. Search → Match error signature against known issues │    │
│  │  2. Retrieve → Get verified fix bundle                  │    │
│  │  3. Apply → AI uses solution directly                   │    │
│  │                                                         │    │
│  │  Result: Fixed in 1 lookup, not 50 web searches         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                     │
│                           ▼                                     │
│  "Fixed! The data wasn't fetched yet. Added null check."        │
└─────────────────────────────────────────────────────────────────┘

When your AI solves a NEW issue:
┌─────────────────────────────────────────────────────────────────┐
│  AI submits → Sanitization Layer → Community Database           │
│                                                                 │
│  • Secrets stripped        • PII removed                        │
│  • Code generalized        • Solution verified                  │
│                                                                 │
│  Now everyone benefits from this fix.                           │
└─────────────────────────────────────────────────────────────────┘
```

---

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

- **Zero Friction** — Works via MCP; your AI assistant uses it automatically, no manual searches
- **Verified Fixes Only** — Every solution actually worked; no more "did you try restarting?" noise
- **Privacy-First** — Two-layer sanitization scrubs secrets and PII before anything leaves your machine
- **Model-Aware** — Knows that Claude handles React differently than GPT; solutions matched to your stack
- **Token Efficient** — Get answers in one lookup instead of 50 web searches; keep your context clean
- **Community-Powered** — Every AI-solved issue makes everyone's assistant smarter
- **Environment-Aware** — Tracks OS, language versions, and runtime context for precise matches
- **Auto-Harvesting** — GitHub issue crawler automatically populates the knowledge base from 47+ popular repositories

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) - System design and components
- [Setup & Configuration](docs/SETUP.md) - Installation and environment setup
- [API Reference](docs/API.md) - MCP tools and data models
- [GitHub Crawler](docs/CRAWLER.md) - Automated issue harvesting from GitHub
- [Deployment Guide](docs/DEPLOYMENT.md) - Railway + Vercel deployment
- [Contributing](docs/CONTRIBUTING.md) - Development guidelines

## Project Status

**Status:** Active Development

### Completed
- Pydantic data models (MasterIssue, ChildIssue, FixBundle, Analytics, Environment)
- Two-layer sanitization pipeline (secrets, PII, MRE synthesis, LLM sanitizer)
- Database clients (Supabase, Qdrant)
- Embedding service (Google Gemini)
- MCP server with 5 tools (stdio, HTTP, and dual transport modes)
- OAuth 2.1 with PKCE authentication
- Infrastructure improvements (custom exceptions, centralized logging, thread-safe clients)
- Enhanced metadata services (contribution classifier, environment extractor, model parser)
- Security hardening (generic error messages, structured error handling)
- Vector storage optimization (single combined vector with INT8 scalar quantization)
- Frontend dashboard (Next.js 15) with GIM branding and responsive design
- CI/CD pipelines (GitHub Actions for backend, frontend, and crawler)
- Docker deployment support
- Vercel (frontend) + Railway (backend) deployment
- GitHub issue crawler with batch pagination, quality scoring, and Gemini retry logic
- Database migrations (5 migration files including OAuth and crawler state tables)

### In Progress
- Canonicalization engine (root cause classification, clustering)
- Search ranking algorithm
- Full tool-to-database integration

## MCP Tools

Your AI assistant calls these automatically — you don't need to do anything:

| Tool | What It Does | When It's Called |
|------|--------------|------------------|
| `gim_search_issues` | Find matching known issues | AI hits an error |
| `gim_get_fix_bundle` | Get the verified fix steps | Match found |
| `gim_submit_issue` | Contribute a new solution | AI solves something new |
| `gim_confirm_fix` | Report if the fix worked | After applying a fix |
| `gim_report_usage` | Anonymous usage analytics | Background |

See [API Reference](docs/API.md) for detailed tool schemas.

## Technology Stack

### Backend
- **MCP Protocol** - Anthropic Model Context Protocol
- **Python 3.12+** - Core language
- **Pydantic** - Data validation and settings
- **Supabase** - PostgreSQL database
- **Qdrant** - Vector database with INT8 scalar quantization (single combined vector per issue)
- **Google Gemini** - Embeddings (gemini-embedding-001, 3072-dim) & LLM sanitization (gemini-3-flash-preview)

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS v4** - Utility-first styling
- **Zustand** - Lightweight state management
- **TanStack React Query** - Server state & data fetching

## Frontend Application

A modern web dashboard for browsing, searching, and contributing to the GIM knowledge base.

**Running the Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to access the application.

**Screens:**
- **Landing** (`/`) - Project overview and getting started
- **Docs** (`/docs/*`) - Full documentation with sidebar navigation
- **Dashboard** (`/dashboard`) - Search and browse issues with category filters
- **Issue Detail** (`/dashboard/issues/[id]`) - Full issue view with fix bundles and trust signals
- **Profile** (`/dashboard/profile`) - User contributions, heatmap, and GIM ID card
- **Terms** (`/terms`) - Terms of service

## Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key
GOOGLE_API_KEY=your-google-api-key

# Authentication (required for HTTP transport)
JWT_SECRET_KEY=your-secret-key-minimum-32-characters-long

# Optional
EMBEDDING_MODEL=gemini-embedding-001
LLM_MODEL=gemini-3-flash-preview
LOG_LEVEL=INFO
GITHUB_TOKEN=your-github-pat              # For crawler (higher rate limits)
ACCESS_TOKEN_TTL_HOURS=24                  # JWT access token lifetime
SANITIZATION_CONFIDENCE_THRESHOLD=0.85     # Min confidence for sanitization
SIMILARITY_MERGE_THRESHOLD=0.85            # Threshold for issue merging
```

See [Setup Guide](docs/SETUP.md) for the full environment variables reference.

## Contributing

We're building this in the open. Here's how you can help:

**Use GIM** — Every issue your AI solves and shares makes the whole system smarter.

**Build with us** — We follow TDD. Write failing tests first, then implement.

```bash
pytest -v  # Run before every commit
```

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## Join the Movement

The age of vibe coding is here. Millions of developers — engineers and non-engineers alike — are building with AI. The question is: will every AI assistant reinvent the wheel on every error, or will they learn from each other?

**GIM is betting on collective intelligence.**

When you use GIM, you're not just helping yourself — you're contributing to a growing knowledge base that makes every vibe coder's AI smarter. The more we share, the faster we all ship.

- Star this repo to follow along
- Try it in your workflow
- Share what you build
- **Every contribution counts**

## License

This project is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE). You may use, modify, and distribute this software for any **noncommercial purpose**. Commercial use is not permitted under this license.

---

## The Vision

We believe coding forums aren't dead — they just need to evolve.

Stack Overflow was built for humans searching browsers. GIM is built for AI assistants that need instant, verified answers without breaking your flow.

**The vibe coding revolution is just beginning.** Whether you're an engineer letting AI handle the boilerplate or a non-engineer bringing ideas to life — we're all vibe coders now. And when we share what we learn, we all get better.

**Every bug your AI solves today becomes a shortcut for the entire community tomorrow.**

The more vibe coders join, the smarter everyone's AI becomes. That's not a feature — that's the whole point.

Join us in building the collective memory layer for the AI coding era.

---

*Privacy-preserving. Community-powered. Built for vibe coders.*
