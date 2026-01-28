# GIM Authentication Guide

This guide explains how GIM's authentication system works using GIM IDs, JWT tokens, and OAuth 2.1.

## Overview

GIM supports two authentication methods:

### 1. OAuth 2.1 with PKCE (Recommended for MCP Clients)

Industry-standard OAuth 2.1 with PKCE for secure MCP client authorization. MCP clients automatically discover and use OAuth via the well-known endpoint.

### 2. Direct GIM ID Exchange (Simple Integration)

Simple GIM ID to JWT token exchange for non-OAuth clients or direct API access.

Both methods use:
- **GIM ID**: A permanent UUID credential that identifies a user
- **JWT Token**: Short-lived access token for API calls

This design provides:
- Simple credential management (just store one UUID)
- Short-lived tokens for security
- Rate limiting per GIM ID
- Easy revocation
- OAuth 2.1 compliance for MCP protocol

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Client    │         │  GIM Server  │         │  Database   │
└─────────────┘         └──────────────┘         └─────────────┘
      │                        │                        │
      │  1. Create GIM ID      │                        │
      ├───────────────────────>│                        │
      │                        │  Store identity        │
      │                        ├───────────────────────>│
      │  GIM ID (UUID)         │                        │
      │<───────────────────────┤                        │
      │                        │                        │
      │  2. Exchange for JWT   │                        │
      │  (send GIM ID)         │                        │
      ├───────────────────────>│                        │
      │                        │  Validate GIM ID       │
      │                        ├───────────────────────>│
      │                        │  OK                    │
      │                        │<───────────────────────┤
      │  JWT Token             │                        │
      │<───────────────────────┤                        │
      │                        │                        │
      │  3. Use MCP tools      │                        │
      │  (with JWT token)      │                        │
      ├───────────────────────>│                        │
      │                        │  Verify JWT            │
      │                        │  Check rate limits     │
      │                        ├───────────────────────>│
      │                        │  Execute operation     │
      │  Response              │                        │
      │<───────────────────────┤                        │
```

## Transport Modes

### Stdio Mode (Default)

For MCP clients like Claude Desktop. Authentication is handled automatically through the MCP protocol.

```bash
python -m src.server --transport stdio
```

In stdio mode, authentication is **optional** and primarily used for rate limiting if configured.

### HTTP Mode

For web applications and API access. Requires JWT authentication.

```bash
python -m src.server --transport http --host 0.0.0.0 --port 8000
```

HTTP mode **requires** JWT authentication for all MCP tool calls.

## Getting Started

### Step 1: Create a GIM ID

Make a POST request to `/auth/gim-id`:

```bash
curl -X POST http://localhost:8000/auth/gim-id \
  -H "Content-Type: application/json" \
  -d '{
    "description": "My development environment",
    "metadata": {"app": "my-app"}
  }'
```

Response:

```json
{
  "gim_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-27T10:30:00Z",
  "description": "My development environment"
}
```

**Save this GIM ID!** It's your permanent credential.

### Step 2: Exchange GIM ID for JWT Token

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "gim_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Tokens expire in 1 hour by default (configurable via `ACCESS_TOKEN_TTL_HOURS`).

### Step 3: Use the Token

Include the token in the `Authorization` header:

```bash
curl http://localhost:8000/mcp/tools/gim_search_issues \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "TypeError: Cannot read property of undefined",
    "language": "typescript"
  }'
```

## OAuth 2.1 Endpoints (MCP Clients)

### GET /.well-known/oauth-authorization-server

OAuth Authorization Server Metadata (RFC 8414). MCP clients use this to discover OAuth endpoints.

**Response (200 OK)**:

```json
{
  "issuer": "http://localhost:8000",
  "authorization_endpoint": "http://localhost:8000/authorize",
  "token_endpoint": "http://localhost:8000/token",
  "registration_endpoint": "http://localhost:8000/register",
  "revocation_endpoint": "http://localhost:8000/revoke",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["none"]
}
```

### POST /register

Dynamic client registration (RFC 7591). Register a new OAuth client.

**Request Body**:

```json
{
  "redirect_uris": ["http://localhost:3000/callback"],
  "client_name": "My MCP Client",
  "grant_types": ["authorization_code", "refresh_token"]
}
```

**Response (201 Created)**:

```json
{
  "client_id": "generated-client-id",
  "client_name": "My MCP Client",
  "redirect_uris": ["http://localhost:3000/callback"],
  "grant_types": ["authorization_code", "refresh_token"]
}
```

### GET /authorize

OAuth authorization endpoint. Displays GIM ID login page.

**Query Parameters**:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `response_type` | Yes | Must be "code" |
| `client_id` | Yes | Registered client ID |
| `redirect_uri` | Yes | Must match registered URI |
| `code_challenge` | Yes | PKCE S256 code challenge |
| `code_challenge_method` | No | Must be "S256" (default) |
| `state` | No | CSRF protection state |
| `scope` | No | Requested scope |

**Example**:

```
GET /authorize?response_type=code&client_id=xxx&redirect_uri=http://localhost:3000/callback&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&code_challenge_method=S256&state=xyz
```

Returns HTML page for user to enter GIM ID.

### POST /token

OAuth token endpoint. Exchange authorization code for tokens or refresh tokens.

**Authorization Code Grant**:

```bash
curl -X POST http://localhost:8000/token \
  -d "grant_type=authorization_code" \
  -d "client_id=xxx" \
  -d "code=authorization-code" \
  -d "code_verifier=original-pkce-verifier" \
  -d "redirect_uri=http://localhost:3000/callback"
```

**Refresh Token Grant**:

```bash
curl -X POST http://localhost:8000/token \
  -d "grant_type=refresh_token" \
  -d "client_id=xxx" \
  -d "refresh_token=your-refresh-token"
```

**Response (200 OK)**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "new-refresh-token",
  "scope": null
}
```

### POST /revoke

OAuth token revocation (RFC 7009). Revoke a refresh token.

**Request Body** (form-encoded):

```
token=refresh-token-to-revoke
token_type_hint=refresh_token
```

**Response (200 OK)**:

```json
{}
```

## Direct Authentication Endpoints

### POST /auth/gim-id

Create a new GIM ID.

**Request Body** (all fields optional):

```json
{
  "description": "Optional description",
  "metadata": {
    "key": "value"
  }
}
```

**Response (201 Created)**:

```json
{
  "gim_id": "uuid-here",
  "created_at": "2026-01-27T10:30:00Z",
  "description": "Optional description"
}
```

### POST /auth/token

Exchange GIM ID for JWT access token.

**Request Body**:

```json
{
  "gim_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200 OK)**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Error Responses**:

- `401 Unauthorized`: GIM ID not found or inactive
- `400 Bad Request`: Invalid request format

### POST /auth/revoke

Revoke a GIM ID (requires authentication with token for that GIM ID).

**Headers**:

```
Authorization: Bearer <your-jwt-token>
```

**Request Body**:

```json
{
  "gim_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200 OK)**:

```json
{
  "success": true,
  "message": "GIM ID revoked"
}
```

**Error Responses**:

- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Cannot revoke a GIM ID you don't own
- `404 Not Found`: GIM ID not found

### GET /auth/rate-limit

Check rate limit status (requires authentication).

**Headers**:

```
Authorization: Bearer <your-jwt-token>
```

**Response (200 OK)**:

```json
{
  "gim_id": "550e8400-e29b-41d4-a716-446655440000",
  "daily_limit": 100,
  "daily_remaining": 87,
  "reset_at": "2026-01-28T00:00:00Z"
}
```

**Response Headers**:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1706400000
```

### GET /health

Health check endpoint (no authentication required).

**Response (200 OK)**:

```json
{
  "status": "healthy",
  "service": "gim-mcp"
}
```

## JWT Token Details

### Token Claims

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // GIM ID
  "iss": "gim-mcp",                                // Issuer
  "aud": "gim-clients",                            // Audience
  "exp": 1706371200,                               // Expiration (Unix timestamp)
  "iat": 1706367600,                               // Issued at (Unix timestamp)
  "gim_identity_id": "internal-uuid-here"          // Internal DB reference
}
```

### Token Configuration

Configure via environment variables:

```env
JWT_SECRET_KEY=your-secure-secret-key-min-32-chars  # Required, min 32 chars
AUTH_ISSUER=gim-mcp                                  # Optional, default shown
AUTH_AUDIENCE=gim-clients                            # Optional, default shown
ACCESS_TOKEN_TTL_HOURS=1                             # Optional, default 1 hour
```

**Security Note**: The `JWT_SECRET_KEY` must be:
- At least 32 characters long
- Cryptographically random
- Kept secret and never committed to version control
- Rotated periodically

Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Rate Limiting

GIM implements per-operation rate limiting to ensure fair usage.

### Rate-Limited Operations

- `gim_search_issues`: 100 per day (default)
- `gim_get_fix_bundle`: 100 per day (default)

### Unlimited Operations

- `gim_submit_issue`: Unlimited (we want contributions!)
- `gim_confirm_fix`: Unlimited (feedback is valuable)
- `gim_report_usage`: Unlimited (analytics)

### Rate Limit Configuration

Set the default daily search limit:

```env
DEFAULT_DAILY_SEARCH_LIMIT=100  # Default value
```

### Rate Limit Headers

All authenticated responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1706400000  # Unix timestamp
```

### Handling Rate Limit Errors

When rate limit is exceeded, the server returns:

**Status**: 429 Too Many Requests

**Body**:

```json
{
  "error": "rate_limit_exceeded",
  "error_description": "Rate limit exceeded for gim_search_issues: 100/100 (resets at 2026-01-28T00:00:00Z)"
}
```

The `reset_at` field tells you when you can make requests again.

### Daily Reset

Rate limits reset daily at midnight UTC. The reset time is tracked per GIM ID in the database.

## Security Considerations

### GIM ID Storage

- Store GIM IDs securely (they're like API keys)
- Don't hardcode them in source code
- Use environment variables or secure key stores
- Don't commit them to version control

### Token Expiration

- Tokens expire after 1 hour by default
- Implement token refresh logic in your client
- Don't store tokens longer than necessary

### Revocation

- Revoke GIM IDs if compromised
- Revocation is immediate and affects all tokens
- Use the `/auth/revoke` endpoint

### Transport Security

- Always use HTTPS in production
- The JWT secret must be kept confidential
- Rotate JWT secrets periodically

## Client Implementation Example

### Python

```python
import httpx
from uuid import UUID

class GIMClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.gim_id = None
        self.access_token = None

    async def create_gim_id(self, description: str = None):
        """Create a new GIM ID."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/gim-id",
                json={"description": description} if description else {}
            )
            response.raise_for_status()
            data = response.json()
            self.gim_id = UUID(data["gim_id"])
            return self.gim_id

    async def get_token(self):
        """Exchange GIM ID for JWT token."""
        if not self.gim_id:
            raise ValueError("No GIM ID set")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/token",
                json={"gim_id": str(self.gim_id)}
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            return self.access_token

    async def search_issues(self, error_message: str, **kwargs):
        """Search for issues."""
        if not self.access_token:
            await self.get_token()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp/tools/gim_search_issues",
                headers=headers,
                json={"error_message": error_message, **kwargs}
            )

            # Handle rate limiting
            if response.status_code == 429:
                reset_time = response.headers.get("X-RateLimit-Reset")
                raise RateLimitExceeded(f"Rate limit exceeded. Resets at {reset_time}")

            response.raise_for_status()
            return response.json()

# Usage
client = GIMClient("http://localhost:8000")
await client.create_gim_id("My app")
results = await client.search_issues("TypeError: undefined is not an object")
```

## Troubleshooting

### "Invalid or expired token"

- Your JWT token has expired (check `expires_in` from token response)
- Request a new token using `/auth/token`

### "GIM ID not found or inactive"

- The GIM ID doesn't exist in the database
- The GIM ID has been revoked
- Check that you're using the correct GIM ID

### "Rate limit exceeded"

- You've hit your daily limit for search operations
- Check `/auth/rate-limit` to see when limits reset
- Consider implementing caching on your side

### "Authorization header required"

- You forgot to include the `Authorization: Bearer <token>` header
- Check that the header format is correct

## FAQ

**Q: Can I use multiple GIM IDs?**

Yes! Create as many as you need. Each has independent rate limits.

**Q: What happens if I lose my GIM ID?**

You'll need to create a new one. GIM IDs can't be recovered if lost.

**Q: How do I increase my rate limit?**

Contact the server administrator. They can adjust `DEFAULT_DAILY_SEARCH_LIMIT` or modify individual GIM ID limits in the database.

**Q: Can I use GIM without authentication?**

Only in stdio mode. HTTP mode requires authentication for all operations.

**Q: Do tokens persist across server restarts?**

Tokens are stateless JWTs validated by signature. They remain valid until expiration, even after server restarts. However, if the JWT secret changes, all tokens become invalid.
