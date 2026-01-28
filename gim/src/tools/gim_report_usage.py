"""GIM Report Usage Tool - Report usage event for analytics."""

from typing import Any, Dict, List

from src.db.supabase_client import insert_record
from src.exceptions import GIMError, SupabaseError, ValidationError
from src.logging_config import get_logger, set_request_context
from src.tools.base import ToolDefinition, create_text_response, create_error_response


logger = get_logger("tools.report_usage")


report_usage_tool = ToolDefinition(
    name="gim_report_usage",
    description="""Report a usage event to GIM for analytics.

Use this to track how GIM is being used, which helps improve the service.
Event types include: search, fix_retrieved, fix_applied, error_encountered.""",
    input_schema={
        "type": "object",
        "properties": {
            "event_type": {
                "type": "string",
                "description": "Type of usage event",
            },
            "metadata": {
                "type": "object",
                "description": "Additional event metadata",
            },
        },
        "required": ["event_type"],
    },
    annotations={
        "readOnlyHint": False,
    },
)


VALID_EVENT_TYPES = [
    "search",
    "fix_retrieved",
    "fix_applied",
    "error_encountered",
    "session_start",
    "session_end",
]


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
        await insert_record(
            table="usage_events",
            data={
                "event_type": event_type,
                "metadata": metadata,
            },
        )

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
