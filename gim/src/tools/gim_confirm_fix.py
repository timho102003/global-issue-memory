"""GIM Confirm Fix Tool - Report whether a fix bundle worked."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.supabase_client import get_record, update_record, insert_record
from src.tools.base import ToolDefinition, create_text_response, create_error_response


confirm_fix_tool = ToolDefinition(
    name="gim_confirm_fix",
    description="""Report whether a fix bundle from GIM worked.

Use this after attempting to apply a fix from gim_get_fix_bundle.
This helps improve fix reliability scores and benefits future users.""",
    input_schema={
        "type": "object",
        "properties": {
            "issue_id": {
                "type": "string",
                "description": "The issue ID the fix was for",
            },
            "fix_bundle_id": {
                "type": "string",
                "description": "The fix bundle ID that was attempted",
            },
            "success": {
                "type": "boolean",
                "description": "Whether the fix worked (true) or failed (false)",
            },
            "notes": {
                "type": "string",
                "description": "Optional notes about the fix attempt",
            },
            "session_id": {
                "type": "string",
                "description": "Optional session ID for tracking",
            },
            "model": {
                "type": "string",
                "description": "AI model that applied the fix",
            },
            "provider": {
                "type": "string",
                "description": "Model provider",
            },
        },
        "required": ["issue_id", "success"],
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
    try:
        issue_id = arguments.get("issue_id")
        fix_bundle_id = arguments.get("fix_bundle_id")
        success = arguments.get("success")
        notes = arguments.get("notes", "")
        session_id = arguments.get("session_id")
        model = arguments.get("model")
        provider = arguments.get("provider")

        if not issue_id:
            return create_error_response("issue_id is required")
        if success is None:
            return create_error_response("success is required")

        # Verify issue exists
        issue = await get_record(table="master_issues", record_id=issue_id)
        if not issue:
            return create_error_response(f"Issue not found: {issue_id}")

        # Update fix bundle if specified
        if fix_bundle_id:
            fix_bundle = await get_record(table="fix_bundles", record_id=fix_bundle_id)
            if fix_bundle:
                current_count = fix_bundle.get("verification_count", 0)
                current_score = fix_bundle.get("confidence_score", 0.5)

                if success:
                    # Increase confidence score and verification count
                    new_count = current_count + 1
                    # Bayesian update for confidence score
                    new_score = min((current_score * current_count + 1.0) / new_count, 1.0)

                    await update_record(
                        table="fix_bundles",
                        record_id=fix_bundle_id,
                        data={
                            "verification_count": new_count,
                            "confidence_score": new_score,
                            "last_confirmed_at": datetime.utcnow().isoformat(),
                        },
                    )
                else:
                    # Decrease confidence score
                    new_count = current_count + 1
                    new_score = max((current_score * current_count + 0.0) / new_count, 0.0)

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
        if success:
            await update_record(
                table="master_issues",
                record_id=issue_id,
                data={
                    "verification_count": current_issue_count + 1,
                    "last_verified_at": datetime.utcnow().isoformat(),
                },
            )

        # Log confirmation event
        await _log_confirmation_event(
            issue_id=issue_id,
            fix_bundle_id=fix_bundle_id,
            success=success,
            notes=notes,
            session_id=session_id,
            model=model,
            provider=provider,
        )

        return create_text_response({
            "success": True,
            "message": "Fix confirmation recorded",
            "issue_id": issue_id,
            "fix_bundle_id": fix_bundle_id,
            "fix_succeeded": success,
        })

    except Exception as e:
        return create_error_response(f"Failed to confirm fix: {str(e)}")


async def _log_confirmation_event(
    issue_id: str,
    fix_bundle_id: Optional[str],
    success: bool,
    notes: str,
    session_id: Optional[str],
    model: Optional[str],
    provider: Optional[str],
) -> None:
    """Log a fix confirmation event.

    Args:
        issue_id: Issue ID.
        fix_bundle_id: Fix bundle ID.
        success: Whether fix succeeded.
        notes: Optional notes.
        session_id: Session ID.
        model: AI model.
        provider: Model provider.
    """
    try:
        await insert_record(
            table="usage_events",
            data={
                "event_type": "fix_confirmed",
                "issue_id": issue_id,
                "session_id": session_id,
                "model": model,
                "provider": provider,
                "metadata": {
                    "fix_bundle_id": fix_bundle_id,
                    "success": success,
                    "notes": notes[:500] if notes else None,
                },
            },
        )
    except Exception:
        pass


# Export for server registration
confirm_fix_tool.execute = execute
