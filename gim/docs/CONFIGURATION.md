# GIM Configuration Guide

Complete guide to configuring the GIM MCP Server.

## Overview

GIM uses environment variables for configuration, loaded from a `.env` file or system environment.

## Environment Variables

### Required Variables

These must be set for GIM to function:

```env
# Supabase Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key

# Qdrant Configuration (Required)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# Google AI Configuration (Required)
GOOGLE_API_KEY=your-google-ai-api-key

# Authentication (Required)
JWT_SECRET_KEY=your-secure-secret-key-min-32-chars
```

### Optional Variables

These have sensible defaults:

```env
# Google AI Models
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=3072
LLM_MODEL=gemini-3-flash-preview

# Logging
LOG_LEVEL=INFO

# Authentication
AUTH_ISSUER=gim-mcp
AUTH_AUDIENCE=gim-clients
ACCESS_TOKEN_TTL_HOURS=24

# Server Transport
TRANSPORT_MODE=stdio
HTTP_HOST=0.0.0.0
HTTP_PORT=8000

# Rate Limiting
DEFAULT_DAILY_SEARCH_LIMIT=100

# Sanitization
SANITIZATION_CONFIDENCE_THRESHOLD=0.95

# Similarity
SIMILARITY_MERGE_THRESHOLD=0.85
```

---

## Variable Reference

### Supabase Configuration

#### SUPABASE_URL

**Type**: string (URL)
**Required**: Yes
**Example**: `https://abcdefgh.supabase.co`

Your Supabase project URL. Find this in your Supabase project settings.

#### SUPABASE_KEY

**Type**: string
**Required**: Yes
**Example**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

Supabase API key. Use:
- **Anon key**: For development/testing (limited permissions)
- **Service role key**: For production (full permissions)

Find in Supabase project settings > API.

---

### Qdrant Configuration

#### QDRANT_URL

**Type**: string (URL)
**Required**: Yes
**Example**: `https://abc123.qdrant.io`

Your Qdrant Cloud cluster URL. Find in Qdrant Cloud dashboard.

#### QDRANT_API_KEY

**Type**: string
**Required**: Yes
**Example**: `xyz789...`

Qdrant API key for authentication. Find in Qdrant Cloud dashboard > API Keys.

---

### Google AI Configuration

#### GOOGLE_API_KEY

**Type**: string
**Required**: Yes
**Example**: `AIzaSy...`

Google AI API key for embeddings and LLM. Get from [Google AI Studio](https://makersuite.google.com/app/apikey).

#### EMBEDDING_MODEL

**Type**: string
**Required**: No
**Default**: `gemini-embedding-001`
**Options**:
- `gemini-embedding-001` (recommended, 3072 dimensions)
- `text-embedding-004` (legacy, 768 dimensions)

Model used for generating embeddings. If you change this, you must:
1. Update `EMBEDDING_DIMENSIONS` to match
2. Update/recreate Qdrant collection with new dimension
3. Re-embed all existing issues

#### EMBEDDING_DIMENSIONS

**Type**: integer
**Required**: No
**Default**: `3072`

Vector dimensions for the embedding model. Must match the model's output dimensions:
- `gemini-embedding-001`: 3072
- `text-embedding-004`: 768

#### LLM_MODEL

**Type**: string
**Required**: No
**Default**: `gemini-3-flash-preview`
**Options**:
- `gemini-3-flash-preview` (fast, cost-effective)
- `gemini-2.5-flash-preview-05-20` (previous version)
- `gemini-1.5-pro` (more capable, slower)

Model used for sanitization and canonicalization.

---

### Logging

#### LOG_LEVEL

**Type**: string
**Required**: No
**Default**: `INFO`
**Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

Logging verbosity. Controls the centralized logging system.

**Log Levels Explained**:
- `DEBUG`: Detailed operation logs with timing, request IDs, and argument/result logging (development only)
- `INFO`: Normal operations, startup/shutdown messages
- `WARNING`: Recoverable issues, deprecation warnings
- `ERROR`: Serious problems that prevent operations from completing
- `CRITICAL`: System-level failures

**Recommendations**:
- Development: `DEBUG` (see all operation details)
- Staging: `INFO` (normal verbosity)
- Production: `WARNING` or `INFO` (reduce noise)

**Logging Features**:
- Request context tracking with unique request IDs
- Automatic operation timing via `@log_operation` decorator
- Structured log format: `timestamp | level | logger | [request_id] | message`
- Separate logger namespace (`gim.*`) for organized log management

**Example Log Output**:
```
2026-01-27 10:30:15 | DEBUG    | gim.services.search | [a1b2c3d4] | Starting operation search_issues (op_id=ef456789)
2026-01-27 10:30:15 | DEBUG    | gim.services.search | [a1b2c3d4] | Completed operation search_issues (op_id=ef456789) in 45.23ms
2026-01-27 10:30:16 | ERROR    | gim.db.qdrant      | [a1b2c3d4] | Failed operation vector_search (op_id=gh789abc) after 102.45ms | error=QdrantError: Connection timeout
```

---

### Authentication

#### JWT_SECRET_KEY

**Type**: string
**Required**: Yes
**Min Length**: 32 characters
**Example**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

Secret key for signing JWT tokens. Must be:
- At least 32 characters long
- Cryptographically random
- Kept secret (never commit to version control)
- Rotated periodically

**Generate a secure key**:

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

#### AUTH_ISSUER

**Type**: string
**Required**: No
**Default**: `gim-mcp`

JWT token issuer identifier. Used in token validation.

#### AUTH_AUDIENCE

**Type**: string
**Required**: No
**Default**: `gim-clients`

JWT token audience identifier. Used in token validation.

#### ACCESS_TOKEN_TTL_HOURS

**Type**: integer
**Required**: No
**Default**: `1`
**Range**: 1-24

JWT token time-to-live in hours. Shorter is more secure but requires more frequent token refreshes.

**Recommendations**:
- Development: 24 hours (convenience)
- Production: 1-2 hours (security)

---

### Server Transport

#### TRANSPORT_MODE

**Type**: string
**Required**: No
**Default**: `stdio`
**Options**: `stdio`, `http`, `dual`

Server transport mode:
- `stdio`: For MCP clients (Claude Desktop)
- `http`: For web applications
- `dual`: Both transports (not recommended, use separate instances)

#### HTTP_HOST

**Type**: string (IP address)
**Required**: No
**Default**: `0.0.0.0`

Host to bind HTTP server to.

**Options**:
- `0.0.0.0`: Listen on all interfaces
- `127.0.0.1`: Localhost only (development)
- Specific IP: Bind to specific interface

#### HTTP_PORT

**Type**: integer
**Required**: No
**Default**: `8000`
**Range**: 1-65535

Port for HTTP server.

---

### Rate Limiting

#### DEFAULT_DAILY_SEARCH_LIMIT

**Type**: integer
**Required**: No
**Default**: `100`
**Range**: 1+

Default daily limit for search and get_fix_bundle operations per GIM ID.

**Recommendations**:
- Free tier: 100
- Pro tier: 1000
- Enterprise: Unlimited (set to very high value)

Can be overridden per GIM ID in the database:

```sql
UPDATE gim_identities
SET daily_search_limit = 1000
WHERE gim_id = 'specific-gim-id';
```

---

### Sanitization

#### SANITIZATION_CONFIDENCE_THRESHOLD

**Type**: float
**Required**: No
**Default**: `0.95`
**Range**: 0.0-1.0

Minimum confidence score required for sanitization approval. Issues with lower confidence are flagged for review.

**Recommendations**:
- Strict (production): 0.95
- Moderate: 0.85
- Lenient (testing): 0.70

---

### Similarity

#### SIMILARITY_MERGE_THRESHOLD

**Type**: float
**Required**: No
**Default**: `0.85`
**Range**: 0.0-1.0

Similarity threshold for suggesting issue merges. Issues with similarity above this are considered duplicates.

**Recommendations**:
- Conservative (fewer merges): 0.90
- Balanced: 0.85
- Aggressive (more merges): 0.75

---

## Configuration File

### .env File

Create a `.env` file in the project root:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# Qdrant
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-key

# Google AI
GOOGLE_API_KEY=your-key

# Auth
JWT_SECRET_KEY=your-secure-secret-key-min-32-chars

# Optional: Override defaults
LOG_LEVEL=INFO
TRANSPORT_MODE=http
HTTP_PORT=8000
```

### .env.example

Create a `.env.example` template (safe to commit):

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key

# Qdrant Configuration
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# Google AI Configuration
GOOGLE_API_KEY=your-google-ai-api-key

# Authentication
JWT_SECRET_KEY=generate-a-secure-32-character-key

# Optional Configuration
# LOG_LEVEL=INFO
# TRANSPORT_MODE=stdio
# HTTP_PORT=8000
# DEFAULT_DAILY_SEARCH_LIMIT=100
```

### .gitignore

Always exclude `.env` from version control:

```gitignore
# Environment variables
.env
.env.local
.env.*.local
```

---

## Command Line Arguments

Override environment variables via command line:

```bash
python -m src.server \
  --transport http \
  --host 0.0.0.0 \
  --port 8000 \
  --no-auth  # Disable auth (not recommended)
```

**Available Arguments**:

| Argument | Type | Description |
|----------|------|-------------|
| `--transport` | choice | Transport mode: `stdio` or `http` |
| `--host` | string | HTTP host (default from config) |
| `--port` | integer | HTTP port (default from config) |
| `--no-auth` | flag | Disable authentication (dangerous) |

---

## Environment-Specific Configuration

### Development

```env
# .env.development
SUPABASE_URL=https://dev-project.supabase.co
SUPABASE_KEY=dev-key
QDRANT_URL=https://dev-cluster.qdrant.io
QDRANT_API_KEY=dev-key
GOOGLE_API_KEY=dev-key
JWT_SECRET_KEY=dev-secret-key-min-32-characters
LOG_LEVEL=DEBUG
TRANSPORT_MODE=http
HTTP_PORT=8000
DEFAULT_DAILY_SEARCH_LIMIT=1000
```

### Staging

```env
# .env.staging
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_KEY=staging-key
QDRANT_URL=https://staging-cluster.qdrant.io
QDRANT_API_KEY=staging-key
GOOGLE_API_KEY=staging-key
JWT_SECRET_KEY=staging-secret-key-min-32-chars
LOG_LEVEL=INFO
TRANSPORT_MODE=http
HTTP_PORT=8000
DEFAULT_DAILY_SEARCH_LIMIT=100
```

### Production

```env
# .env.production
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_KEY=prod-service-role-key  # Use service role
QDRANT_URL=https://prod-cluster.qdrant.io
QDRANT_API_KEY=prod-key
GOOGLE_API_KEY=prod-key
JWT_SECRET_KEY=prod-secret-key-min-32-chars-rotated-regularly
LOG_LEVEL=WARNING
TRANSPORT_MODE=http
HTTP_HOST=0.0.0.0
HTTP_PORT=8000
DEFAULT_DAILY_SEARCH_LIMIT=100
```

Load specific environment:

```bash
# Development
cp .env.development .env
python -m src.server

# Staging
cp .env.staging .env
python -m src.server

# Production (or use container env vars)
cp .env.production .env
python -m src.server
```

---

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Don't copy .env file - use environment variables instead
CMD ["python", "-m", "src.server"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  gim:
    build: .
    ports:
      - "8000:8000"
    environment:
      # Required
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_KEY: ${SUPABASE_KEY}
      QDRANT_URL: ${QDRANT_URL}
      QDRANT_API_KEY: ${QDRANT_API_KEY}
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}

      # Optional
      TRANSPORT_MODE: http
      HTTP_HOST: 0.0.0.0
      HTTP_PORT: 8000
      LOG_LEVEL: INFO
    command: ["python", "-m", "src.server", "--transport", "http"]
```

Run with:

```bash
# Load .env file and start
docker-compose --env-file .env up
```

---

## Kubernetes Configuration

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gim-config
data:
  TRANSPORT_MODE: "http"
  HTTP_HOST: "0.0.0.0"
  HTTP_PORT: "8000"
  LOG_LEVEL: "INFO"
  DEFAULT_DAILY_SEARCH_LIMIT: "100"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gim-secrets
type: Opaque
stringData:
  SUPABASE_URL: "https://your-project.supabase.co"
  SUPABASE_KEY: "your-key"
  QDRANT_URL: "https://your-cluster.qdrant.io"
  QDRANT_API_KEY: "your-key"
  GOOGLE_API_KEY: "your-key"
  JWT_SECRET_KEY: "your-secure-secret-key"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gim
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gim
  template:
    metadata:
      labels:
        app: gim
    spec:
      containers:
      - name: gim
        image: gim:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: gim-config
        - secretRef:
            name: gim-secrets
```

---

## Validation

### Check Configuration

```python
from src.config import get_settings

try:
    settings = get_settings()
    print("Configuration valid!")
    print(f"Transport mode: {settings.transport_mode}")
    print(f"HTTP port: {settings.http_port}")
except Exception as e:
    print(f"Configuration error: {e}")
```

### Test Services

```bash
# Test Supabase connection
curl "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_KEY"

# Test Qdrant connection
curl "$QDRANT_URL/collections" \
  -H "api-key: $QDRANT_API_KEY"

# Test Google AI (list models)
curl "https://generativelanguage.googleapis.com/v1/models?key=$GOOGLE_API_KEY"
```

---

## Troubleshooting

### "Missing required configuration"

One or more required environment variables are not set. Check:

```bash
# List all environment variables
env | grep -E "SUPABASE|QDRANT|GOOGLE|JWT"

# Verify .env file is loaded
cat .env
```

### "JWT secret key must be at least 32 characters"

Your `JWT_SECRET_KEY` is too short. Generate a new one:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### "Could not connect to Supabase/Qdrant"

Check that URLs and API keys are correct:

```bash
# Test connection manually
curl "$SUPABASE_URL/rest/v1/" -H "apikey: $SUPABASE_KEY"
curl "$QDRANT_URL/collections" -H "api-key: $QDRANT_API_KEY"
```

### Configuration not updating

- Restart the server after changing `.env`
- Check for typos in variable names (they're case-sensitive)
- Ensure `.env` file is in the correct location (project root)

---

## Security Best Practices

1. **Never commit secrets**: Use `.gitignore` to exclude `.env`
2. **Use service role in production**: More permissions than anon key
3. **Rotate secrets regularly**: Change JWT secret, API keys periodically
4. **Use environment-specific configs**: Different secrets per environment
5. **Limit API key permissions**: Use read-only keys where possible
6. **Monitor API usage**: Set up alerts for unusual activity
7. **Use HTTPS in production**: Never expose secrets over HTTP

---

## References

- [Supabase Documentation](https://supabase.com/docs)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Google AI Documentation](https://ai.google.dev/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
