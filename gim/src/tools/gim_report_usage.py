"""GIM Report Usage Tool - Report usage event for analytics."""

from typing import Any, Dict, List

from src.db.supabase_client import insert_record
from src.exceptions import GIMError, SupabaseError, ValidationError
from src.logging_config import get_logger, set_request_context
from src.tools.base import ToolDefinition, create_text_response, create_error_response


logger = get_logger("tools.report_usage")


# Valid event types for usage tracking
# Note: Most events are logged automatically by their respective tools.
# This tool is for manual reporting of events not covered elsewhere.
VALID_EVENT_TYPES = [
    # Auto-logged by gim_search_issues - DO NOT use manually
    "search",
    # Auto-logged by gim_get_fix_bundle - DO NOT use manually
    "fix_retrieved",
    # Auto-logged by gim_confirm_fix - DO NOT use manually
    "fix_confirmed",
    # Auto-logged by gim_submit_issue - DO NOT use manually
    "issue_submitted",
    # Manual events - USE these with this tool
    "fix_applied",
    "error_encountered",
    "session_start",
    "session_end",
]


report_usage_tool = ToolDefinition(
    name="gim_report_usage",
    description="""Report a usage event to GIM for analytics.

⚠️  IMPORTANT: Most events are logged AUTOMATICALLY by other GIM tools.
    Only use this tool for manual event reporting.

AUTOMATIC EVENTS (DO NOT report manually - already tracked):
├─ 'search'          → Auto-logged by gim_search_issues
├─ 'fix_retrieved'   → Auto-logged by gim_get_fix_bundle
├─ 'fix_confirmed'   → Auto-logged by gim_confirm_fix
└─ 'issue_submitted' → Auto-logged by gim_submit_issue

MANUAL EVENTS (use this tool for these):
├─ 'fix_applied'        → After applying a fix WITHOUT using gim_get_fix_bundle
├─ 'error_encountered'  → To report errors that couldn't be processed
├─ 'session_start'      → At the beginning of a coding session (optional)
└─ 'session_end'        → At the end of a coding session (optional)

EXAMPLE USAGE:
  When to use 'fix_applied':
    - You found a fix through other means (not GIM) and applied it
    - You want to track that a manual fix was attempted

  When to use 'error_encountered':
    - An error occurred that prevented normal GIM workflow
    - Useful for debugging and improving GIM reliability""",
    input_schema={
        "type": "object",
        "properties": {
            "event_type": {
                "type": "string",
                "enum": VALID_EVENT_TYPES,
                "description": (
                    "Type of usage event. Most events are auto-logged by other tools. "
                    "Use 'fix_applied' when applying a fix not from GIM, "
                    "'error_encountered' for processing errors, "
                    "'session_start'/'session_end' for session tracking."
                ),
            },
            "metadata": {
                "type": "object",
                "description": (
                    "Additional event context. Include relevant details like "
                    "error_message, issue_id, fix_source, or any debugging info."
                ),
            },
        },
        "required": ["event_type"],
    },
    annotations={
        "readOnlyHint": False,
    },
)


async def execute(arguments: Dict[str, Any]) -> List:
    """Execute the report usage tool.

    Args:
        arguments: Tool arguments.

    Returns:
        List: MCP response content.
    """
    # Set request context for tracing
    request_id = set_request_context()
    logger.debug(f"Processing usage report (request_id={request_id})")

    try:
        event_type = arguments.get("event_type")
        metadata = arguments.get("metadata", {})
        gim_id = arguments.get("gim_id")

        if not event_type:
            raise ValidationError("event_type is required", field="event_type")

        if event_type not in VALID_EVENT_TYPES:
            raise ValidationError(
                f"Invalid event_type. Must be one of: {VALID_EVENT_TYPES}",
                field="event_type",
                constraint=f"one_of:{','.join(VALID_EVENT_TYPES)}",
            )

        # Record the usage event
        logger.debug(f"Recording usage event: {event_type}")
        data = {
            "event_type": event_type,
            "metadata": metadata,
        }
        if gim_id:
            data["gim_id"] = gim_id
        await insert_record(table="usage_events", data=data)

        logger.info(f"Usage event recorded: {event_type}")
        return create_text_response({
            "success": True,
            "message": "Usage event recorded",
            "event_type": event_type,
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
        logger.exception("Unexpected error during usage reporting")
        return create_error_response("An unexpected error occurred. Please try again later.")


# Export for server registration
report_usage_tool.execute = execute
