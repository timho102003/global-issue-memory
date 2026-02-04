"""GIM Submit Issue Tool - Submit a resolved issue to GIM."""

from typing import Any, Dict, List, Optional

from src.db.supabase_client import insert_record
from src.exceptions import ValidationError
from src.logging_config import get_logger, set_request_context
from src.tools.base import ToolDefinition, create_text_response, create_error_response


logger = get_logger("tools.submit_issue")


def _sanitize_structured_data(data: Any) -> Any:
    """Recursively sanitize structured data (lists, dicts, strings).

    Applies pattern-based sanitization to all string values in nested
    data structures before database storage.

    Args:
        data: The data to sanitize (can be str, list, dict, or primitive).

    Returns:
        The sanitized data with the same structure.
    """
    if isinstance(data, str):
        from src.services.sanitization.secret_detector import detect_secrets
        from src.services.sanitization.pii_scrubber import scrub_pii

        secret_result = detect_secrets(data)
        pii_result = scrub_pii(secret_result.sanitized_text)
        return pii_result.sanitized_text
    elif isinstance(data, list):
        return [_sanitize_structured_data(item) for item in data]
    elif isinstance(data, dict):
        return {k: _sanitize_structured_data(v) for k, v in data.items()}
    return data


submit_issue_tool = ToolDefinition(
    name="gim_submit_issue",
    description="""Submit a RESOLVED issue to GIM to help other AI assistants.

┌─────────────────────────────────────────────────────────────────────┐
│  WHEN TO USE: After you have SUCCESSFULLY resolved an error AND    │
│  gim_search_issues found no existing solution AND the fix is       │
│  GLOBALLY USEFUL — meaning a stranger on a completely different    │
│  codebase could hit the same error.                                │
└─────────────────────────────────────────────────────────────────────┘

SUBMIT (globally reproducible — a stranger would hit this):
  ✓ Library/package version conflicts or incompatibilities
  ✓ Framework configuration pitfalls (Next.js, FastAPI, Django)
  ✓ Build tool or bundler errors (webpack, vite, esbuild, cargo)
  ✓ Deployment & CI/CD setup issues (Docker, Vercel, AWS)
  ✓ Environment or OS-specific problems (Node version, Python path)
  ✓ SDK/API breaking changes or undocumented behavior
  ✓ AI model quirks (tool calling schema, response parsing, token limits)
  ✓ Language-level gotchas (async/await traps, type system edge cases)

DO NOT SUBMIT (project-local — specific to this codebase):
  ✗ Errors that are not yet resolved
  ✗ Issues that already exist in GIM (search first)
  ✗ Fixes that haven't been tested/verified
  ✗ Database column/schema mismatches specific to this project
  ✗ Variable naming bugs or wrong function arguments
  ✗ Business logic errors unique to the project
  ✗ Missing project-internal imports or modules
  ✗ Typos in project code
  ✗ Test fixture or mock data mismatches
  ✗ User-specific file paths or local configuration values

WORKFLOW:
  1. Encounter error → Call gim_search_issues
  2. No match found → Solve the error yourself
  3. Fix verified → Apply global usefulness filter:
     → YES (stranger would hit this) → Call this tool
     → NO  (project-local issue)     → Skip submission
  4. GIM automatically:
     ├─ Sanitizes all content (removes secrets, PII, paths)
     ├─ Checks for similar issues (may link as child issue)
     ├─ Generates embeddings for future search matching
     └─ Stores the fix bundle for others to use

WHAT TO INCLUDE:
  Required:
    - error_message: The exact error text
    - root_cause: WHY the error occurred (not just WHAT)
    - fix_summary: Brief description of the solution
    - fix_steps: Step-by-step instructions
    - provider: MUST include your model provider (e.g., 'anthropic', 'openai')
    - model: MUST include your model name (e.g., 'claude-sonnet-4-20250514')

  Highly Recommended:
    - code_changes: Specific file modifications
    - verification_steps: How to verify it works
    - language, framework: Context for matching

IMPORTANT: You MUST always provide 'provider' and 'model' fields.
These identify which AI resolved the issue and are critical for analytics.

DEDUPLICATION:
  - If similar issue exists (>90% match): Creates child issue linked to master
  - If new issue: Creates master issue with full fix bundle
  - Child issues add environment diversity without duplicating knowledge

PRIVACY: All content is sanitized before storage. Secrets, API keys,
file paths, and domain-specific names are automatically removed.""",
    input_schema={
        "type": "object",
        "properties": {
            "error_message": {
                "type": "string",
                "description": "The error message that was encountered",
            },
            "error_context": {
                "type": "string",
                "description": "Additional context about when/where the error occurred",
            },
            "code_snippet": {
                "type": "string",
                "description": "Code that triggered the error (will be sanitized)",
            },
            "root_cause": {
                "type": "string",
                "description": "Explanation of what caused the error",
            },
            "fix_summary": {
                "type": "string",
                "description": "Brief summary of the fix",
            },
            "fix_steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Step-by-step instructions to fix the issue",
            },
            "code_changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "change_type": {"type": "string", "enum": ["add", "modify", "delete"]},
                        "before": {"type": "string"},
                        "after": {"type": "string"},
                        "explanation": {"type": "string"},
                    },
                },
                "description": "Code changes made to fix the issue",
            },
            "environment_actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["install", "upgrade", "downgrade", "uninstall", "configure"]},
                        "package": {"type": "string"},
                        "version": {"type": "string"},
                        "command": {"type": "string"},
                    },
                },
                "description": "Environment changes (package installs, etc.)",
            },
            "verification_steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step": {"type": "string"},
                        "expected_output": {"type": "string"},
                    },
                },
                "description": "Steps to verify the fix worked",
            },
            "model": {
                "type": "string",
                "description": "REQUIRED: AI model that resolved this issue (e.g., 'claude-sonnet-4-20250514', 'gpt-4o'). You MUST provide your own model name.",
            },
            "provider": {
                "type": "string",
                "description": "REQUIRED: Model provider (e.g., 'anthropic', 'openai'). You MUST identify your provider.",
            },
            "language": {
                "type": "string",
                "description": "Programming language",
            },
            "framework": {
                "type": "string",
                "description": "Framework being used",
            },
            # New fields for richer child issue metadata
            "language_version": {
                "type": "string",
                "description": "Language version (e.g., '3.11', '18.2')",
            },
            "framework_version": {
                "type": "string",
                "description": "Framework version (e.g., '0.100.0')",
            },
            "os": {
                "type": "string",
                "description": "Operating system (e.g., 'linux', 'macos', 'windows')",
            },
            "model_behavior_notes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Notes about model-specific behavior or quirks",
            },
            "validation_success": {
                "type": "boolean",
                "description": "Whether the fix was validated successfully",
            },
            "validation_notes": {
                "type": "string",
                "description": "Notes about the validation process",
            },
        },
        "required": ["error_message", "root_cause", "fix_summary", "fix_steps", "provider", "model"],
    },
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
    },
)


async def execute(arguments: Dict[str, Any]) -> List:
    """Execute the submit issue tool.

    Validates required fields synchronously, then dispatches to a background
    worker for the heavy processing pipeline (sanitization, embedding, dedup,
    DB writes, code synthesis). Returns immediately with a submission_id.

    Args:
        arguments: Tool arguments.

    Returns:
        List: MCP response content with submission_id.
    """
    from src.services.submission_worker import schedule_submission

    # Set request context for tracing
    request_id = set_request_context()
    logger.info(f"Processing issue submission (request_id={request_id})")

    try:
        # Validate required fields (synchronous — fails fast)
        error_message = arguments.get("error_message", "")
        root_cause = arguments.get("root_cause", "")
        fix_summary = arguments.get("fix_summary", "")
        fix_steps = arguments.get("fix_steps", [])
        provider = arguments.get("provider")
        model = arguments.get("model")

        if not error_message:
            raise ValidationError("error_message is required", field="error_message")
        if not root_cause:
            raise ValidationError("root_cause is required", field="root_cause")
        if not fix_summary:
            raise ValidationError("fix_summary is required", field="fix_summary")
        if not fix_steps:
            raise ValidationError("fix_steps is required", field="fix_steps")
        if not provider:
            raise ValidationError("provider is required (e.g., 'anthropic', 'openai')", field="provider")
        if not model:
            raise ValidationError("model is required (e.g., 'claude-sonnet-4-20250514')", field="model")

        # Dispatch to background worker
        submission_id = schedule_submission(arguments, request_id)

        # Build friendly user-facing message with security info
        friendly_message = f"""✅ Submitted for Processing

Your fix will be processed securely and help the AI community!

🔒 Automatic Security Protection:
   • API keys & secrets → Auto-removed if detected
   • Personal information → Auto-scrubbed
   • File paths → Anonymized

📋 Submission ID: {submission_id[:12]}...

Thank you for contributing!"""

        from src.models.responses import SubmitIssueAcceptedResponse
        response = SubmitIssueAcceptedResponse(
            success=True,
            message=friendly_message,
            submission_id=submission_id,
        )
        return create_text_response(response.model_dump())

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        return create_error_response(f"Validation error: {e.message}")

    except Exception as e:
        logger.exception("Unexpected error during submission")
        return create_error_response("An unexpected error occurred. Please try again later.")


def _classify_root_cause(root_cause: str) -> str:
    """Classify root cause into a RootCauseCategory value.

    Maps root cause descriptions to one of the standard categories:
    - environment: Dependencies, configuration, version issues
    - model_behavior: AI model behavior, tool calling, schema issues
    - api_integration: API, authentication, network issues
    - code_generation: Code syntax, types, logic issues
    - framework_specific: Framework-specific issues

    Args:
        root_cause: Root cause description.

    Returns:
        str: Root cause category matching RootCauseCategory enum values.
    """
    root_cause_lower = root_cause.lower()

    # Keywords mapped to RootCauseCategory values
    # environment: Dependencies, configuration, version issues
    environment_keywords = [
        "missing", "not found", "import error", "module not found",
        "dependency", "package", "install", "pip", "npm", "version",
        "incompatible", "upgrade", "downgrade", "config", "configuration",
        "setting", "environment variable", "env", "path",
    ]

    # model_behavior: AI model behavior issues
    model_behavior_keywords = [
        "model", "llm", "ai", "claude", "gpt", "openai", "anthropic",
        "tool calling", "function calling", "schema", "prompt",
        "hallucination", "context", "token", "response format",
        "tool_use", "tool use", "assistant", "completion",
    ]

    # api_integration: API and network issues
    api_integration_keywords = [
        "api", "endpoint", "request", "response", "http", "rest",
        "auth", "authentication", "permission", "forbidden", "unauthorized",
        "connection", "timeout", "network", "socket", "cors", "header",
        "rate limit", "quota", "breaking change", "deprecated",
    ]

    # code_generation: Code-related issues
    code_generation_keywords = [
        "type error", "type mismatch", "cannot be", "expected",
        "syntax", "parse", "invalid", "none", "null", "undefined",
        "nonetype", "attribute", "key error", "index", "logic",
        "incorrect", "wrong", "bug", "exception", "traceback",
    ]

    # framework_specific: Framework issues
    framework_keywords = [
        "langchain", "llamaindex", "fastapi", "django", "flask",
        "react", "next", "vue", "angular", "tensorflow", "pytorch",
        "pandas", "numpy", "framework", "library", "sdk",
    ]

    # Check in priority order
    if any(kw in root_cause_lower for kw in model_behavior_keywords):
        return "model_behavior"
    if any(kw in root_cause_lower for kw in framework_keywords):
        return "framework_specific"
    if any(kw in root_cause_lower for kw in api_integration_keywords):
        return "api_integration"
    if any(kw in root_cause_lower for kw in code_generation_keywords):
        return "code_generation"
    if any(kw in root_cause_lower for kw in environment_keywords):
        return "environment"

    # Default to environment for unknown issues
    return "environment"


async def _log_submission_event(
    issue_id: str,
    is_child: bool,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    gim_id: Optional[str] = None,
) -> None:
    """Log an issue submission event.

    This is a non-critical operation that should not fail the main submission.

    Args:
        issue_id: Issue ID.
        is_child: Whether this is a child issue.
        model: AI model used.
        provider: Model provider.
        gim_id: GIM user ID who submitted the issue.
    """
    try:
        data = {
            "event_type": "issue_submitted",
            "issue_id": issue_id,
            "model": model,
            "provider": provider,
            "metadata": {
                "is_child_issue": is_child,
            },
        }
        if gim_id:
            data["gim_id"] = gim_id
        await insert_record(table="usage_events", data=data)
    except Exception as e:
        # Log but don't fail the main operation
        logger.error(f"Failed to log submission event: {e}", exc_info=True)


# Export for server registration
submit_issue_tool.execute = execute
