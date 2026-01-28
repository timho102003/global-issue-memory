# GIM Architecture

This document provides a comprehensive overview of GIM's architecture, design decisions, and system components.

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         GIM MCP Server                           │
│                                                                  │
│  ┌────────────────┐         ┌─────────────────────────────┐   │
│  │  FastMCP 2.x   │         │    Authentication Layer     │   │
│  │   Transport    │◄────────┤  - GIM ID Management        │   │
│  │  (stdio/HTTP)  │         │  - JWT Token Service        │   │
│  └────────┬───────┘         │  - Rate Limiter             │   │
│           │                 └─────────────────────────────┘   │
│           │                                                    │
│  ┌────────▼────────────────────────────────────────────────┐  │
│  │                   MCP Tools Layer                       │  │
│  │  - search_issues  - get_fix_bundle  - submit_issue     │  │
│  │  - confirm_fix    - report_usage                       │  │
│  └────────┬────────────────────────────────────────────────┘  │
│           │                                                    │
│  ┌────────▼────────────────────────────────────────────────┐  │
│  │               Business Logic Layer                      │  │
│  │  - Sanitization Pipeline   - Canonicalization          │  │
│  │  - Deduplication Logic     - Analytics                 │  │
│  └────────┬────────────────────────────────────────────────┘  │
│           │                                                    │
│  ┌────────▼────────────────────────────────────────────────┐  │
│  │                  Storage Layer                          │  │
│  │  - Supabase Client    - Qdrant Client                  │  │
│  │  - Repository Pattern - Vector Operations              │  │
│  └────────┬────────────────────────────────────────────────┘  │
└───────────┼────────────────────────────────────────────────────┘
            │
            │
    ┌───────▼──────┐              ┌──────────────┐
    │   Supabase   │              │    Qdrant    │
    │  (Postgres)  │              │   (Vectors)  │
    │              │              │              │
    │ - Auth       │              │ - Embeddings │
    │ - Metadata   │              │ - Search     │
    └──────────────┘              └──────────────┘
```

## Core Components

### 1. Transport Layer (FastMCP 2.x)

GIM uses FastMCP 2.x for both stdio and HTTP transports.

**Stdio Mode**:
- Direct stdin/stdout communication
- Used by MCP clients (Claude Desktop)
- No authentication required (trusted local environment)

**HTTP Mode**:
- RESTful HTTP API
- JWT authentication required
- Suitable for web applications and remote clients

**Key Features**:
- Custom authentication handler integration
- Automatic tool registration
- Lifecycle management (startup/shutdown)
- Custom route support (auth endpoints)

### 2. Authentication Layer

#### GIM ID Service

Manages GIM identities (authentication credentials).

**Responsibilities**:
- Create new GIM IDs
- Validate GIM IDs
- Revoke GIM IDs
- Track usage statistics

**Implementation**: `src/auth/gim_id_service.py`

#### JWT Token Service

Handles JWT token creation and validation.

**Algorithm**: HS256 (HMAC with SHA-256)

**Token Claims**:
- `sub`: GIM ID (subject)
- `iss`: Issuer (gim-mcp)
- `aud`: Audience (gim-clients)
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp
- `gim_identity_id`: Internal database ID

**Implementation**: `src/auth/jwt_service.py`

#### Rate Limiter

Per-operation rate limiting based on GIM identity.

**Rate Limited Operations**:
- `gim_search_issues`: 100/day
- `gim_get_fix_bundle`: 100/day

**Unlimited Operations**:
- `gim_submit_issue`
- `gim_confirm_fix`
- `gim_report_usage`

**Features**:
- Atomic database operations (prevents race conditions)
- Automatic daily reset at midnight UTC
- Per-GIM-ID customization
- Graceful error handling

**Implementation**: `src/auth/rate_limiter.py`

### 3. MCP Tools Layer

Five core tools exposed via MCP protocol:

#### gim_search_issues

Search for known issues using semantic similarity.

**Process**:
1. Generate embedding for error message
2. Check rate limits
3. Perform vector search in Qdrant
4. Apply filters (model, language, framework)
5. Return top K results with metadata
6. Update rate limit counters

#### gim_get_fix_bundle

Retrieve detailed fix information with related issues.

**Process**:
1. Check rate limits
2. Fetch issue from Qdrant by ID
3. Find related issues via similarity search
4. Compile comprehensive fix bundle
5. Update rate limit counters

#### gim_submit_issue

Submit new issue to the knowledge base.

**Process**:
1. Sanitize error message and fix
2. Generate canonical forms
3. Generate embedding
4. Check for duplicates
5. Store or merge with existing issue
6. Update statistics

#### gim_confirm_fix

Provide feedback on fix effectiveness.

**Process**:
1. Fetch issue from Qdrant
2. Update fix success rate
3. Store feedback (if provided)
4. Update occurrence statistics

#### gim_report_usage

Report analytics events for monitoring.

**Process**:
1. Validate event type
2. Store event with metadata
3. Update aggregated metrics

### 4. Business Logic Layer

#### Sanitization Pipeline

Removes sensitive information from error messages and fixes.

**Sanitization Steps**:
1. **PII Detection**: Email addresses, phone numbers, names
2. **Path Removal**: File paths, URLs, IP addresses
3. **Secret Detection**: API keys, tokens, passwords
4. **Project-Specific Removal**: Package names, internal identifiers

**Technology**: Google Gemini LLM with structured prompts

**Output**: Sanitized text + confidence score

**Implementation**: `src/services/sanitization/`

#### Canonicalization

Converts sanitized issues into canonical forms.

**Purpose**:
- Normalize similar error messages
- Enable better deduplication
- Improve search accuracy

**Examples**:
- `TypeError: Cannot read property 'x' of undefined`
- `TypeError: Cannot read property 'y' of undefined`
- → `TypeError: Cannot read property of undefined`

**Technology**: Google Gemini LLM with structured prompts

**Implementation**: `src/services/canonicalization/`

#### Deduplication

Identifies and merges duplicate issues.

**Strategy**:
1. Generate embedding for new issue
2. Search for similar issues (cosine similarity)
3. If similarity > threshold (0.85): suggest merge
4. If merge approved: increment occurrence_count
5. Update fix success rate based on feedback

**Threshold Configuration**: `SIMILARITY_MERGE_THRESHOLD=0.85`

### 5. Storage Layer

#### Supabase Client

PostgreSQL database for structured data.

**Tables**:
- `gim_identities`: Authentication and rate limiting

**Operations**:
- CRUD operations on identities
- Atomic rate limit updates
- Statistics tracking

**Features**:
- Row Level Security (RLS)
- Automatic timestamps
- JSONB metadata storage

**Implementation**: `src/db/supabase_client.py`

#### Qdrant Client

Vector database for semantic search.

**Collections**:
- `gim_issues`: Issue embeddings and metadata

**Operations**:
- Vector similarity search
- Filtered search (by model, language, etc.)
- Payload updates (statistics)
- Batch operations

**Features**:
- 3072-dimensional vectors (gemini-embedding-001)
- Cosine similarity distance
- Rich payload filtering
- Scalable cloud deployment

**Implementation**: `src/db/qdrant_client.py`

## Data Models

### Pydantic Models

All data uses Pydantic models for validation:

- `GIMIdentity`: Authentication identity with rate limits
- `JWTClaims`: JWT token structure
- `TokenRequest`/`TokenResponse`: Token exchange
- `Issue`: Core issue data structure
- `FixBundle`: Comprehensive fix information
- `Environment`: Execution environment details
- `AnalyticsEvent`: Usage tracking

**Benefits**:
- Type safety
- Automatic validation
- Serialization/deserialization
- OpenAPI schema generation

## Authentication Flow

### Token-Based Authentication

```
1. Client creates GIM ID
   POST /auth/gim-id
   ↓
   Response: {gim_id: "uuid"}

2. Client stores GIM ID securely
   (e.g., environment variable, keychain)

3. Client exchanges GIM ID for JWT
   POST /auth/token {gim_id: "uuid"}
   ↓
   Response: {access_token: "jwt", expires_in: 3600}

4. Client uses JWT for authenticated requests
   Authorization: Bearer <jwt>
   ↓
   Server validates JWT
   ↓
   Server checks rate limits
   ↓
   Server processes request

5. Token expires after 1 hour
   Client repeats step 3 to get new token
```

### Rate Limiting Flow

```
1. Request arrives with JWT
   ↓
2. Extract GIM identity ID from JWT
   ↓
3. Check if daily reset needed
   IF NOW >= daily_reset_at:
     - Reset daily_search_used = 0
     - Set daily_reset_at = tomorrow midnight
   ↓
4. Check rate limit
   IF daily_search_used >= daily_search_limit:
     - Return 429 Too Many Requests
   ↓
5. Perform operation
   ↓
6. Increment counters (atomic)
   - daily_search_used += 1
   - total_searches += 1
   ↓
7. Return response with rate limit headers
   X-RateLimit-Limit: 100
   X-RateLimit-Remaining: 87
   X-RateLimit-Reset: 1706400000
```

## Sanitization Pipeline

### Phase 1: PII Removal

```python
# Before
error = "User john.doe@company.com encountered TypeError in /Users/john/project/src/main.py"

# After
error = "User [EMAIL] encountered TypeError in [PATH]"
```

### Phase 2: Canonicalization

```python
# Before (multiple similar issues)
- "TypeError: Cannot read property 'map' of undefined"
- "TypeError: Cannot read property 'filter' of undefined"
- "TypeError: Cannot read property 'reduce' of undefined"

# After (canonical form)
- "TypeError: Cannot read property of undefined"
```

### Phase 3: Confidence Scoring

LLM provides confidence score (0-1) for sanitization quality.

**Thresholds**:
- `>= 0.95`: Auto-approve
- `0.70-0.95`: Flag for review
- `< 0.70`: Reject

**Configuration**: `SANITIZATION_CONFIDENCE_THRESHOLD=0.95`

## Vector Search

### Embedding Generation

**Model**: gemini-embedding-001 (Google)
**Dimensions**: 3072
**Input**: Canonical error message + fix description

```python
text = f"{canonical_error}\n\n{canonical_fix}"
embedding = generate_embedding(text)  # [3072 floats]
```

### Search Strategy

**Algorithm**: Approximate Nearest Neighbor (ANN) via HNSW

**Distance Metric**: Cosine similarity

**Filters Applied**:
- Model (optional)
- Provider (optional)
- Language (optional)
- Framework (optional)

**Example Query**:

```python
results = qdrant_client.search(
    collection_name="gim_issues",
    query_vector=embedding,
    limit=5,
    query_filter={
        "must": [
            {"key": "language", "match": {"value": "python"}},
            {"key": "framework", "match": {"value": "fastapi"}}
        ]
    }
)
```

## Error Handling

### Error Categories

1. **Client Errors (4xx)**:
   - 400 Bad Request: Invalid parameters
   - 401 Unauthorized: Missing/invalid auth
   - 403 Forbidden: Insufficient permissions
   - 404 Not Found: Resource not found
   - 429 Too Many Requests: Rate limit exceeded

2. **Server Errors (5xx)**:
   - 500 Internal Server Error: Unexpected error
   - 503 Service Unavailable: External service down

### Error Response Format

```json
{
  "error": "error_code",
  "error_description": "Human-readable description"
}
```

### Retry Strategy

**Recommended Client Behavior**:
- 429 (Rate Limit): Wait until `X-RateLimit-Reset`
- 500 (Server Error): Exponential backoff (1s, 2s, 4s)
- 503 (Service Unavailable): Retry after `Retry-After` header

## Performance Optimization

### Caching Strategy

**Client-Side**:
- Cache search results for identical queries
- Cache fix bundles for common issues
- Respect cache-control headers

**Server-Side** (future):
- Redis for hot issues
- Cached embeddings for common queries
- Materialized views for analytics

### Database Optimization

**Qdrant**:
- HNSW index for fast ANN search
- Payload indexes for filters
- Batch operations for bulk updates

**Supabase**:
- Indexes on `gim_id` and `status`
- Atomic operations for rate limiting
- Connection pooling

### Async Operations

All I/O operations are async:
- Database queries
- API calls (Google AI)
- Vector operations

**Benefits**:
- High concurrency
- Efficient resource usage
- Non-blocking operations

## Security Considerations

### Authentication Security

1. **JWT Signing**: HS256 with 32+ character secret
2. **Token Expiration**: 1 hour default (configurable)
3. **No Token Storage**: Stateless tokens
4. **Secret Rotation**: Periodic JWT secret updates

### Data Security

1. **Sanitization**: Remove PII before storage
2. **RLS Policies**: Row-level security in Supabase
3. **API Key Permissions**: Minimal required permissions
4. **TLS**: HTTPS for all external communication

### Rate Limiting Security

1. **Per-GIM-ID Limits**: Prevent abuse
2. **Atomic Operations**: Prevent race conditions
3. **Daily Reset**: Fair usage across time
4. **Revocation**: Instant GIM ID disabling

## Monitoring and Observability

### Metrics to Monitor

**Application Metrics**:
- Request rate (requests/second)
- Error rate (errors/request)
- Response time (p50, p95, p99)
- Rate limit hit rate

**Database Metrics**:
- Query latency
- Connection pool usage
- Storage size
- Index performance

**Business Metrics**:
- Active GIM IDs
- Daily searches performed
- Issues submitted
- Fix success rate

### Logging

**Log Levels**:
- `DEBUG`: Development only
- `INFO`: Normal operations
- `WARNING`: Recoverable issues
- `ERROR`: Serious problems
- `CRITICAL`: System failures

**Structured Logging** (future):
```json
{
  "timestamp": "2026-01-27T10:30:00Z",
  "level": "INFO",
  "message": "Search completed",
  "gim_id": "uuid",
  "operation": "gim_search_issues",
  "duration_ms": 45,
  "results_count": 3
}
```

## Scalability

### Horizontal Scaling

**Stateless Design**: Multiple server instances can run in parallel

**Load Balancing**: Distribute requests across instances

**Session Management**: No server-side sessions (JWT tokens)

### Vertical Scaling

**Database**: Supabase and Qdrant both support vertical scaling

**Memory**: Increase for larger embedding cache

**CPU**: More cores for concurrent request processing

### Data Sharding (Future)

**By Tenant**: Multi-tenant support with data isolation

**By Region**: Geographic distribution for low latency

## Technology Stack

### Core Framework
- **FastMCP 2.x**: MCP protocol implementation
- **Starlette**: ASGI web framework (via FastMCP)
- **Uvicorn**: ASGI server

### Data Processing
- **Pydantic**: Data validation and models
- **Google Gemini**: LLM for sanitization
- **gemini-embedding-001**: Embedding generation

### Storage
- **Supabase**: PostgreSQL database
- **Qdrant**: Vector database

### Authentication
- **PyJWT**: JWT token handling
- **Custom**: GIM ID system

### Testing
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting

## Design Decisions

### Why FastMCP 2.x?

- Native support for both stdio and HTTP transports
- Built-in authentication framework
- Automatic tool registration
- Active development and community

### Why GIM ID + JWT?

- **Simple**: One credential to store (GIM ID)
- **Secure**: Short-lived tokens (JWT)
- **Flexible**: Easy to revoke and rotate
- **Stateless**: No server-side session storage

### Why Hybrid Storage?

- **Supabase**: Relational data, ACID transactions, RLS
- **Qdrant**: Vector search, high performance, scalable

Each storage system excels at its specific use case.

### Why Google AI?

- **Quality**: High-quality embeddings and LLM
- **Cost**: Competitive pricing
- **API**: Simple, well-documented API
- **Performance**: Fast inference

### Why Rate Limiting?

- **Fair Usage**: Prevent abuse and ensure availability
- **Cost Control**: Limit API costs
- **Quality**: Encourage thoughtful queries
- **Freemium Model**: Enable paid tiers

## Future Enhancements

### Phase 2: Advanced Features

- **Feedback Loop**: Learn from fix confirmations
- **Custom Models**: Fine-tuned embeddings
- **Batch Operations**: Bulk issue submission
- **Admin Dashboard**: Usage analytics and management

### Phase 3: Enterprise Features

- **Multi-Tenant**: Organization support
- **SSO Integration**: OAuth, SAML
- **Audit Logs**: Comprehensive activity tracking
- **SLA Guarantees**: Uptime commitments

### Phase 4: AI Enhancements

- **Root Cause Analysis**: Automatic issue categorization
- **Fix Generation**: AI-suggested fixes
- **Impact Assessment**: Severity scoring
- **Trend Detection**: Emerging issue patterns

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Supabase Documentation](https://supabase.com/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Google AI Documentation](https://ai.google.dev/)
