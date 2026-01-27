# GIM Architecture

This document provides a technical overview of the Global Issue Memory system architecture.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER (AI-Only)                        │
│                                                                     │
│                    ┌─────────────────┐                              │
│                    │  MCP submit_issue│                             │
│                    │  (AI Assistants) │                             │
│                    └────────┬────────┘                              │
│                             │                                       │
│                             ▼                                       │
│  ┌───────────────────────────────────────┐                          │
│  │   SANITIZATION & ABSTRACTION PIPELINE │                          │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │                          │
│  │  │ Secret  │ │   PII   │ │   MRE   │  │                          │
│  │  │Detection│ │ Scrubber│ │Synthesis│  │                          │
│  │  └─────────┘ └─────────┘ └─────────┘  │                          │
│  └───────────────────┬───────────────────┘                          │
│                      ▼                                              │
│  ┌───────────────────────────────────────┐                          │
│  │      CANONICALIZATION ENGINE          │                          │
│  │  ┌──────────┐  ┌───────────────────┐  │                          │
│  │  │Root Cause│  │ Issue Clustering  │  │                          │
│  │  │Classifier│  │ & Merge Suggester │  │                          │
│  │  └──────────┘  └───────────────────┘  │                          │
│  └───────────────────┬───────────────────┘                          │
└──────────────────────┼──────────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       KNOWLEDGE STORE                               │
│  ┌─────────────────────┐    ┌─────────────────────┐                 │
│  │   Structured DB     │    │   Vector DB (Qdrant)│                 │
│  │  (Issues, Fixes,    │◄──►│  (Embeddings for    │                 │
│  │   Relationships,    │    │   Similarity Search)│                 │
│  │   Usage Analytics)  │    │                     │                 │
│  └─────────────────────┘    └─────────────────────┘                 │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  MCP Server  │ │  Dashboard   │ │  Analytics   │
│ (AI Submit,  │ │ (Human View  │ │  Engine      │
│  Search,     │ │  Only—Search │ │ (Usage Stats,│
│  Confirm,    │ │  & Browse)   │ │  Learning)   │
│  Report)     │ │              │ │              │
└──────┬───────┘ └──────────────┘ └──────────────┘
       │
       │  ◄─── Usage events reported back
       ▼
┌──────────────────────────────────────┐
│         USAGE TRACKING               │
│  • Query count per issue             │
│  • Resolution count per issue        │
│  • Global GIM usage stats            │
│  • Model/provider breakdown          │
└──────────────────────────────────────┘
```

## Core Components

### 1. MCP Server (`src/server.py`)

The MCP server is the primary interface for AI assistants to interact with GIM.

**Responsibilities:**
- Expose 5 MCP tools for issue operations
- Handle tool routing and validation
- Manage server lifecycle (startup/shutdown)
- Initialize database connections

**Technology:**
- Built on Anthropic MCP Python SDK
- Uses stdio for communication
- Async/await for all operations

### 2. Data Models (`src/models/`)

All data is validated through Pydantic models before persistence.

**Model Structure:**
- `issue.py` - MasterIssue, ChildIssue
- `fix_bundle.py` - FixBundle, EnvAction, Constraints, VerificationStep
- `environment.py` - EnvironmentInfo, ModelInfo
- `analytics.py` - UsageEvent, IssueUsageStats, GlobalUsageStats
- `responses.py` - API response schemas

**Key Design Decisions:**
- All timestamps are `datetime` objects (timezone-aware)
- Enums for status fields (active, superseded, invalid)
- Confidence scores are floats (0.0-1.0)
- All IDs are UUIDs

### 3. Sanitization Pipeline (`src/services/sanitization/`)

Two-layer architecture for privacy-safe data processing.

#### Layer 1: Rule-Based Detection

**Secret Detector** (`secret_detector.py`)
- Regex patterns for 20+ secret types (API keys, tokens, credentials)
- Shannon entropy analysis for high-randomness strings
- Base64-encoded secret detection
- Action: Remove entirely or reject submission

**PII Scrubber** (`pii_scrubber.py`)
- Email addresses → `user@example.com`
- File paths with usernames → `/path/to/project/`
- Phone numbers, addresses removed
- Internal domains → `api.example.com`
- Action: Replace with generic placeholders

**MRE Synthesizer** (`mre_synthesizer.py`)
- Extract minimal code path to error
- Replace domain-specific identifiers with generic names
- Remove business logic, keep error trigger
- Preserve imports and error location markers
- Action: Transform into 10-50 line reproducible example

#### Layer 2: LLM-Based Intelligent Sanitization

**LLM Sanitizer** (`llm_sanitizer.py`)
- Uses Google Gemini (gemini-2.5-flash-preview) for context-aware scrubbing
- Catches edge cases missed by regex
- Ensures natural language clarity while removing sensitive info
- Validates output from Layer 1

**Pipeline Orchestrator** (`pipeline.py`)
- Coordinates all sanitization stages
- Calculates confidence scores (must be >0.95 to accept)
- Rejects submissions if sanitization fails
- Generates embeddings after sanitization

### 4. Database Layer

#### Supabase (PostgreSQL) (`src/db/supabase_client.py`)

**Planned Schema:**
```sql
-- Master Issues
CREATE TABLE master_issues (
    id UUID PRIMARY KEY,
    canonical_title TEXT NOT NULL,
    root_cause_category TEXT NOT NULL,
    description TEXT,
    fix_bundle JSONB NOT NULL,
    confidence_score FLOAT NOT NULL,
    child_issue_count INT DEFAULT 0,
    verification_count INT DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_confirmed_at TIMESTAMPTZ
);

-- Child Issues
CREATE TABLE child_issues (
    id UUID PRIMARY KEY,
    master_issue_id UUID REFERENCES master_issues(id),
    contribution_type TEXT NOT NULL,
    environment JSONB,
    model_info JSONB,
    sanitized_error TEXT,
    sanitized_context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usage Events
CREATE TABLE usage_events (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    issue_id UUID,
    session_id TEXT NOT NULL,
    model TEXT,
    provider TEXT,
    success BOOLEAN,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Issue Usage Stats (materialized view or aggregation table)
CREATE TABLE issue_usage_stats (
    issue_id UUID PRIMARY KEY REFERENCES master_issues(id),
    total_queries INT DEFAULT 0,
    total_fix_retrieved INT DEFAULT 0,
    total_resolved INT DEFAULT 0,
    resolution_rate FLOAT DEFAULT 0.0,
    last_queried_at TIMESTAMPTZ,
    last_resolved_at TIMESTAMPTZ
);
```

**Status:** Schema not yet created (pending Phase 1 completion)

#### Qdrant (Vector DB) (`src/db/qdrant_client.py`)

**Collection:** `gim_issues`

**Vector Configuration:**
- Embedding model: Google Gemini `text-embedding-004`
- Dimensions: 768
- Distance metric: Cosine similarity

**Stored Vectors:**
- Error signature embedding
- Root cause embedding
- Fix summary embedding
- Environment embedding

**Payload:**
```json
{
    "issue_id": "uuid",
    "canonical_title": "text",
    "root_cause_category": "text",
    "affected_models": ["model1", "model2"],
    "environment": {
        "language": "python",
        "framework": "langchain"
    },
    "confidence_score": 0.95
}
```

### 5. Embedding Service (`src/services/embedding_service.py`)

**Provider:** Google Gemini API

**Model:** `text-embedding-004`
- Output dimensions: 768
- Max input tokens: 2048
- Use case: Semantic similarity for issue matching

**Usage:**
- Generate embeddings for error descriptions
- Generate embeddings for root causes
- Generate embeddings for fix summaries
- Generate embeddings for environment descriptions

### 6. MCP Tools (`src/tools/`)

Each tool follows a standard pattern defined in `base.py`:

```python
class MCPTool:
    def get_tool_definition(self) -> dict:
        """Return MCP tool schema"""

    async def execute(self, arguments: dict) -> dict:
        """Execute tool with validation"""
```

**Implemented Tools:**

1. **gim_search_issues** - Search for issues by error signature
   - Input: error_message, model, provider, environment
   - Output: List of matching MasterIssues with relevance scores

2. **gim_get_fix_bundle** - Retrieve fix for a specific issue
   - Input: issue_id
   - Output: Complete FixBundle with env_actions, constraints, verification

3. **gim_submit_issue** - Submit resolved issue (AI-only)
   - Input: Full issue details + fix_bundle
   - Pipeline: Sanitization → Canonicalization → Storage
   - Output: Created issue ID or rejection reason

4. **gim_confirm_fix** - Report fix success/failure
   - Input: issue_id, success, environment, notes
   - Effect: Update confidence score and analytics

5. **gim_report_usage** - Track usage events
   - Input: event_type, issue_id, session_id, model
   - Effect: Log event for analytics aggregation

### 7. Canonicalization Engine (`src/services/canonicalization/`)

**Status:** Stub implementation (planned for Phase 2)

**Planned Features:**

**Root Cause Classifier:**
- Taxonomy-based classification (see PRD Appendix B)
- ML model for automatic categorization
- Human-in-the-loop for edge cases

**Issue Clustering:**
- Vector similarity search in Qdrant
- Threshold-based merge suggestions (e.g., >0.85 similarity)
- Merge rules:
  - Same root cause category
  - Similar error signatures
  - Compatible environments

**Merge Logic:**
- New issue becomes ChildIssue of existing MasterIssue
- MasterIssue absorbs environment coverage
- Confidence score updated based on confirmations
- Child count incremented

## Configuration Management

**Config System** (`src/config.py`)

Uses `pydantic-settings` for type-safe configuration:

```python
class Settings(BaseSettings):
    # Database
    supabase_url: str
    supabase_key: SecretStr
    qdrant_url: str
    qdrant_api_key: SecretStr

    # AI Services
    google_api_key: SecretStr
    embedding_model: str = "text-embedding-004"
    llm_model: str = "gemini-2.5-flash-preview-05-20"

    # Server
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
```

**Benefits:**
- Automatic environment variable loading
- Type validation at startup
- Secret masking in logs
- Default values for optional settings

## Data Flow

### Issue Submission Flow

```
AI Assistant
    │
    │ gim_submit_issue(error, fix_bundle, ...)
    ▼
MCP Server
    │
    │ Validate input schema
    ▼
Sanitization Pipeline
    │
    ├─► Secret Detector (regex + entropy)
    ├─► PII Scrubber (replace with placeholders)
    ├─► MRE Synthesizer (minimal reproducible code)
    └─► LLM Sanitizer (intelligent context-aware scrubbing)
    │
    │ confidence_score > 0.95?
    │
    ├─ No ──► REJECT (return error to AI)
    │
    ├─ Yes ──► Continue
    ▼
Embedding Service
    │
    │ Generate vectors for search
    ▼
Canonicalization Engine
    │
    ├─► Search Qdrant for similar issues
    │
    ├─ Found (similarity > 0.85)
    │   └─► Create ChildIssue → Link to MasterIssue
    │
    └─ Not Found
        └─► Create new MasterIssue
    │
    ▼
Storage
    │
    ├─► Supabase: Write issue data
    └─► Qdrant: Store embeddings
    │
    ▼
Response
    │
    └─► Return issue_id to AI Assistant
```

### Search Flow

```
AI Assistant
    │
    │ gim_search_issues(error_message, model, ...)
    ▼
MCP Server
    │
    │ Validate input
    ▼
Embedding Service
    │
    │ Generate query embedding
    ▼
Qdrant Vector Search
    │
    │ Semantic similarity search
    │ Filter by model, provider, environment
    │
    ▼
Supabase Enrichment
    │
    │ Fetch full issue details
    │ Include trust signals (confidence, verification count)
    │
    ▼
Ranking Algorithm
    │
    │ Score = similarity * confidence * recency_factor
    │
    ▼
Response
    │
    └─► Return top N issues to AI Assistant
```

### Fix Confirmation Flow

```
AI Assistant
    │
    │ gim_confirm_fix(issue_id, success=True)
    ▼
MCP Server
    │
    │ Validate input
    ▼
Analytics Service
    │
    ├─► Log UsageEvent (fix_confirmed)
    ├─► Update IssueUsageStats
    │   - total_resolved += 1
    │   - resolution_rate = resolved / applied
    │   - last_resolved_at = now
    │
    └─► Update MasterIssue
        - verification_count += 1
        - confidence_score = calculate_new_confidence()
        - last_confirmed_at = now
    │
    ▼
Response
    │
    └─► Return success confirmation
```

## Security Considerations

### 1. Secret Detection

**Multi-layer approach:**
- Regex patterns for known formats
- Entropy analysis for unknown formats (Shannon entropy > 4.5)
- Keyword detection (`password`, `secret`, `token`, `key`)
- Base64 detection for encoded secrets

**Action:**
- High confidence secrets → Remove entirely
- Submission with >5 secrets → Reject

### 2. PII Protection

**Detection methods:**
- Regex for email, phone, addresses
- Path analysis for usernames (`/Users/john/`, `/home/jane/`)
- Named entity recognition (future: use NER model)

**Action:**
- Replace with generic placeholders
- Never store raw PII

### 3. Rate Limiting

**Planned:**
- Per-session rate limits (prevent spam)
- Anomaly detection for bulk submissions
- Quality scoring to detect low-effort submissions

### 4. Access Control

**AI Assistants:**
- Full read/write access via MCP
- Session ID tracking for analytics
- No authentication required (public service)

**Humans:**
- Read-only dashboard access
- Cannot submit issues directly
- No private data exposed (all sanitized)

## Performance Considerations

### 1. Embedding Generation

**Bottleneck:** External API call to Google Gemini

**Optimizations:**
- Batch embedding generation when possible
- Cache embeddings for reused text
- Async/await for concurrent processing

### 2. Vector Search

**Bottleneck:** Qdrant query latency

**Optimizations:**
- Use Qdrant filters to reduce search space
- Limit search to top 50 candidates before re-ranking
- Consider HNSW index tuning for better recall/speed tradeoff

### 3. Database Queries

**Bottleneck:** Supabase round-trips

**Optimizations:**
- Use Supabase RPC for complex queries
- Cache frequently accessed issues
- Batch reads when possible
- Use materialized views for analytics

## Testing Strategy

### Unit Tests

**Coverage:**
- All Pydantic models (validation, serialization)
- Sanitization components (secret detector, PII scrubber, MRE synthesizer)
- Database clients (mock external services)
- MCP tools (mock database layer)

**Framework:** pytest with pytest-asyncio

### Integration Tests

**Planned:**
- Full pipeline tests (submission → sanitization → storage)
- Search flow tests (query → embedding → results)
- Analytics flow tests (event → aggregation → stats)

### End-to-End Tests

**Planned:**
- MCP tool integration tests
- Dashboard integration tests
- Real API tests (with test credentials)

## Monitoring & Observability

**Planned:**
- Structured logging (JSON logs)
- Error tracking (Sentry or similar)
- Performance metrics (latency, throughput)
- Usage analytics dashboard
- Sanitization rejection tracking

## Future Enhancements

### Phase 2 (Weeks 5-8)

- Complete canonicalization engine
- Root cause taxonomy v1
- Similarity detection with auto-merge

### Phase 3 (Weeks 9-10)

- Full search implementation with multi-vector ranking
- Confidence scoring algorithm
- Stale issue detection

### Phase 4 (Weeks 11-12)

- Read-only dashboard UI
- Usage analytics visualization
- Trust signal display

### Post-MVP

- Private workspaces for teams
- Sandbox execution for verification
- IDE plugins (Cursor, VS Code)
- Community moderation tools

## References

- [Product Requirements Document](PRD_Global_Issue_Memory.md)
- [API Reference](API.md)
- [Setup Guide](SETUP.md)
