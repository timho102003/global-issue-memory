# GIM Setup & Configuration Guide

This guide walks you through setting up a local development environment for Global Issue Memory (GIM).

## Prerequisites

- **Python 3.12+** (required)
- **Git** (for cloning the repository)
- **Supabase account** (free tier available)
- **Qdrant** (local Docker or cloud instance)
- **Google Cloud account** (for Gemini API)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/gim.git
cd gim
```

### 2. Create Virtual Environment

```bash
# Navigate to the gim project directory
cd gim/

# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -e .

# Install development dependencies (includes pytest)
pip install -e ".[dev]"
```

### 4. Set Up External Services

#### Supabase (PostgreSQL)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Note your project URL and API key (anon/public key)

**Important:** Database schema is not yet created. This will be added in Phase 1.

#### Qdrant (Vector Database)

**Option A: Local Docker (Recommended for Development)**

```bash
# Pull Qdrant Docker image
docker pull qdrant/qdrant

# Run Qdrant container
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

Your Qdrant instance will be available at `http://localhost:6333`.

**Option B: Qdrant Cloud**

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a free cluster
3. Note your cluster URL and API key

#### Google Gemini API

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Note your API key

### 5. Configure Environment Variables

Create a `.env` file in the `gim/` directory:

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key  # Leave empty for local Docker

# Google AI Configuration
GOOGLE_API_KEY=your-google-api-key

# Authentication (Required for HTTP transport)
JWT_SECRET_KEY=your-secure-secret-key-min-32-chars
AUTH_ISSUER=gim-mcp
AUTH_AUDIENCE=gim-clients
ACCESS_TOKEN_TTL_HOURS=1

# OAuth 2.1 Configuration (Optional - has sensible defaults)
OAUTH_ISSUER_URL=http://localhost:8000
OAUTH_AUTHORIZATION_CODE_TTL_SECONDS=600    # 10 minutes
OAUTH_ACCESS_TOKEN_TTL_SECONDS=3600         # 1 hour
OAUTH_REFRESH_TOKEN_TTL_DAYS=30             # 30 days

# Transport Configuration
TRANSPORT_MODE=stdio  # or "http" or "dual"
HTTP_HOST=0.0.0.0
HTTP_PORT=8000

# Optional: Model Configuration
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=3072
LLM_MODEL=gemini-2.5-flash-preview-05-20

# Optional: Rate Limiting
DEFAULT_DAILY_SEARCH_LIMIT=100

# Optional: Logging
LOG_LEVEL=INFO
```

### 6. Verify Installation

```bash
# Run tests
pytest -v

# Expected output:
# tests/test_models/test_issue.py::test_master_issue_validation PASSED
# tests/test_models/test_environment.py::test_model_info_validation PASSED
# ...
# ==================== XX passed in X.XXs ====================
```

## Database Migration

After setting up Supabase, run the database migrations to create required tables:

```bash
# Navigate to gim/ directory
cd gim/

# Run migrations (in Supabase SQL Editor or via CLI)
# Migration 001: GIM identities table
psql $SUPABASE_URL -f migrations/001_create_gim_identities.sql

# Migration 002: Issue tables
psql $SUPABASE_URL -f migrations/002_create_issue_tables.sql

# Migration 003: OAuth tables
psql $SUPABASE_URL -f migrations/003_create_oauth_tables.sql
```

**Alternative: Manual Migration via Supabase Studio**

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste contents of each migration file (001, 002, 003)
4. Execute each migration in order

## Running the MCP Server

### Start the Server

**Stdio Mode** (for local MCP clients like Claude Desktop):

```bash
# Make sure you're in the gim/ directory with .venv activated
python main.py

# Or explicitly:
python -m src.server --transport stdio
```

The server will start and listen for MCP protocol messages on stdin/stdout.

**HTTP Mode** (for remote access with OAuth 2.1):

```bash
# Start with OAuth authentication
python -m src.server --transport http --host 0.0.0.0 --port 8000

# The server will expose:
# - MCP endpoint: POST /mcp
# - OAuth endpoints: /authorize, /token, /register, /revoke
# - Discovery: /.well-known/oauth-authorization-server
```

**HTTP Mode without Authentication** (development only):

```bash
python -m src.server --transport http --no-auth
```

### Configure MCP Clients

#### Option 1: Local Stdio Mode (Claude Desktop, Cursor)

Add GIM to your MCP client configuration for local stdio access:

**For Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`):**

```json
{
  "mcpServers": {
    "gim": {
      "command": "python",
      "args": ["/absolute/path/to/gim/main.py"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-supabase-key",
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_API_KEY": "",
        "GOOGLE_API_KEY": "your-google-api-key"
      }
    }
  }
}
```

**Important:** Use absolute paths in MCP configurations.

#### Option 2: Remote HTTP Mode with OAuth 2.1

For remote access, MCP clients can use OAuth 2.1 with PKCE:

**Step 1: Client Discovery**

The MCP client automatically discovers OAuth endpoints:

```bash
# Client fetches server metadata
GET https://your-gim-server.com/.well-known/oauth-authorization-server

# Response includes:
{
  "issuer": "https://your-gim-server.com",
  "authorization_endpoint": "https://your-gim-server.com/authorize",
  "token_endpoint": "https://your-gim-server.com/token",
  "registration_endpoint": "https://your-gim-server.com/register",
  "revocation_endpoint": "https://your-gim-server.com/revoke",
  "code_challenge_methods_supported": ["S256"]
}
```

**Step 2: Client Registration**

```bash
# Client registers with GIM server
POST https://your-gim-server.com/register
Content-Type: application/json

{
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:3000/callback"]
}

# Response:
{
  "client_id": "abc123xyz",
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:3000/callback"]
}
```

**Step 3: Authorization Flow**

```bash
# 1. Client generates PKCE challenge and redirects user to:
GET https://your-gim-server.com/authorize?
    response_type=code&
    client_id=abc123xyz&
    redirect_uri=http://localhost:3000/callback&
    code_challenge=PKCE_CHALLENGE&
    code_challenge_method=S256&
    state=random_state

# 2. User enters their GIM ID in the authorization form

# 3. Server redirects back with authorization code:
GET http://localhost:3000/callback?code=AUTH_CODE&state=random_state

# 4. Client exchanges code for tokens:
POST https://your-gim-server.com/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE&
client_id=abc123xyz&
redirect_uri=http://localhost:3000/callback&
code_verifier=PKCE_VERIFIER

# 5. Response with access and refresh tokens:
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here"
}
```

**Step 4: Using Access Token**

```bash
# Client makes MCP requests with Bearer token
POST https://your-gim-server.com/mcp
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "gim_search_issues",
    "arguments": {...}
  }
}
```

**Step 5: Refreshing Tokens**

```bash
# When access token expires, refresh it:
POST https://your-gim-server.com/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
client_id=abc123xyz&
refresh_token=refresh_token_here

# Response with new tokens (old refresh token is revoked):
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "new_refresh_token_here"
}
```

#### Option 3: Simple HTTP Mode with Direct GIM ID Exchange

For clients that don't support OAuth:

```bash
# 1. Generate GIM ID (one-time)
POST https://your-gim-server.com/auth/gim-id
Content-Type: application/json

{}

# Response:
{
  "gim_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-27T10:00:00Z"
}

# 2. Exchange GIM ID for JWT (repeat when token expires)
POST https://your-gim-server.com/auth/token
Content-Type: application/json

{
  "gim_id": "550e8400-e29b-41d4-a716-446655440000"
}

# Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}

# 3. Use JWT for MCP requests
POST https://your-gim-server.com/mcp
Authorization: Bearer eyJhbGc...
```

### Verify MCP Tools are Available

In your MCP client (e.g., Claude Desktop), you should see 5 GIM tools:

- `gim_search_issues`
- `gim_get_fix_bundle`
- `gim_submit_issue`
- `gim_confirm_fix`
- `gim_report_usage`

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_models/test_issue.py -v

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code (if using black)
black src/ tests/

# Type checking (if using mypy)
mypy src/

# Linting (if using ruff)
ruff check src/ tests/
```

### Debugging

**Enable debug logging:**

```bash
# In .env
LOG_LEVEL=DEBUG
```

**Check logs:**

The MCP server logs to stderr. Redirect to a file for easier debugging:

```bash
python main.py 2> gim_debug.log
```

## Database Maintenance

### Cleanup Expired OAuth Tokens

OAuth authorization codes and refresh tokens should be periodically cleaned up. The migrations include cleanup functions:

```sql
-- Cleanup expired authorization codes (run daily via cron)
SELECT cleanup_expired_oauth_codes();

-- Cleanup expired/revoked refresh tokens (run daily via cron)
SELECT cleanup_expired_oauth_tokens();
```

**Setting up automated cleanup (Supabase):**

1. Go to Database > Functions in Supabase Dashboard
2. Verify the cleanup functions exist
3. Use Supabase Edge Functions or external cron (GitHub Actions, cron-job.org) to call:

```bash
# Daily cleanup via curl
curl -X POST 'https://your-project.supabase.co/rest/v1/rpc/cleanup_expired_oauth_codes' \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Content-Type: application/json"

curl -X POST 'https://your-project.supabase.co/rest/v1/rpc/cleanup_expired_oauth_tokens' \
  -H "apikey: YOUR_SUPABASE_KEY" \
  -H "Content-Type: application/json"
```

### Database Backup

Recommended backup strategy:

1. **Supabase Projects**: Automatic daily backups (included in paid plans)
2. **Manual Backup**: Use `pg_dump` to export your database
3. **Qdrant**: Snapshots can be created via Qdrant API

```bash
# Backup Supabase (PostgreSQL)
pg_dump $DATABASE_URL > gim_backup_$(date +%Y%m%d).sql

# Backup Qdrant collection
curl -X POST 'http://localhost:6333/collections/gim_issues/snapshots'
```

## Qdrant Collection Setup

The MCP server automatically creates the Qdrant collection on startup. You can verify it:

```bash
# Check collections
curl http://localhost:6333/collections

# Expected response:
{
  "result": {
    "collections": [
      {"name": "gim_issues"}
    ]
  }
}
```

## Troubleshooting

### Issue: "Module 'mcp' not found"

**Solution:**
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"
```

### Issue: "Connection refused to Qdrant"

**Solution:**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not running, start it
docker run -p 6333:6333 qdrant/qdrant

# Or check your QDRANT_URL in .env
```

### Issue: "Google API authentication failed"

**Solution:**
```bash
# Verify your API key
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_API_KEY"

# If failed, regenerate key at https://makersuite.google.com/app/apikey
```

### Issue: "Supabase connection timeout"

**Solution:**
- Check your SUPABASE_URL (should include `https://`)
- Verify your API key is the "anon" key, not the "service_role" key
- Check your internet connection
- Verify your Supabase project is not paused (free tier pauses after inactivity)

### Issue: Tests failing with "ModuleNotFoundError"

**Solution:**
```bash
# Ensure you installed the package in editable mode
pip install -e .

# Verify package is installed
pip show gim
```

### Issue: OAuth authorization fails with "invalid_client"

**Solution:**
- Verify client_id is registered via `/register` endpoint
- Check client_id matches exactly in authorization and token requests
- Ensure redirect_uri is registered for the client

### Issue: PKCE verification failed

**Solution:**
- Ensure code_challenge_method is "S256" (not "plain")
- Verify code_verifier matches the original challenge
- Check that authorization code hasn't expired (10 min default)
- Ensure code hasn't been used already (single-use)

### Issue: Refresh token revoked

**Solution:**
- Refresh tokens are single-use and rotate on each refresh
- Store the new refresh_token from each token refresh response
- Check token hasn't expired (30 days default)
- Verify token wasn't manually revoked via `/revoke`

### Issue: "Authorization code not found"

**Solution:**
- Authorization codes are single-use and short-lived (10 min)
- Codes are hashed in storage - ensure using exact code from redirect
- Check system time is synchronized (codes have strict expiration)
- Verify code wasn't already exchanged

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes | - | Supabase project URL |
| `SUPABASE_KEY` | Yes | - | Supabase anon/public key |
| `QDRANT_URL` | Yes | - | Qdrant instance URL |
| `QDRANT_API_KEY` | No | - | Qdrant API key (empty for local) |
| `GOOGLE_API_KEY` | Yes | - | Google AI Studio API key |
| `JWT_SECRET_KEY` | Yes (HTTP) | - | Secret key for JWT signing (min 32 chars) |
| `AUTH_ISSUER` | No | `gim-mcp` | JWT token issuer identifier |
| `AUTH_AUDIENCE` | No | `gim-clients` | JWT token audience identifier |
| `ACCESS_TOKEN_TTL_HOURS` | No | `1` | JWT access token TTL in hours |
| `OAUTH_ISSUER_URL` | No | `http://localhost:8000` | OAuth server issuer URL |
| `OAUTH_AUTHORIZATION_CODE_TTL_SECONDS` | No | `600` | Auth code TTL (10 min) |
| `OAUTH_ACCESS_TOKEN_TTL_SECONDS` | No | `3600` | OAuth access token TTL (1 hour) |
| `OAUTH_REFRESH_TOKEN_TTL_DAYS` | No | `30` | Refresh token TTL (30 days) |
| `TRANSPORT_MODE` | No | `stdio` | Transport mode (stdio, http, dual) |
| `HTTP_HOST` | No | `0.0.0.0` | Host for HTTP server |
| `HTTP_PORT` | No | `8000` | Port for HTTP server |
| `DEFAULT_DAILY_SEARCH_LIMIT` | No | `100` | Daily search limit per GIM ID |
| `EMBEDDING_MODEL` | No | `gemini-embedding-001` | Google embedding model |
| `EMBEDDING_DIMENSIONS` | No | `3072` | Embedding vector dimensions |
| `LLM_MODEL` | No | `gemini-2.5-flash-preview-05-20` | Google LLM model for sanitization |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Next Steps

- Read the [Architecture Guide](ARCHITECTURE.md) to understand system design
- Read the [API Reference](API.md) to learn about MCP tools
- Read the [PRD](PRD_Global_Issue_Memory.md) for full product specification
- Check the [Contributing Guide](CONTRIBUTING.md) for development guidelines

## Getting Help

- Check existing [GitHub Issues](https://github.com/your-org/gim/issues)
- Read the [FAQ](FAQ.md) (coming soon)
- Join the [Discord community](https://discord.gg/gim) (coming soon)

## Docker Setup (Alternative)

**Coming Soon:** Docker Compose setup for one-command local environment.

```bash
# Planned for Phase 2
docker-compose up
```

This will spin up:
- GIM MCP server
- Qdrant
- PostgreSQL (local alternative to Supabase)
- Dashboard UI (when implemented)
