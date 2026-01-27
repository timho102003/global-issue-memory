# GIM API Reference

This document provides detailed API specifications for all GIM MCP tools and data models.

## MCP Tools

All tools follow the MCP (Model Context Protocol) specification and return structured JSON responses.

### 1. gim_search_issues

Search Global Issue Memory for known issues matching an error.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "error_message": {
      "type": "string",
      "description": "The error message or stack trace"
    },
    "model": {
      "type": "string",
      "description": "Model name (e.g., claude-3-opus-20240229)"
    },
    "provider": {
      "type": "string",
      "description": "Provider (e.g., anthropic, openai, google)"
    },
    "environment": {
      "type": "object",
      "properties": {
        "language": { "type": "string" },
        "framework": { "type": "string" },
        "os": { "type": "string" }
      }
    },
    "limit": {
      "type": "integer",
      "default": 5,
      "description": "Maximum number of results to return"
    }
  },
  "required": ["error_message"]
}
```

**Example Request:**

```python
await mcp_client.call_tool("gim_search_issues", {
    "error_message": "AttributeError: module 'langchain.tools' has no attribute 'tool'",
    "model": "claude-3-opus-20240229",
    "provider": "anthropic",
    "environment": {
        "language": "python",
        "framework": "langchain"
    },
    "limit": 5
})
```

**Response:**

```json
{
  "issues": [
    {
      "issue_id": "550e8400-e29b-41d4-a716-446655440000",
      "canonical_title": "LangChain @tool decorator moved to langchain_core",
      "root_cause_category": "API/Integration - Endpoint Deprecation",
      "relevance_score": 0.95,
      "confidence_score": 0.88,
      "verification_count": 23,
      "last_confirmed_at": "2025-01-20T15:30:00Z",
      "affected_models": [
        {
          "provider": "anthropic",
          "model_name": "claude-3-opus-20240229"
        }
      ]
    }
  ],
  "total_results": 1
}
```

---

### 2. gim_get_fix_bundle

Get the validated fix bundle for a specific issue.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "issue_id": {
      "type": "string",
      "description": "The master issue ID (UUID)"
    }
  },
  "required": ["issue_id"]
}
```

**Example Request:**

```python
await mcp_client.call_tool("gim_get_fix_bundle", {
    "issue_id": "550e8400-e29b-41d4-a716-446655440000"
})
```

**Response:**

```json
{
  "issue_id": "550e8400-e29b-41d4-a716-446655440000",
  "canonical_title": "LangChain @tool decorator moved to langchain_core",
  "root_cause": "LangChain 0.2.x moved the @tool decorator to langchain_core.tools",
  "fix_bundle": {
    "env_actions": [
      {
        "order": 1,
        "type": "upgrade",
        "command": "pip install langchain-core>=0.2.0",
        "explanation": "Install langchain-core which contains the new tool decorator location"
      }
    ],
    "constraints": {
      "working_versions": {
        "langchain-core": ">=0.2.0",
        "python": ">=3.9"
      },
      "incompatible_with": [
        "langchain<0.2.0 (use old import path)"
      ],
      "required_environment": []
    },
    "verification": [
      {
        "order": 1,
        "command": "python -c \"from langchain_core.tools import tool; print('OK')\"",
        "expected_output": "OK"
      }
    ],
    "code_fix": "# Fixed code\nfrom langchain_core.tools import tool  # <-- Correct import path\n\n@tool\ndef search(query: str) -> str:\n    \"\"\"Search for information.\"\"\"\n    return f\"Results for: {query}\""
  },
  "confidence_score": 0.88,
  "verification_count": 23
}
```

---

### 3. gim_submit_issue

Submit a RESOLVED issue to Global Issue Memory. **Only call this AFTER you have successfully fixed the issue.**

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "error_description": {
      "type": "string",
      "description": "Clear description of the error (will be sanitized)"
    },
    "error_message": {
      "type": "string",
      "description": "The actual error message or stack trace (will be sanitized)"
    },
    "code_snippet": {
      "type": "string",
      "description": "Minimal code that reproduces the issue. MUST be sanitized: no secrets, no PII, no business logic, generic names only."
    },
    "root_cause": {
      "type": "string",
      "description": "What caused the issue (e.g., 'version mismatch', 'missing config')"
    },
    "fix_bundle": {
      "type": "object",
      "description": "The working solution - REQUIRED",
      "properties": {
        "env_actions": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": {
                "type": "string",
                "enum": ["install", "upgrade", "downgrade", "config", "flag", "command"]
              },
              "command": { "type": "string" },
              "explanation": { "type": "string" }
            }
          }
        },
        "constraints": {
          "type": "object",
          "properties": {
            "working_versions": { "type": "object" },
            "incompatible_with": {
              "type": "array",
              "items": { "type": "string" }
            }
          }
        },
        "verification": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "command": { "type": "string" },
              "expected_output": { "type": "string" }
            }
          }
        },
        "code_fix": {
          "type": "string",
          "description": "The corrected code snippet (sanitized, minimal)"
        }
      },
      "required": ["env_actions", "verification"]
    },
    "model": {
      "type": "string",
      "description": "Model that resolved the issue"
    },
    "provider": {
      "type": "string",
      "description": "Provider of the model"
    },
    "environment": {
      "type": "object",
      "properties": {
        "language": { "type": "string" },
        "language_version": { "type": "string" },
        "framework": { "type": "string" },
        "framework_version": { "type": "string" },
        "os": { "type": "string" }
      }
    }
  },
  "required": ["error_description", "root_cause", "fix_bundle", "model", "provider"]
}
```

**Example Request:**

```python
await mcp_client.call_tool("gim_submit_issue", {
    "error_description": "LangChain tool decorator causes AttributeError when using with Claude API",
    "error_message": "AttributeError: module 'langchain.tools' has no attribute 'tool'",
    "code_snippet": """# Minimal reproducible example
from langchain.tools import tool  # <-- ERROR: 'tool' not found

@tool
def search(query: str) -> str:
    \"\"\"Search for information.\"\"\"
    return f"Results for: {query}"
""",
    "root_cause": "LangChain 0.2.x moved the @tool decorator to langchain_core.tools",
    "fix_bundle": {
        "env_actions": [
            {
                "order": 1,
                "type": "upgrade",
                "command": "pip install langchain-core>=0.2.0",
                "explanation": "Install langchain-core which contains the new tool decorator location"
            }
        ],
        "constraints": {
            "working_versions": {
                "langchain-core": ">=0.2.0",
                "python": ">=3.9"
            },
            "incompatible_with": ["langchain<0.2.0 (use old import path)"]
        },
        "verification": [
            {
                "order": 1,
                "command": "python -c \"from langchain_core.tools import tool; print('OK')\"",
                "expected_output": "OK"
            }
        ],
        "code_fix": """# Fixed code
from langchain_core.tools import tool  # <-- Correct import path

@tool
def search(query: str) -> str:
    \"\"\"Search for information.\"\"\"
    return f"Results for: {query}"
"""
    },
    "model": "claude-3-opus-20240229",
    "provider": "anthropic",
    "environment": {
        "language": "python",
        "language_version": "3.11",
        "framework": "langchain",
        "framework_version": "0.2.0",
        "os": "macOS"
    }
})
```

**Response (Success):**

```json
{
  "status": "created",
  "issue_id": "550e8400-e29b-41d4-a716-446655440000",
  "master_issue_id": "660e8400-e29b-41d4-a716-446655440000",
  "merged": true,
  "message": "Issue submitted successfully and merged with existing master issue"
}
```

**Response (Rejected - Sanitization Failed):**

```json
{
  "status": "rejected",
  "reason": "sanitization_failed",
  "details": "Detected 3 potential secrets in submission. Please remove sensitive data and resubmit.",
  "confidence_score": 0.72
}
```

---

### 4. gim_confirm_fix

Report whether a fix bundle worked. This data is stored for analytics and confidence scoring.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "issue_id": {
      "type": "string",
      "description": "The master issue ID (UUID)"
    },
    "success": {
      "type": "boolean",
      "description": "Whether the fix resolved the issue"
    },
    "environment": {
      "type": "object",
      "description": "Environment where fix was applied"
    },
    "notes": {
      "type": "string",
      "description": "Optional notes about the fix attempt"
    },
    "session_id": {
      "type": "string",
      "description": "AI assistant session identifier for tracking"
    }
  },
  "required": ["issue_id", "success"]
}
```

**Example Request:**

```python
await mcp_client.call_tool("gim_confirm_fix", {
    "issue_id": "550e8400-e29b-41d4-a716-446655440000",
    "success": True,
    "environment": {
        "language": "python",
        "language_version": "3.11",
        "os": "macOS"
    },
    "notes": "Fix worked perfectly on first try",
    "session_id": "session_abc123"
})
```

**Response:**

```json
{
  "status": "confirmed",
  "issue_id": "550e8400-e29b-41d4-a716-446655440000",
  "updated_confidence": 0.89,
  "updated_verification_count": 24
}
```

---

### 5. gim_report_usage

Report usage event to GIM server for analytics. Called automatically by MCP on search/fix operations.

**Input Schema:**

```json
{
  "type": "object",
  "properties": {
    "event_type": {
      "type": "string",
      "enum": ["search", "fix_retrieved", "fix_applied", "fix_confirmed", "issue_submitted"],
      "description": "Type of usage event"
    },
    "issue_id": {
      "type": "string",
      "description": "Related issue ID if applicable"
    },
    "session_id": {
      "type": "string",
      "description": "AI assistant session identifier"
    },
    "model": {
      "type": "string",
      "description": "Model making the request"
    },
    "provider": {
      "type": "string",
      "description": "Provider of the model"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["event_type", "session_id", "timestamp"]
}
```

**Example Request:**

```python
await mcp_client.call_tool("gim_report_usage", {
    "event_type": "fix_retrieved",
    "issue_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "session_abc123",
    "model": "claude-3-opus-20240229",
    "provider": "anthropic",
    "timestamp": "2025-01-27T10:00:00Z"
})
```

**Response:**

```json
{
  "status": "recorded",
  "event_id": "770e8400-e29b-41d4-a716-446655440000"
}
```

---

## Data Models

### MasterIssue

Represents a canonical issue with aggregated knowledge.

```python
class MasterIssue(BaseModel):
    id: UUID
    canonical_title: str
    root_cause_category: str
    description: Optional[str]

    # Model awareness
    affected_models: List[ModelInfo]
    model_specific_notes: Dict[str, str] = {}

    # Fix bundle
    fix_bundle: FixBundle

    # Trust signals
    confidence_score: float  # 0.0 - 1.0
    child_issue_count: int = 0
    environment_coverage: List[str] = []
    verification_count: int = 0
    last_confirmed_at: Optional[datetime] = None

    # Metadata
    created_at: datetime
    updated_at: datetime
    status: Literal["active", "superseded", "invalid"] = "active"
```

### ChildIssue

Represents a specific instance of an issue that contributes to a MasterIssue.

```python
class ChildIssue(BaseModel):
    id: UUID
    master_issue_id: UUID

    # Contribution type
    contribution_type: Literal["environment", "symptom", "model_quirk", "validation"]

    # Content
    environment: EnvironmentInfo
    symptoms: List[str] = []
    model_info: ModelInfo
    validation_result: Optional[ValidationResult] = None

    # Sanitized content only
    sanitized_error: str
    sanitized_context: str

    created_at: datetime
```

### FixBundle

Contains a complete, actionable fix for an issue.

```python
class FixBundle(BaseModel):
    # Required
    env_actions: List[EnvAction]  # Ordered list
    constraints: Constraints
    verification: List[VerificationStep]

    # Optional
    patch_diff: Optional[str] = None  # Unified diff format
    code_fix: Optional[str] = None    # Fixed code snippet
```

### EnvAction

A single action to resolve an issue.

```python
class EnvAction(BaseModel):
    order: int
    type: Literal["install", "upgrade", "downgrade", "config", "flag", "command"]
    command: str
    explanation: str
```

### Constraints

Working conditions and incompatibilities for a fix.

```python
class Constraints(BaseModel):
    working_versions: Dict[str, str] = {}  # e.g., {"python": ">=3.9"}
    incompatible_with: List[str] = []
    required_environment: List[str] = []
```

### VerificationStep

A step to verify a fix worked.

```python
class VerificationStep(BaseModel):
    order: int
    command: str
    expected_output: str
```

### ModelInfo

Information about an AI model.

```python
class ModelInfo(BaseModel):
    provider: Literal["anthropic", "openai", "google", "groq", "together", "local", "other"]
    model_name: str
    model_version: Optional[str] = None
    behavior_notes: List[str] = []
```

### EnvironmentInfo

Technical environment where an issue occurred.

```python
class EnvironmentInfo(BaseModel):
    language: Optional[str] = None
    language_version: Optional[str] = None
    framework: Optional[str] = None
    framework_version: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    additional_context: Dict[str, str] = {}
```

### UsageEvent

A single usage event for analytics.

```python
class UsageEvent(BaseModel):
    id: UUID
    event_type: Literal["search", "fix_retrieved", "fix_applied", "fix_confirmed", "issue_submitted"]
    issue_id: Optional[UUID] = None
    session_id: str
    model: Optional[str] = None
    provider: Optional[str] = None
    success: Optional[bool] = None  # For fix_confirmed events
    timestamp: datetime
```

### IssueUsageStats

Usage statistics for a specific issue.

```python
class IssueUsageStats(BaseModel):
    issue_id: UUID
    total_queries: int = 0
    total_fix_retrieved: int = 0
    total_fix_applied: int = 0
    total_resolved: int = 0
    resolution_rate: float = 0.0  # resolved / applied
    last_queried_at: Optional[datetime] = None
    last_resolved_at: Optional[datetime] = None
```

### GlobalUsageStats

Global usage statistics across all issues.

```python
class GlobalUsageStats(BaseModel):
    total_queries: int = 0
    total_issues_resolved: int = 0
    total_issues_submitted: int = 0
    active_sessions_24h: int = 0
    queries_24h: int = 0
    resolutions_24h: int = 0
    top_queried_issues: List[UUID] = []
    top_resolved_issues: List[UUID] = []
```

---

## Error Responses

All tools return errors in a consistent format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

**Common Error Codes:**

| Code | Description |
|------|-------------|
| `validation_error` | Input validation failed |
| `sanitization_failed` | Could not safely sanitize submission |
| `not_found` | Issue not found |
| `insufficient_data` | Missing required data |
| `rate_limit_exceeded` | Too many requests |
| `internal_error` | Server error |

---

## Rate Limits

**Current:** No rate limits enforced (MVP)

**Planned:**
- 100 searches per session per hour
- 10 submissions per session per day
- 1000 confirmations per session per day

---

## Pagination

For endpoints returning multiple results:

```json
{
  "issues": [...],
  "total_results": 150,
  "page": 1,
  "page_size": 10,
  "next_page": "cursor_token_here"
}
```

**Note:** Pagination not yet implemented for MVP.

---

## Versioning

**Current API Version:** v1 (implicit)

Future versions will use explicit versioning in tool names:
- `gim_v2_search_issues`
- Or version in request: `{"api_version": "v2"}`

---

## References

- [Product Requirements Document](PRD_Global_Issue_Memory.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Setup Guide](SETUP.md)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
