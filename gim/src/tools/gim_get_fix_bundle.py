"""GIM Get Fix Bundle Tool - Retrieve validated fix bundle for an issue."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from src.db.issue_resolver import resolve_issue_id
from src.db.supabase_client import get_record, query_records, insert_record
from src.exceptions import GIMError, SupabaseError, ValidationError
from src.logging_config import get_logger, set_request_context
from src.tools.base import ToolDefinition, create_text_response, create_error_response


def validate_uuid(value: str, field_name: str) -> str:
    """Validate that a string is a valid UUID.

    Args:
        value: The string to validate.
        field_name: Name of the field for error messages.

    Returns:
        str: The validated UUID string.

    Raises:
        ValidationError: If the value is not a valid UUID.
    """
    try:
        UUID(value)
        return value
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid UUID format for {field_name}", field=field_name)


logger = get_logger("tools.get_fix_bundle")


get_fix_bundle_tool = ToolDefinition(
    name="gim_get_fix_bundle",
    description="""Retrieve the complete fix bundle for a GIM issue.

┌─────────────────────────────────────────────────────────────────────┐
│  WHEN TO USE: After gim_search_issues returns a matching issue.    │
│  Use the issue_id from the search results.                         │
└─────────────────────────────────────────────────────────────────────┘

WORKFLOW:
  1. Get issue_id from gim_search_issues results
  2. Call this tool with that issue_id
  3. Apply the fix:
     ├─ Follow fix_steps in order
     ├─ Apply code_changes to the user's files
     └─ Run any environment_actions (installs, configs)
  4. Verify using verification_steps
  5. ⚠️  CRITICAL: Call `gim_confirm_fix` to report the outcome
     └─ This improves fix quality for everyone!

WHAT YOU GET BACK:
  - fix_steps: Ordered list of human-readable instructions
  - code_changes: Specific file modifications with before/after
  - environment_actions: Package installs, config changes, etc.
  - verification_steps: How to confirm the fix works
  - confidence_score: How reliable this fix is (0.0-1.0)
  - verification_count: How many times this fix has been verified

CONFIDENCE SCORES:
  - 0.9+  : Highly reliable, verified by multiple users
  - 0.7-0.9: Good reliability, likely to work
  - 0.5-0.7: Moderate reliability, may need adaptation
  - <0.5  : Low reliability, use with caution""",
    input_schema={
        "type": "object",
        "properties": {
            "issue_id": {
                "type": "string",
                "format": "uuid",
                "description": (
                    "The issue ID from gim_search_issues results. "
                    "This is a UUID that uniquely identifies the issue."
                ),
            },
            "include_related": {
                "type": "boolean",
                "description": (
                    "Include related child issues that may have additional "
                    "context or alternative fixes. Default: true."
                ),
                "default": True,
            },
        },
        "required": ["issue_id"],
    },
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)


async def execute(arguments: Dict[str, Any]) -> List:
    """Execute the get fix bundle tool.

    Args:
        arguments: Tool arguments.

    Returns:
        List: MCP response content.
    """
    # Set request context for tracing
    request_id = set_request_context()
    logger.info(f"Processing fix bundle request (request_id={request_id})")

    try:
        issue_id = arguments.get("issue_id")
        include_related = arguments.get("include_related", True)
        gim_id = arguments.get("gim_id")

        if not issue_id:
            raise ValidationError("issue_id is required", field="issue_id")
        issue_id = validate_uuid(issue_id, "issue_id")

        # Resolve issue ID (handles both master and child IDs)
        logger.debug(f"Resolving issue {issue_id}")
        master_issue, child_issue, is_child = await resolve_issue_id(issue_id)
        if not master_issue:
            logger.warning(f"Issue not found: {issue_id}")
            return create_error_response(f"Issue not found: {issue_id}")

        master_issue_id = master_issue.get("id")
        issue = master_issue

        # Fetch fix bundle(s) using the master issue ID
        fix_bundles = await query_records(
            table="fix_bundles",
            filters={"master_issue_id": master_issue_id},
            order_by="confidence_score",
            ascending=False,
        )

        if not fix_bundles:
            logger.info(f"No fix bundle available for issue {issue_id}")
            return create_text_response({
                "success": True,
                "issue_id": issue_id,
                "master_issue_id": master_issue_id,
                "is_child_issue": is_child,
                "message": "No fix bundle available for this issue",
                "fix_bundle": None,
            })

        # Get the highest confidence fix bundle
        best_fix = fix_bundles[0]

        # Log retrieval event
        await _log_retrieval_event(
            issue_id=master_issue_id,
            fix_bundle_id=best_fix.get("id"),
            gim_id=gim_id,
        )

        logger.info(f"Retrieved fix bundle {best_fix.get('id')} for issue {issue_id}")
        return create_text_response({
            "success": True,
            "issue_id": issue_id,
            "master_issue_id": master_issue_id,
            "is_child_issue": is_child,
            "canonical_error": issue.get("canonical_error"),
            "root_cause": issue.get("root_cause"),
            "fix_bundle": {
                "id": best_fix.get("id"),
                "summary": best_fix.get("summary"),
                "fix_steps": best_fix.get("fix_steps", []),
                "code_changes": best_fix.get("code_changes", []),
                "environment_actions": best_fix.get("environment_actions", []),
                "constraints": best_fix.get("constraints", {}),
                "verification_steps": best_fix.get("verification_steps", []),
                "confidence_score": best_fix.get("confidence_score", 0),
                "verification_count": best_fix.get("verification_count", 0),
                "last_confirmed_at": best_fix.get("last_confirmed_at"),
                "version": best_fix.get("version", 1),
                "is_current": best_fix.get("is_current", True),
                "code_fix": best_fix.get("code_fix"),
                "patch_diff": best_fix.get("patch_diff"),
                "created_at": best_fix.get("created_at", ""),
                "updated_at": best_fix.get("updated_at", ""),
            },
            "alternative_fixes_count": len(fix_bundles) - 1,
        })

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        return create_error_response(f"Validation error: {e.message}")

    except SupabaseError as e:
        logger.error(f"Database error: {e.message}")
        return create_error_response(f"Database error: {e.message}")

    except GIMError as e:
        logger.error(f"GIM error: {e.message}")
        return create_error_response(f"Error: {e.message}")

    except Exception as e:
        logger.exception("Unexpected error during fix bundle retrieval")
        return create_error_response("An unexpected error occurred. Please try again later.")


async def _log_retrieval_event(
    issue_id: str,
    fix_bundle_id: Optional[str] = None,
    gim_id: Optional[str] = None,
) -> None:
    """Log a fix bundle retrieval event.

    This is a non-critical operation that should not fail the main retrieval.

    Args:
        issue_id: Issue ID.
        fix_bundle_id: Fix bundle ID.
        gim_id: GIM user ID who retrieved the fix bundle.
    """
    try:
        data = {
            "event_type": "fix_retrieved",
            "issue_id": issue_id,
            "metadata": {
                "fix_bundle_id": fix_bundle_id,
            },
        }
        if gim_id:
            data["gim_id"] = gim_id
        await insert_record(table="usage_events", data=data)
    except Exception as e:
        logger.error(f"Failed to log retrieval event: {e}", exc_info=True)


# Export for server registration
get_fix_bundle_tool.execute = execute
