"""Base tool utilities for GIM MCP tools."""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from mcp.types import Tool, TextContent


@dataclass
class ToolDefinition:
    """Definition of an MCP tool.

    Attributes:
        name: Tool name.
        description: Tool description.
        input_schema: JSON schema for input.
        annotations: Tool annotations (hints).
    """

    name: str
    description: str
    input_schema: Dict[str, Any]
    annotations: Dict[str, bool] = field(default_factory=dict)

    def get_tool_definition(self) -> Tool:
        """Convert to MCP Tool type.

        Returns:
            Tool: MCP Tool definition.
        """
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema,
        )


def create_text_response(content: Any) -> List[TextContent]:
    """Create a text response for MCP.

    Args:
        content: Content to return (will be JSON serialized if not string).

    Returns:
        List[TextContent]: MCP text content response.
    """
    if isinstance(content, str):
        text = content
    else:
        text = json.dumps(content, indent=2, default=str)

    return [TextContent(type="text", text=text)]


def create_error_response(error: str) -> List[TextContent]:
    """Create an error response for MCP.

    Args:
        error: Error message.

    Returns:
        List[TextContent]: MCP text content with error.
    """
    return [TextContent(type="text", text=json.dumps({"error": error}))]
