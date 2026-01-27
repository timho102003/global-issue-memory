"""GIM Search Issues Tool - Search for known issues matching an error."""

from typing import Any, Dict, List, Optional

from src.db.supabase_client import query_records, insert_record
from src.db.qdrant_client import search_similar_issues
from src.services.embedding_service import generate_embedding
from src.services.sanitization.pipeline import quick_sanitize
from src.tools.base import ToolDefinition, create_text_response, create_error_response


search_issues_tool = ToolDefinition(
    name="gim_search_issues",
    description="""Search GIM (Global Issue Memory) for known issues matching an error.

Use this tool when encountering an error to check if a solution already exists.
Returns ranked matching issues with fix bundles.

The query will be automatically sanitized to remove any sensitive information.""",
    input_schema={
        "type": "object",
        "properties": {
            "error_message": {
                "type": "string",
                "description": "The error message to search for",
            },
            "model": {
                "type": "string",
                "description": "AI model being used (e.g., 'claude-3-opus', 'gpt-4')",
            },
            "provider": {
                "type": "string",
                "description": "Model provider (e.g., 'anthropic', 'openai')",
            },
            "language": {
                "type": "string",
                "description": "Programming language context (e.g., 'python', 'javascript')",
            },
            "framework": {
                "type": "string",
                "description": "Framework being used (e.g., 'fastapi', 'react')",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5,
            },
        },
        "required": ["error_message"],
    },
    annotations={
        "readOnlyHint": True,
        "idempotentHint": True,
    },
)


async def execute(arguments: Dict[str, Any]) -> List:
    """Execute the search issues tool.

    Args:
        arguments: Tool arguments.

    Returns:
        List: MCP response content.
    """
    try:
        # Extract arguments
        error_message = arguments.get("error_message", "")
        model = arguments.get("model")
        provider = arguments.get("provider")
        language = arguments.get("language")
        framework = arguments.get("framework")
        limit = arguments.get("limit", 5)

        if not error_message:
            return create_error_response("error_message is required")

        # Sanitize the search query
        sanitized_query, warnings = quick_sanitize(error_message)

        # Generate embedding for search
        query_vector = await generate_embedding(sanitized_query)

        # Build filters
        filters: Optional[Dict[str, Any]] = None
        if provider:
            filters = filters or {}
            filters["model_provider"] = provider

        # Search Qdrant for similar issues
        vector_results = await search_similar_issues(
            query_vector=query_vector,
            vector_name="error_signature",
            limit=limit,
            score_threshold=0.5,
            filters=filters,
        )

        if not vector_results:
            # Log search event
            await _log_search_event(
                query=sanitized_query,
                results_count=0,
                model=model,
                provider=provider,
            )

            return create_text_response({
                "success": True,
                "message": "No matching issues found in GIM",
                "results": [],
                "sanitization_warnings": warnings,
            })

        # Fetch full issue details from Supabase
        issue_ids = [r["payload"].get("issue_id") for r in vector_results if r["payload"].get("issue_id")]

        issues = []
        for issue_id in issue_ids:
            issue = await query_records(
                table="master_issues",
                filters={"id": issue_id},
                limit=1,
            )
            if issue:
                # Also fetch fix bundle
                fix_bundles = await query_records(
                    table="fix_bundles",
                    filters={"issue_id": issue_id},
                    order_by="confidence_score",
                    ascending=False,
                    limit=1,
                )

                issue_data = issue[0]
                issue_data["fix_bundle"] = fix_bundles[0] if fix_bundles else None

                # Find similarity score
                for r in vector_results:
                    if r["payload"].get("issue_id") == issue_id:
                        issue_data["similarity_score"] = r["score"]
                        break

                issues.append(issue_data)

        # Sort by similarity score
        issues.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        # Log search event
        await _log_search_event(
            query=sanitized_query,
            results_count=len(issues),
            model=model,
            provider=provider,
        )

        return create_text_response({
            "success": True,
            "message": f"Found {len(issues)} matching issue(s)",
            "results": [
                {
                    "issue_id": i.get("id"),
                    "similarity_score": i.get("similarity_score"),
                    "canonical_error": i.get("canonical_error"),
                    "root_cause": i.get("root_cause"),
                    "root_cause_category": i.get("root_cause_category"),
                    "verification_count": i.get("verification_count", 0),
                    "has_fix_bundle": i.get("fix_bundle") is not None,
                    "fix_summary": i.get("fix_bundle", {}).get("summary") if i.get("fix_bundle") else None,
                }
                for i in issues
            ],
            "sanitization_warnings": warnings,
        })

    except Exception as e:
        return create_error_response(f"Search failed: {str(e)}")


async def _log_search_event(
    query: str,
    results_count: int,
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> None:
    """Log a search event for analytics.

    Args:
        query: Sanitized search query.
        results_count: Number of results returned.
        model: AI model used.
        provider: Model provider.
    """
    try:
        await insert_record(
            table="usage_events",
            data={
                "event_type": "search",
                "model": model,
                "provider": provider,
                "metadata": {
                    "query_length": len(query),
                    "results_count": results_count,
                },
            },
        )
    except Exception:
        # Don't fail the search if logging fails
        pass


# Export for server registration
search_issues_tool.execute = execute
