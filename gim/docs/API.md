# GIM API Reference

Complete reference for GIM's HTTP endpoints and MCP tools.

## Base URL

```
http://localhost:8000  # Development
https://your-domain.com  # Production
```

## Authentication

All MCP tool endpoints require JWT authentication in HTTP mode:

```
Authorization: Bearer <your-jwt-token>
```

See [Authentication Guide](AUTHENTICATION.md) for details.

## HTTP Endpoints

### Authentication Endpoints

#### POST /auth/gim-id

Create a new GIM ID.

**Authentication**: None required

**Request Body** (optional):

```json
{
  "description": "My development environment",
  "metadata": {
    "app": "my-app",
    "environment": "production"
  }
}
```

**Response (201 Created)**:

```json
{
  "gim_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-27T10:30:00Z",
  "description": "My development environment"
}
```

**Error Responses**:

- `500 Internal Server Error`: Failed to create GIM ID

---

#### POST /auth/token

Exchange GIM ID for JWT access token.

**Authentication**: None required

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

---

#### POST /auth/revoke

Revoke a GIM ID permanently.

**Authentication**: Required (Bearer token for the GIM ID being revoked)

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

---

#### GET /auth/rate-limit

Check current rate limit status.

**Authentication**: Required

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

**Error Responses**:

- `401 Unauthorized`: Missing or invalid token

---

#### GET /health

Health check endpoint.

**Authentication**: None required

**Response (200 OK)**:

```json
{
  "status": "healthy",
  "service": "gim-mcp"
}
```

---

## MCP Tools

All MCP tools require authentication in HTTP mode.

### gim_search_issues

Search for known issues matching an error message.

**Rate Limited**: Yes (100/day default)

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `error_message` | string | Yes | The error message to search for |
| `model` | string | No | AI model being used (e.g., "gpt-4", "claude-opus") |
| `provider` | string | No | Model provider (e.g., "openai", "anthropic") |
| `language` | string | No | Programming language (e.g., "python", "typescript") |
| `framework` | string | No | Framework being used (e.g., "react", "fastapi") |
| `limit` | integer | No | Maximum results to return (default: 5, max: 20) |

**Example Request**:

```json
{
  "error_message": "TypeError: Cannot read property 'map' of undefined",
  "language": "typescript",
  "framework": "react",
  "limit": 5
}
```

**Example Response**:

```json
{
  "results": [
    {
      "issue_id": "123e4567-e89b-12d3-a456-426614174000",
      "canonical_error": "TypeError: Cannot read property of undefined",
      "canonical_fix": "Add null check before accessing property",
      "similarity_score": 0.95,
      "occurrence_count": 42,
      "fix_success_rate": 0.89,
      "model": "gpt-4",
      "provider": "openai",
      "language": "typescript",
      "framework": "react",
      "created_at": "2026-01-20T10:30:00Z",
      "updated_at": "2026-01-27T08:15:00Z"
    }
  ],
  "total_results": 1,
  "query_time_ms": 45
}
```

**Error Responses**:

- `401 Unauthorized`: Missing or invalid authentication
- `429 Too Many Requests`: Rate limit exceeded
- `400 Bad Request`: Invalid parameters

---

### gim_get_fix_bundle

Get detailed fix information for a specific issue, including related issues.

**Rate Limited**: Yes (100/day default)

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_id` | string (UUID) | Yes | The issue ID to get fix bundle for |
| `include_related` | boolean | No | Include related issues (default: true) |

**Example Request**:

```json
{
  "issue_id": "123e4567-e89b-12d3-a456-426614174000",
  "include_related": true
}
```

**Example Response**:

```json
{
  "issue": {
    "issue_id": "123e4567-e89b-12d3-a456-426614174000",
    "canonical_error": "TypeError: Cannot read property of undefined",
    "canonical_fix": "Add null check before accessing property",
    "detailed_explanation": "This error occurs when attempting to access a property on an undefined or null value...",
    "code_example": "// Before:\nconst value = obj.property.map(x => x);\n\n// After:\nconst value = obj.property?.map(x => x) ?? [];",
    "occurrence_count": 42,
    "fix_success_rate": 0.89,
    "model": "gpt-4",
    "provider": "openai",
    "language": "typescript",
    "framework": "react",
    "tags": ["null-safety", "optional-chaining"],
    "created_at": "2026-01-20T10:30:00Z",
    "updated_at": "2026-01-27T08:15:00Z"
  },
  "related_issues": [
    {
      "issue_id": "223e4567-e89b-12d3-a456-426614174001",
      "canonical_error": "TypeError: Cannot read property 'length' of undefined",
      "similarity_score": 0.87,
      "fix_success_rate": 0.92
    }
  ],
  "total_related": 3
}
```

**Error Responses**:

- `401 Unauthorized`: Missing or invalid authentication
- `429 Too Many Requests`: Rate limit exceeded
- `404 Not Found`: Issue not found
- `400 Bad Request`: Invalid issue ID format

---

### gim_submit_issue

Submit a new issue with fix to the knowledge base.

**Rate Limited**: No (unlimited submissions encouraged)

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `error_message` | string | Yes | The error message encountered |
| `fix_applied` | string | Yes | The fix that was applied |
| `model` | string | No | AI model being used |
| `provider` | string | No | Model provider |
| `language` | string | No | Programming language |
| `framework` | string | No | Framework being used |
| `environment` | object | No | Environment details (OS, versions, etc.) |

**Example Request**:

```json
{
  "error_message": "TypeError: Cannot read property 'map' of undefined",
  "fix_applied": "Added optional chaining: obj.property?.map(x => x) ?? []",
  "model": "gpt-4",
  "provider": "openai",
  "language": "typescript",
  "framework": "react",
  "environment": {
    "os": "darwin",
    "node_version": "20.10.0",
    "typescript_version": "5.3.3"
  }
}
```

**Example Response**:

```json
{
  "issue_id": "323e4567-e89b-12d3-a456-426614174002",
  "status": "created",
  "message": "Issue submitted successfully",
  "sanitization_confidence": 0.98,
  "similar_existing_issues": [
    {
      "issue_id": "123e4567-e89b-12d3-a456-426614174000",
      "similarity_score": 0.85,
      "suggestion": "Consider confirming if this is a duplicate"
    }
  ]
}
```

**Error Responses**:

- `401 Unauthorized`: Missing or invalid authentication
- `400 Bad Request`: Invalid parameters or sanitization failed
- `500 Internal Server Error`: Failed to store issue

---

### gim_confirm_fix

Confirm whether a suggested fix worked or not (feedback loop).

**Rate Limited**: No (unlimited feedback encouraged)

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_id` | string (UUID) | Yes | The issue ID being confirmed |
| `fix_worked` | boolean | Yes | Whether the fix resolved the issue |
| `feedback` | string | No | Optional detailed feedback |

**Example Request**:

```json
{
  "issue_id": "123e4567-e89b-12d3-a456-426614174000",
  "fix_worked": true,
  "feedback": "Worked perfectly! Optional chaining solved the problem."
}
```

**Example Response**:

```json
{
  "status": "confirmed",
  "message": "Thank you for your feedback",
  "issue_id": "123e4567-e89b-12d3-a456-426614174000",
  "updated_success_rate": 0.90
}
```

**Error Responses**:

- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Issue not found
- `400 Bad Request`: Invalid parameters

---

### gim_report_usage

Report usage analytics events (for telemetry and monitoring).

**Rate Limited**: No (unlimited reporting)

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_type` | string | Yes | Type of event (e.g., "search_performed", "fix_applied") |
| `metadata` | object | No | Additional event metadata |

**Example Request**:

```json
{
  "event_type": "search_performed",
  "metadata": {
    "query_time_ms": 45,
    "results_count": 3,
    "filters_used": ["language", "framework"]
  }
}
```

**Example Response**:

```json
{
  "status": "recorded",
  "message": "Event recorded successfully",
  "event_id": "423e4567-e89b-12d3-a456-426614174003"
}
```

**Error Responses**:

- `401 Unauthorized`: Missing or invalid authentication
- `400 Bad Request`: Invalid event type or metadata

---

## Rate Limiting

### Rate Limit Headers

All authenticated responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1706400000
```

### Rate Limit Error Response

When rate limit is exceeded:

**Status**: 429 Too Many Requests

**Body**:

```json
{
  "error": "rate_limit_exceeded",
  "error_description": "Rate limit exceeded for gim_search_issues: 100/100 (resets at 2026-01-28T00:00:00Z)",
  "limit": 100,
  "used": 100,
  "reset_at": "2026-01-28T00:00:00Z"
}
```

**Headers**:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706400000
Retry-After: 43200
```

### Operations by Rate Limit Status

**Rate Limited (100/day)**:
- `gim_search_issues`
- `gim_get_fix_bundle`

**Unlimited**:
- `gim_submit_issue`
- `gim_confirm_fix`
- `gim_report_usage`

---

## Error Responses

All errors follow this format:

```json
{
  "error": "error_code",
  "error_description": "Human-readable description"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `invalid_request` | 400 | Malformed request or invalid parameters |
| `unauthorized` | 401 | Missing or invalid authentication |
| `forbidden` | 403 | Authenticated but not authorized for this resource |
| `not_found` | 404 | Resource not found |
| `rate_limit_exceeded` | 429 | Too many requests |
| `server_error` | 500 | Internal server error |
| `invalid_grant` | 401 | Invalid GIM ID during token exchange |

---

## SDK Examples

### Python

```python
from gim_client import GIMClient

# Initialize client
client = GIMClient("http://localhost:8000")

# Create GIM ID (do this once, save the ID)
gim_id = await client.create_gim_id("My app")

# Get token
await client.authenticate(gim_id)

# Search for issues
results = await client.search_issues(
    error_message="TypeError: undefined is not an object",
    language="typescript",
    framework="react"
)

# Get fix bundle
fix_bundle = await client.get_fix_bundle(
    issue_id=results["results"][0]["issue_id"]
)

# Submit new issue
await client.submit_issue(
    error_message="New error...",
    fix_applied="Fixed by...",
    language="python"
)

# Confirm fix worked
await client.confirm_fix(
    issue_id=results["results"][0]["issue_id"],
    fix_worked=True,
    feedback="Worked great!"
)
```

### TypeScript

```typescript
import { GIMClient } from 'gim-client';

// Initialize client
const client = new GIMClient('http://localhost:8000');

// Create GIM ID (do this once, save the ID)
const { gim_id } = await client.createGIMId('My app');

// Get token
await client.authenticate(gim_id);

// Search for issues
const results = await client.searchIssues({
  errorMessage: 'TypeError: undefined is not an object',
  language: 'typescript',
  framework: 'react',
});

// Get fix bundle
const fixBundle = await client.getFixBundle({
  issueId: results.results[0].issue_id,
});

// Submit new issue
await client.submitIssue({
  errorMessage: 'New error...',
  fixApplied: 'Fixed by...',
  language: 'typescript',
});

// Confirm fix worked
await client.confirmFix({
  issueId: results.results[0].issue_id,
  fixWorked: true,
  feedback: 'Worked great!',
});
```

### cURL

```bash
# Create GIM ID
curl -X POST http://localhost:8000/auth/gim-id \
  -H "Content-Type: application/json" \
  -d '{"description": "My app"}'
# Save the returned gim_id

# Get token
TOKEN=$(curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"gim_id": "YOUR_GIM_ID"}' | jq -r '.access_token')

# Search issues
curl http://localhost:8000/mcp/tools/gim_search_issues \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "TypeError: undefined is not an object",
    "language": "typescript"
  }'

# Check rate limits
curl http://localhost:8000/auth/rate-limit \
  -H "Authorization: Bearer $TOKEN"
```

---

## Versioning

The API currently has no versioning. Breaking changes will be announced with migration guides.

Future versions may use URL-based versioning:
- `/v1/auth/token`
- `/v2/auth/token`

---

## Changelog

### v0.1.0 (2026-01-27)

- Initial release
- Authentication endpoints
- MCP tools: search, get_fix_bundle, submit, confirm, report
- Rate limiting for search operations
- JWT token-based authentication

---

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
