"""GIM Report Usage Tool - Report usage event for analytics."""

from typing import Any, Dict, List, Optional

from src.db.supabase_client import insert_record
from src.tools.base import ToolDefinition, create_text_response, create_error_response


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
                "enum": ["search", "fix_retrieved", "fix_applied", "error_encountered", "session_start", "session_end"],
                "description": "Type of usage event",
            },
            "issue_id": {
                "type": "string",
                "description": "Related issue ID (if applicable)",
            },
            "session_id": {
                "type": "string",
                "description": "Session ID for tracking user journey",
            },
            "model": {
                "type": "string",
                "description": "AI model being used",
            },
            "provider": {
                "type": "string",
                "description": "Model provider (e.g., 'anthropic', 'openai')",
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


async def execute(arguments: Dict[str, Any]) -> List:
    """Execute the report usage tool.

    Args:
        arguments: Tool arguments.

    Returns:
        List: MCP response content.
    """
    try:
        event_type = arguments.get("event_type")
        issue_id = arguments.get("issue_id")
        session_id = arguments.get("session_id")
        model = arguments.get("model")
        provider = arguments.get("provider")
        metadata = arguments.get("metadata", {})

        if not event_type:
            return create_error_response("event_type is required")

        valid_events = [
            "search",
            "fix_retrieved",
            "fix_applied",
            "error_encountered",
            "session_start",
            "session_end",
        ]
        if event_type not in valid_events:
            return create_error_response(f"Invalid event_type. Must be one of: {valid_events}")

        # Record the usage event
        await insert_record(
            table="usage_events",
            data={
                "event_type": event_type,
                "issue_id": issue_id,
                "session_id": session_id,
                "model": model,
                "provider": provider,
                "metadata": metadata,
            },
        )

        return create_text_response({
            "success": True,
            "message": "Usage event recorded",
            "event_type": event_type,
        })

    except Exception as e:
        return create_error_response(f"Failed to report usage: {str(e)}")


# Export for server registration
report_usage_tool.execute = execute
