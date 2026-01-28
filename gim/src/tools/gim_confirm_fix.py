"""GIM Confirm Fix Tool - Report whether a fix bundle worked."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.db.supabase_client import get_record, update_record, insert_record, query_records
from src.exceptions import GIMError, SupabaseError, ValidationError
from src.logging_config import get_logger, set_request_context
from src.tools.base import ToolDefinition, create_text_response, create_error_response


logger = get_logger("tools.confirm_fix")


confirm_fix_tool = ToolDefinition(
    name="gim_confirm_fix",
    description="""Report whether a fix from GIM worked or failed.

┌─────────────────────────────────────────────────────────────────────┐
│  ⚠️  CRITICAL: ALWAYS call this after applying a fix from GIM!     │
│  This feedback loop is essential for improving fix quality.        │
└─────────────────────────────────────────────────────────────────────┘

WHEN TO USE:
  - ALWAYS after applying a fix from gim_get_fix_bundle
  - Even if the fix only partially worked
  - Even if you had to modify the fix slightly

WHY THIS MATTERS:
  ├─ fix_worked=true  → Increases confidence score, helps future users
  ├─ fix_worked=false → Decreases confidence score, prevents bad advice
  └─ Your feedback improves GIM for ALL AI coding assistants

WORKFLOW:
  1. Apply fix from gim_get_fix_bundle
  2. Test if the error is resolved
  3. Call this tool:
     ├─ fix_worked=true  if the error is fully resolved
     ├─ fix_worked=false if the error persists or new errors appear
     └─ Include feedback with details about what happened

FEEDBACK EXAMPLES:
  ✓ "Fix worked perfectly, error resolved"
  ✓ "Fix worked after changing import path"
  ✗ "Fix caused new TypeError on line 45"
  ✗ "Fix didn't apply - file structure different"
  ? "Partially worked - main error fixed but side effect remains"

WHAT HAPPENS:
  - Successful fixes: confidence_score increases, verification_count += 1
  - Failed fixes: confidence_score decreases (Bayesian update)
  - All feedback is stored to improve future fix recommendations""",
    input_schema={
        "type": "object",
        "properties": {
            "issue_id": {
                "type": "string",
                "format": "uuid",
                "description": (
                    "The issue ID the fix was for. Get this from "
                    "gim_search_issues or gim_get_fix_bundle response."
                ),
            },
            "fix_worked": {
                "type": "boolean",
                "description": (
                    "Did the fix resolve the error? "
                    "true = error resolved, false = error persists or new errors."
                ),
            },
            "feedback": {
                "type": "string",
                "maxLength": 500,
                "description": (
                    "Details about the fix attempt. Include: what worked, "
                    "what didn't, any modifications needed, or new errors encountered. "
                    "This feedback helps improve fixes for everyone."
                ),
            },
        },
        "required": ["issue_id", "fix_worked"],
    },
    annotations={
        "readOnlyHint": False,
    },
)


async def execute(arguments: Dict[str, Any]) -> List:
    """Execute the confirm fix tool.

    Args:
        arguments: Tool arguments.

    Returns:
        List: MCP response content.
    """
    # Set request context for tracing
    request_id = set_request_context()
    logger.info(f"Processing fix confirmation (request_id={request_id})")

    try:
        issue_id = arguments.get("issue_id")
        fix_worked = arguments.get("fix_worked")
        feedback = arguments.get("feedback", "")

        if not issue_id:
            raise ValidationError("issue_id is required", field="issue_id")
        if fix_worked is None:
            raise ValidationError("fix_worked is required", field="fix_worked")

        # Verify issue exists
        logger.debug(f"Verifying issue {issue_id} exists")
        issue = await get_record(table="master_issues", record_id=issue_id)
        if not issue:
            logger.warning(f"Issue not found: {issue_id}")
            return create_error_response(f"Issue not found: {issue_id}")

        # Get the best fix bundle for this issue
        fix_bundles = await query_records(
            table="fix_bundles",
            filters={"master_issue_id": issue_id},
            order_by="confidence_score",
            ascending=False,
            limit=1,
        )

        fix_bundle_id = None
        if fix_bundles:
            fix_bundle = fix_bundles[0]
            fix_bundle_id = fix_bundle.get("id")
            current_count = fix_bundle.get("verification_count", 0)
            current_score = fix_bundle.get("confidence_score", 0.5)

            if fix_worked:
                # Increase confidence score and verification count
                new_count = current_count + 1
                # Bayesian update for confidence score
                new_score = min((current_score * current_count + 1.0) / new_count, 1.0)

                logger.debug(f"Updating fix bundle {fix_bundle_id} with positive confirmation")
                await update_record(
                    table="fix_bundles",
                    record_id=fix_bundle_id,
                    data={
                        "verification_count": new_count,
                        "confidence_score": new_score,
                        "last_confirmed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            else:
                # Decrease confidence score
                new_count = current_count + 1
                new_score = max((current_score * current_count + 0.0) / new_count, 0.0)

                logger.debug(f"Updating fix bundle {fix_bundle_id} with negative confirmation")
                await update_record(
                    table="fix_bundles",
                    record_id=fix_bundle_id,
                    data={
                        "verification_count": new_count,
                        "confidence_score": new_score,
                    },
                )

        # Update issue verification count
        current_issue_count = issue.get("verification_count", 0)
        if fix_worked:
            logger.debug(f"Updating issue {issue_id} verification count")
            await update_record(
                table="master_issues",
                record_id=issue_id,
                data={
                    "verification_count": current_issue_count + 1,
                    "last_verified_at": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Log confirmation event
        await _log_confirmation_event(
            issue_id=issue_id,
            fix_bundle_id=fix_bundle_id,
            fix_worked=fix_worked,
            feedback=feedback,
        )

        logger.info(f"Fix confirmation recorded for issue {issue_id}: worked={fix_worked}")
        return create_text_response({
            "success": True,
            "message": "Fix confirmation recorded",
            "issue_id": issue_id,
            "fix_bundle_id": fix_bundle_id,
            "fix_worked": fix_worked,
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
        logger.exception("Unexpected error during fix confirmation")
        return create_error_response("An unexpected error occurred. Please try again later.")


async def _log_confirmation_event(
    issue_id: str,
    fix_bundle_id: Optional[str],
    fix_worked: bool,
    feedback: str,
) -> None:
    """Log a fix confirmation event.

    This is a non-critical operation that should not fail the main confirmation.

    Args:
        issue_id: Issue ID.
        fix_bundle_id: Fix bundle ID.
        fix_worked: Whether fix succeeded.
        feedback: Optional feedback.
    """
    try:
        await insert_record(
            table="usage_events",
            data={
                "event_type": "fix_confirmed",
                "issue_id": issue_id,
                "metadata": {
                    "fix_bundle_id": fix_bundle_id,
                    "fix_worked": fix_worked,
                    "feedback": feedback[:500] if feedback else None,
                },
            },
        )
    except Exception as e:
        logger.warning(f"Failed to log confirmation event: {e}")


# Export for server registration
confirm_fix_tool.execute = execute
