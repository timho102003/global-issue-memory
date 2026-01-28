"""GIM Submit Issue Tool - Submit a resolved issue to GIM."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config import get_settings
from src.db.supabase_client import insert_record, query_records
from src.db.qdrant_client import upsert_issue_vectors, search_similar_issues
from src.services.embedding_service import generate_issue_embeddings
from src.services.sanitization.pipeline import run_sanitization_pipeline, quick_sanitize
from src.tools.base import ToolDefinition, create_text_response, create_error_response


submit_issue_tool = ToolDefinition(
    name="gim_submit_issue",
    description="""Submit a RESOLVED issue to GIM (Global Issue Memory).

Use this ONLY after you have successfully resolved an error.
The submission will be automatically sanitized to remove sensitive information.

Requirements:
- Must include the error that was encountered
- Must include the working fix (fix_bundle)
- Solution must have been verified to work

The tool will:
1. Sanitize all content (remove secrets, PII, domain-specific names)
2. Check for similar existing issues
3. Create new master issue or add as child issue
4. Store the verified fix bundle""",
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
                "description": "AI model that resolved this issue",
            },
            "provider": {
                "type": "string",
                "description": "Model provider (e.g., 'anthropic', 'openai')",
            },
            "language": {
                "type": "string",
                "description": "Programming language",
            },
            "framework": {
                "type": "string",
                "description": "Framework being used",
            },
        },
        "required": ["error_message", "root_cause", "fix_summary", "fix_steps"],
    },
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
    },
)


async def execute(arguments: Dict[str, Any]) -> List:
    """Execute the submit issue tool.

    Args:
        arguments: Tool arguments.

    Returns:
        List: MCP response content.
    """
    try:
        # Extract required arguments
        error_message = arguments.get("error_message", "")
        error_context = arguments.get("error_context", "")
        code_snippet = arguments.get("code_snippet", "")
        root_cause = arguments.get("root_cause", "")
        fix_summary = arguments.get("fix_summary", "")
        fix_steps = arguments.get("fix_steps", [])
        code_changes = arguments.get("code_changes", [])
        environment_actions = arguments.get("environment_actions", [])
        verification_steps = arguments.get("verification_steps", [])
        model = arguments.get("model")
        provider = arguments.get("provider")
        language = arguments.get("language")
        framework = arguments.get("framework")

        # Validate required fields
        if not error_message:
            return create_error_response("error_message is required")
        if not root_cause:
            return create_error_response("root_cause is required")
        if not fix_summary:
            return create_error_response("fix_summary is required")
        if not fix_steps:
            return create_error_response("fix_steps is required")

        # Run sanitization pipeline
        sanitization_result = await run_sanitization_pipeline(
            error_message=error_message,
            error_context=error_context,
            code_snippet=code_snippet,
            use_llm=True,
        )

        # Also sanitize root cause and fix summary
        sanitized_root_cause, _ = quick_sanitize(root_cause)
        sanitized_fix_summary, _ = quick_sanitize(fix_summary)
        sanitized_fix_steps = [quick_sanitize(step)[0] for step in fix_steps]

        # Generate embeddings for similarity search
        embeddings = await generate_issue_embeddings(
            error_message=sanitization_result.sanitized_error,
            root_cause=sanitized_root_cause,
            fix_summary=sanitized_fix_summary,
        )

        # Check for similar existing issues
        settings = get_settings()
        similar_issues = await search_similar_issues(
            query_vector=embeddings["error_signature"],
            vector_name="error_signature",
            limit=5,
            score_threshold=settings.similarity_merge_threshold,
        )

        # Determine if this should be a new master issue or child issue
        is_child_issue = False
        parent_issue_id = None

        if similar_issues and similar_issues[0]["score"] >= settings.similarity_merge_threshold:
            # High similarity - create child issue
            is_child_issue = True
            parent_issue_id = similar_issues[0]["payload"].get("issue_id")

        # Create issue record
        issue_id = str(uuid.uuid4())

        if is_child_issue and parent_issue_id:
            # Create child issue
            await insert_record(
                table="child_issues",
                data={
                    "id": issue_id,
                    "master_issue_id": parent_issue_id,
                    "original_error": sanitization_result.sanitized_error,
                    "original_context": sanitization_result.sanitized_context,
                    "code_snippet": sanitization_result.sanitized_mre,
                    "model": model,
                    "provider": provider,
                    "language": language,
                    "framework": framework,
                    "submitted_at": datetime.utcnow().isoformat(),
                },
            )

            result_type = "child_issue"
            result_id = issue_id
            linked_to = parent_issue_id

        else:
            # Create master issue
            root_cause_category = _classify_root_cause(sanitized_root_cause)

            master_issue = await insert_record(
                table="master_issues",
                data={
                    "id": issue_id,
                    "canonical_error": sanitization_result.sanitized_error,
                    "sanitized_context": sanitization_result.sanitized_context,
                    "sanitized_mre": sanitization_result.sanitized_mre,
                    "root_cause": sanitized_root_cause,
                    "root_cause_category": root_cause_category,
                    "model_provider": provider,
                    "language": language,
                    "framework": framework,
                    "verification_count": 1,  # Initial verification
                    "created_at": datetime.utcnow().isoformat(),
                    "last_verified_at": datetime.utcnow().isoformat(),
                },
            )

            # Store vectors in Qdrant
            await upsert_issue_vectors(
                issue_id=issue_id,
                error_signature_vector=embeddings["error_signature"],
                root_cause_vector=embeddings["root_cause"],
                fix_summary_vector=embeddings["fix_summary"],
                payload={
                    "issue_id": issue_id,
                    "root_cause_category": root_cause_category,
                    "model_provider": provider,
                    "status": "active",
                },
            )

            result_type = "master_issue"
            result_id = issue_id
            linked_to = None

        # Create fix bundle
        fix_bundle_id = str(uuid.uuid4())
        await insert_record(
            table="fix_bundles",
            data={
                "id": fix_bundle_id,
                "master_issue_id": issue_id if not is_child_issue else parent_issue_id,
                "summary": sanitized_fix_summary,
                "fix_steps": sanitized_fix_steps,
                "code_changes": code_changes,
                "environment_actions": environment_actions,
                "verification_steps": verification_steps,
                "confidence_score": sanitization_result.confidence_score,
                "verification_count": 1,
                "created_at": datetime.utcnow().isoformat(),
                "last_confirmed_at": datetime.utcnow().isoformat(),
            },
        )

        # Log submission event
        await _log_submission_event(
            issue_id=result_id,
            is_child=is_child_issue,
            model=model,
            provider=provider,
        )

        return create_text_response({
            "success": True,
            "message": f"Issue submitted successfully as {result_type}",
            "issue_id": result_id,
            "fix_bundle_id": fix_bundle_id,
            "type": result_type,
            "linked_to": linked_to,
            "sanitization": {
                "confidence_score": sanitization_result.confidence_score,
                "llm_used": sanitization_result.llm_sanitization_used,
                "warnings": sanitization_result.warnings,
            },
        })

    except Exception as e:
        return create_error_response(f"Failed to submit issue: {str(e)}")


def _classify_root_cause(root_cause: str) -> str:
    """Classify root cause into a category.

    Args:
        root_cause: Root cause description.

    Returns:
        str: Root cause category.
    """
    root_cause_lower = root_cause.lower()

    # Simple keyword-based classification
    categories = {
        "api_breaking_change": ["breaking change", "deprecated", "removed", "no longer supported"],
        "version_incompatibility": ["version", "incompatible", "upgrade", "downgrade"],
        "missing_dependency": ["missing", "not found", "import error", "module not found"],
        "configuration_error": ["config", "configuration", "setting", "environment variable"],
        "type_error": ["type error", "type mismatch", "cannot be", "expected"],
        "null_reference": ["none", "null", "undefined", "nonetype"],
        "authentication_error": ["auth", "permission", "forbidden", "unauthorized"],
        "network_error": ["connection", "timeout", "network", "socket"],
        "syntax_error": ["syntax", "parse", "invalid"],
        "logic_error": ["logic", "incorrect", "wrong", "bug"],
    }

    for category, keywords in categories.items():
        if any(keyword in root_cause_lower for keyword in keywords):
            return category

    return "other"


async def _log_submission_event(
    issue_id: str,
    is_child: bool,
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> None:
    """Log an issue submission event.

    Args:
        issue_id: Issue ID.
        is_child: Whether this is a child issue.
        model: AI model used.
        provider: Model provider.
    """
    try:
        await insert_record(
            table="usage_events",
            data={
                "event_type": "issue_submitted",
                "issue_id": issue_id,
                "model": model,
                "provider": provider,
                "metadata": {
                    "is_child_issue": is_child,
                },
            },
        )
    except Exception:
        pass


# Export for server registration
submit_issue_tool.execute = execute
