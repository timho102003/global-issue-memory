"""GIM Submit Issue Tool - Submit a resolved issue to GIM."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.config import get_settings
from src.db.supabase_client import insert_record, query_records
from src.db.qdrant_client import upsert_issue_vectors, search_similar_issues
from src.exceptions import (
    GIMError,
    SupabaseError,
    QdrantError,
    EmbeddingError,
    SanitizationError,
    ValidationError,
)
from src.logging_config import get_logger, set_request_context
from src.services.embedding_service import generate_issue_embeddings
from src.services.sanitization.pipeline import run_sanitization_pipeline, quick_sanitize
from src.services.contribution_classifier import classify_contribution_type
from src.services.environment_extractor import extract_environment_info
from src.services.model_parser import parse_model_info
from src.tools.base import ToolDefinition, create_text_response, create_error_response


logger = get_logger("tools.submit_issue")


submit_issue_tool = ToolDefinition(
    name="gim_submit_issue",
    description="""Submit a RESOLVED issue to GIM to help other AI assistants.

┌─────────────────────────────────────────────────────────────────────┐
│  WHEN TO USE: After you have SUCCESSFULLY resolved an error AND    │
│  gim_search_issues found no existing solution.                     │
│  The fix MUST be verified working before submission.               │
└─────────────────────────────────────────────────────────────────────┘

DO NOT SUBMIT:
  ✗ Errors that are not yet resolved
  ✗ Issues that already exist in GIM (check with gim_search_issues first)
  ✗ Trivial typos or user-specific configuration issues
  ✗ Fixes that haven't been tested/verified

WORKFLOW:
  1. Encounter error → Call gim_search_issues
  2. No match found → Solve the error yourself
  3. Fix verified working → Call this tool to share the solution
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

  Highly Recommended:
    - code_changes: Specific file modifications
    - verification_steps: How to verify it works
    - language, framework: Context for matching

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
    # Set request context for tracing
    request_id = set_request_context()
    logger.info(f"Processing issue submission (request_id={request_id})")

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

        # New fields
        language_version = arguments.get("language_version")
        framework_version = arguments.get("framework_version")
        os_info = arguments.get("os")
        model_behavior_notes = arguments.get("model_behavior_notes", [])
        validation_success = arguments.get("validation_success")
        validation_notes = arguments.get("validation_notes")

        # Validate required fields
        if not error_message:
            raise ValidationError("error_message is required", field="error_message")
        if not root_cause:
            raise ValidationError("root_cause is required", field="root_cause")
        if not fix_summary:
            raise ValidationError("fix_summary is required", field="fix_summary")
        if not fix_steps:
            raise ValidationError("fix_steps is required", field="fix_steps")

        # Run sanitization pipeline
        logger.debug("Running sanitization pipeline")
        try:
            sanitization_result = await run_sanitization_pipeline(
                error_message=error_message,
                error_context=error_context,
                code_snippet=code_snippet,
                use_llm=True,
            )
        except Exception as e:
            logger.warning(f"Sanitization pipeline error: {e}")
            raise SanitizationError(
                f"Failed to sanitize content: {str(e)}",
                stage="pipeline",
                original_error=e,
            )

        # Also sanitize root cause and fix summary
        sanitized_root_cause, _ = quick_sanitize(root_cause)
        sanitized_fix_summary, _ = quick_sanitize(fix_summary)
        sanitized_fix_steps = [quick_sanitize(step)[0] for step in fix_steps]

        # Generate embeddings for similarity search
        logger.debug("Generating embeddings")
        try:
            embeddings = await generate_issue_embeddings(
                error_message=sanitization_result.sanitized_error,
                root_cause=sanitized_root_cause,
                fix_summary=sanitized_fix_summary,
            )
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise EmbeddingError(
                f"Failed to generate embeddings: {str(e)}",
                original_error=e,
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
            # Classify contribution type
            contribution_type = classify_contribution_type(
                error_message=sanitization_result.sanitized_error,
                root_cause=sanitized_root_cause,
                fix_steps=sanitized_fix_steps,
                environment_actions=environment_actions,
                model_behavior_notes=model_behavior_notes,
                validation_success=validation_success,
            )

            # Extract environment info
            environment_info = extract_environment_info(
                language=language,
                framework=framework,
                error_context=error_context,
                language_version=language_version,
                framework_version=framework_version,
                os=os_info,
            )

            # Parse model info
            model_provider, model_name, model_version = parse_model_info(
                model=model,
                provider=provider,
            )

            # Create child issue with full metadata
            logger.info(f"Creating child issue linked to {parent_issue_id}")
            await insert_record(
                table="child_issues",
                data={
                    "id": issue_id,
                    "master_issue_id": parent_issue_id,
                    "original_error": sanitization_result.sanitized_error,
                    "original_context": sanitization_result.sanitized_context,
                    "code_snippet": sanitization_result.sanitized_mre,
                    "model": model,
                    "provider": model_provider,
                    "language": language,
                    "framework": framework,
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    # Rich metadata fields
                    "metadata": {
                        "contribution_type": contribution_type.value,
                        "environment": environment_info,
                        "model_name": model_name,
                        "model_version": model_version,
                        "model_behavior_notes": model_behavior_notes,
                        "validation_success": validation_success,
                        "validation_notes": validation_notes,
                    },
                },
            )

            result_type = "child_issue"
            result_id = issue_id
            linked_to = parent_issue_id

        else:
            # Create master issue
            root_cause_category = _classify_root_cause(sanitized_root_cause)

            logger.info(f"Creating master issue with category {root_cause_category}")
            await insert_record(
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
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_verified_at": datetime.now(timezone.utc).isoformat(),
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
        logger.debug(f"Creating fix bundle {fix_bundle_id}")
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
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_confirmed_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Log submission event (non-critical, don't fail on error)
        await _log_submission_event(
            issue_id=result_id,
            is_child=is_child_issue,
            model=model,
            provider=provider,
        )

        logger.info(f"Successfully submitted {result_type} {result_id}")
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

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        return create_error_response(f"Validation error: {e.message}")

    except SanitizationError as e:
        logger.warning(f"Sanitization error: {e.message}")
        return create_error_response(f"Sanitization error: {e.message}")

    except EmbeddingError as e:
        logger.error(f"Embedding error: {e.message}")
        return create_error_response(f"Embedding error: {e.message}")

    except SupabaseError as e:
        logger.error(f"Database error: {e.message}")
        return create_error_response(f"Database error: {e.message}")

    except QdrantError as e:
        logger.error(f"Vector DB error: {e.message}")
        return create_error_response(f"Vector storage error: {e.message}")

    except GIMError as e:
        logger.error(f"GIM error: {e.message}")
        return create_error_response(f"Error: {e.message}")

    except Exception as e:
        logger.exception("Unexpected error during submission")
        return create_error_response("An unexpected error occurred. Please try again later.")


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

    This is a non-critical operation that should not fail the main submission.

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
    except Exception as e:
        # Log but don't fail the main operation
        logger.warning(f"Failed to log submission event: {e}")


# Export for server registration
submit_issue_tool.execute = execute
