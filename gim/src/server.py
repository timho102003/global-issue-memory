"""GIM MCP Server - Global Issue Memory.

A privacy-preserving MCP server that transforms AI coding failures
into sanitized, searchable "master issues" with verified solutions.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from mcp.server import Server
from mcp.server.stdio import stdio_server

from src.config import get_settings
from src.db.qdrant_client import ensure_collection_exists
from src.tools.gim_search_issues import search_issues_tool
from src.tools.gim_get_fix_bundle import get_fix_bundle_tool
from src.tools.gim_submit_issue import submit_issue_tool
from src.tools.gim_confirm_fix import confirm_fix_tool
from src.tools.gim_report_usage import report_usage_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: Server) -> AsyncGenerator[dict, None]:
    """Lifespan context manager for server startup/shutdown.

    Args:
        server: The MCP server instance.

    Yields:
        dict: Context data (empty for now).
    """
    logger.info("GIM MCP Server starting up...")

    # Ensure Qdrant collection exists
    try:
        await ensure_collection_exists()
        logger.info("Qdrant collection verified")
    except Exception as e:
        logger.warning(f"Could not verify Qdrant collection: {e}")

    yield {}

    logger.info("GIM MCP Server shutting down...")


# Create MCP server
app = Server("gim-mcp")


# Register tools
@app.list_tools()
async def list_tools():
    """List all available GIM tools."""
    return [
        search_issues_tool.get_tool_definition(),
        get_fix_bundle_tool.get_tool_definition(),
        submit_issue_tool.get_tool_definition(),
        confirm_fix_tool.get_tool_definition(),
        report_usage_tool.get_tool_definition(),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        Tool result.
    """
    tools = {
        "gim_search_issues": search_issues_tool.execute,
        "gim_get_fix_bundle": get_fix_bundle_tool.execute,
        "gim_submit_issue": submit_issue_tool.execute,
        "gim_confirm_fix": confirm_fix_tool.execute,
        "gim_report_usage": report_usage_tool.execute,
    }

    if name not in tools:
        raise ValueError(f"Unknown tool: {name}")

    return await tools[name](arguments)


async def main():
    """Run the MCP server."""
    settings = get_settings()
    logger.info(f"Starting GIM MCP Server (log_level={settings.log_level})")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
