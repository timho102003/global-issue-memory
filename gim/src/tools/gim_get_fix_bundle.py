"""GIM Get Fix Bundle Tool - Retrieve validated fix bundle for an issue."""

from typing import Any, Dict, List, Optional

from src.db.supabase_client import get_record, query_records, insert_record
from src.tools.base import ToolDefinition, create_text_response, create_error_response


get_fix_bundle_tool = ToolDefinition(
    name="gim_get_fix_bundle",
    description="""Retrieve the validated fix bundle for a GIM issue.

Use this after finding a matching issue via gim_search_issues.
Returns the complete fix including steps, code changes, environment actions,
and verification instructions.""",
    input_schema={
        "type": "object",
        "properties": {
            "issue_id": {
                "type": "string",
                "description": "The issue ID from gim_search_issues results",
            },
            "session_id": {
                "type": "string",
                "description": "Optional session ID for tracking",
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
    try:
        issue_id = arguments.get("issue_id")
        session_id = arguments.get("session_id")

        if not issue_id:
            return create_error_response("issue_id is required")

        # Fetch issue details
        issue = await get_record(table="master_issues", record_id=issue_id)
        if not issue:
            return create_error_response(f"Issue not found: {issue_id}")

        # Fetch fix bundle(s)
        fix_bundles = await query_records(
            table="fix_bundles",
            filters={"issue_id": issue_id},
            order_by="confidence_score",
            ascending=False,
        )

        if not fix_bundles:
            return create_text_response({
                "success": True,
                "issue_id": issue_id,
                "message": "No fix bundle available for this issue",
                "fix_bundle": None,
            })

        # Get the highest confidence fix bundle
        best_fix = fix_bundles[0]

        # Log retrieval event
        await _log_retrieval_event(
            issue_id=issue_id,
            fix_bundle_id=best_fix.get("id"),
            session_id=session_id,
        )

        return create_text_response({
            "success": True,
            "issue_id": issue_id,
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
            },
            "alternative_fixes_count": len(fix_bundles) - 1,
        })

    except Exception as e:
        return create_error_response(f"Failed to retrieve fix bundle: {str(e)}")


async def _log_retrieval_event(
    issue_id: str,
    fix_bundle_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Log a fix bundle retrieval event.

    Args:
        issue_id: Issue ID.
        fix_bundle_id: Fix bundle ID.
        session_id: Session ID.
    """
    try:
        await insert_record(
            table="usage_events",
            data={
                "event_type": "fix_retrieved",
                "issue_id": issue_id,
                "session_id": session_id,
                "metadata": {
                    "fix_bundle_id": fix_bundle_id,
                },
            },
        )
    except Exception:
        pass


# Export for server registration
get_fix_bundle_tool.execute = execute
