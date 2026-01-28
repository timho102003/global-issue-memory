```
   ______ _______ _______
  / _____|_______|_______)
 | /  ___   _     _  _  _
 | | (___)| | | | || || |
 | \____/| | | | || || |
  \_____/|_| |_|_||_||_|

  Global Issue Memory
  AI Coding Issue Intelligence
```

# GIM - Global Issue Memory

A privacy-preserving MCP server that transforms AI coding failures into sanitized, searchable "master issues" with verified solutions.

## What is GIM?

GIM creates a shared knowledge base of AI coding issues and their solutions, enabling AI agents to learn from collective experience while maintaining user privacy through automatic sanitization.

## Quick Start

### Prerequisites

- Python 3.10+
- Supabase account (for metadata storage)
- Qdrant Cloud account (for vector search)
- Google AI API key (for embeddings and LLM)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd gim

# Install dependencies with uv
uv pip install -e ".[dev]"
```

### Configuration

Create a `.env` file in the project root:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key

# Qdrant Configuration
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# Google AI Configuration
GOOGLE_API_KEY=your-google-ai-api-key
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=3072
LLM_MODEL=gemini-2.5-flash-preview-05-20

# Authentication (Required for HTTP transport)
# Generate a secure random key: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-secure-secret-key-min-32-chars
AUTH_ISSUER=gim-mcp
AUTH_AUDIENCE=gim-clients
ACCESS_TOKEN_TTL_HOURS=1

# OAuth 2.1 Settings (Optional - has sensible defaults)
# Used for MCP client authorization via OAuth 2.1 with PKCE
OAUTH_ISSUER_URL=http://localhost:8000
OAUTH_AUTHORIZATION_CODE_TTL_SECONDS=600    # 10 minutes
OAUTH_ACCESS_TOKEN_TTL_SECONDS=3600         # 1 hour
OAUTH_REFRESH_TOKEN_TTL_DAYS=30             # 30 days

# Server Configuration
TRANSPORT_MODE=stdio  # or "http" or "dual"
HTTP_HOST=0.0.0.0
HTTP_PORT=8000

# Rate Limiting
DEFAULT_DAILY_SEARCH_LIMIT=100
```

**Important Notes:**
- `JWT_SECRET_KEY` must be at least 32 characters for security
- For production, set `OAUTH_ISSUER_URL` to your public server URL
- Run database migrations before starting the server (see Setup Guide)
- OAuth endpoints are only exposed in `http` or `dual` transport modes

### Running the Server

**Stdio Mode** (for local MCP clients like Claude Desktop):

```bash
python -m src.server --transport stdio
```

**HTTP Mode with OAuth 2.1** (for remote MCP clients):

```bash
python -m src.server --transport http --host 0.0.0.0 --port 8000

# Server exposes:
# - MCP endpoint: POST /mcp
# - OAuth discovery: GET /.well-known/oauth-authorization-server
# - Client registration: POST /register
# - Authorization: GET/POST /authorize
# - Token endpoint: POST /token
# - Revocation: POST /revoke
# - Direct auth: POST /auth/gim-id, POST /auth/token
```

**HTTP Mode without Auth** (development only):

```bash
python -m src.server --transport http --no-auth
```

**Dual Mode** (both stdio and HTTP):

```bash
python -m src.server --transport dual --host 0.0.0.0 --port 8000
```

## Key Features

- **OAuth 2.1 with PKCE**: Full RFC-compliant OAuth 2.1 authorization server with PKCE (RFC 7636) for secure MCP client authentication
- **Dynamic Client Registration**: Automatic client registration per RFC 7591
- **Privacy-First Design**: Automatic sanitization of sensitive information before storage
- **Semantic Search**: Vector-based search using Google's gemini-embedding-001
- **Issue Deduplication**: Automatic detection and merging of similar issues
- **Solution Verification**: Community feedback on fix effectiveness
- **Multi-Transport**: Supports both stdio (local) and HTTP (remote) transports
- **JWT Authentication**: Secure token-based authentication with refresh token rotation
- **Rate Limiting**: 100 searches/day per GIM ID (configurable)

## MCP Tools

- `gim_search_issues`: Search for known issues matching an error
- `gim_get_fix_bundle`: Get detailed fix information for a specific issue
- `gim_submit_issue`: Submit a new issue with fix to the knowledge base
- `gim_confirm_fix`: Confirm whether a fix worked (feedback loop)
- `gim_report_usage`: Report usage analytics events

## Documentation

- [Setup Guide](/docs/SETUP.md) - Installation, configuration, and database setup
- [Architecture Guide](/docs/ARCHITECTURE.md) - System design, OAuth 2.1 flow, and security
- [API Reference](/docs/API.md) - HTTP endpoints and MCP tools (coming soon)
- [Development Guidelines](/CLAUDE.md) - Code standards and testing practices

**Quick Links:**
- OAuth 2.1 Setup: See [SETUP.md - Configure MCP Clients](/docs/SETUP.md#configure-mcp-clients)
- Database Migrations: See [SETUP.md - Database Migration](/docs/SETUP.md#database-migration)
- Authentication Details: See [ARCHITECTURE.md - Authentication Methods](/docs/ARCHITECTURE.md#authentication-methods-http-transport)

## Development

### Running Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Standards

- Follow PEP 8 conventions
- Write docstrings for all functions (Google style)
- All data models use Pydantic validation
- Test-driven development: write tests first

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## Authentication

GIM supports two authentication methods for HTTP transport:

### Method 1: OAuth 2.1 with PKCE (Recommended)

Standard OAuth 2.1 authorization code flow with PKCE for secure MCP client authorization.

**Supported RFCs:**
- RFC 6749 (OAuth 2.0)
- RFC 7636 (PKCE) - S256 required
- RFC 7591 (Dynamic Client Registration)
- RFC 8414 (Authorization Server Metadata)
- RFC 7009 (Token Revocation)

**Quick Start:**

```bash
# 1. Discover OAuth endpoints
GET /.well-known/oauth-authorization-server

# 2. Register your client
POST /register
{
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:3000/callback"]
}

# 3. Start authorization flow
GET /authorize?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&code_challenge=CHALLENGE&code_challenge_method=S256

# 4. User enters GIM ID at authorization page

# 5. Exchange code for tokens
POST /token
grant_type=authorization_code&code=CODE&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&code_verifier=VERIFIER

# 6. Use access token for MCP requests
POST /mcp
Authorization: Bearer ACCESS_TOKEN

# 7. Refresh when expired
POST /token
grant_type=refresh_token&client_id=CLIENT_ID&refresh_token=REFRESH_TOKEN
```

**Security Features:**
- PKCE S256 only (prevents authorization code interception)
- Authorization codes hashed and single-use
- Refresh token rotation (old token revoked on use)
- Short-lived authorization codes (10 min default)
- Access tokens are JWTs (1 hour TTL default)
- No client secrets required (public clients)

### Method 2: Direct GIM ID Exchange (Simple Clients)

For clients that don't support OAuth or need simpler integration:

```bash
# 1. Generate GIM ID (one-time)
POST /auth/gim-id

# Response: {"gim_id": "550e8400-e29b-41d4-a716-446655440000"}

# 2. Exchange for JWT (repeat when expired)
POST /auth/token
{"gim_id": "550e8400-e29b-41d4-a716-446655440000"}

# Response: {"access_token": "eyJhbGc...", "expires_in": 3600}

# 3. Use token for MCP requests
POST /mcp
Authorization: Bearer eyJhbGc...
```

**When to use:**
- Simple scripts or automation
- Clients without OAuth support
- Development and testing
- Personal projects

See [Setup Guide](docs/SETUP.md) for detailed configuration instructions.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please read our development guidelines in [CLAUDE.md](CLAUDE.md).
