"""GIM Search Issues Tool - Search for known issues matching an error."""

from typing import Any, Dict, List, Optional

from src.db.supabase_client import query_records, insert_record
from src.db.qdrant_client import search_similar_issues
from src.exceptions import (
    GIMError,
    SupabaseError,
    QdrantError,
    EmbeddingError,
    ValidationError,
)
from src.logging_config import get_logger, set_request_context
from src.services.embedding_service import generate_search_embedding
from src.services.sanitization.pipeline import quick_sanitize
from src.tools.base import ToolDefinition, create_text_response, create_error_response


logger = get_logger("tools.search_issues")


search_issues_tool = ToolDefinition(
    name="gim_search_issues",
    description="""Search GIM (Global Issue Memory) for known issues matching an error.

┌─────────────────────────────────────────────────────────────────────┐
│  WHEN TO USE: Immediately when you encounter an error.             │
│  This should be your FIRST step before attempting to solve errors. │
└─────────────────────────────────────────────────────────────────────┘

GIM stores solutions from all AI coding assistants. Searching first can save
time by finding a verified fix instead of solving from scratch.

WORKFLOW:
  1. Call this tool with the error message
  2. Check results:
     ├─ If match found (similarity > 0.7):
     │    → Call `gim_get_fix_bundle` with the issue_id
     │    → Apply the fix
     │    → Call `gim_confirm_fix` to report outcome
     └─ If no match found:
          → Solve the error yourself
          → If the fix is globally useful (would a stranger hit this?),
            call `gim_submit_issue` to share your solution

WHAT YOU GET BACK:
  - issue_id: Use this with gim_get_fix_bundle to get the full fix
  - similarity_score: How closely the issue matches (0.0-1.0)
  - canonical_error: The standardized error description
  - root_cause: Why the error occurs
  - has_fix_bundle: Whether a verified fix exists
  - fix_summary: Brief description of the fix

PRIVACY: Your query is automatically sanitized to remove secrets, PII,
and domain-specific information before processing.""",
    input_schema={
        "type": "object",
        "properties": {
            "error_message": {
                "type": "string",
                "description": (
                    "The full error message or stack trace. Include as much context "
                    "as possible for better matching. Will be auto-sanitized."
                ),
            },
            "model": {
                "type": "string",
                "description": (
                    "Your AI model name (e.g., 'claude-3.5-sonnet', 'gpt-4-turbo'). "
                    "Helps track which models encounter which issues."
                ),
            },
            "provider": {
                "type": "string",
                "enum": ["anthropic", "openai", "google", "meta", "mistral", "other"],
                "description": "Your model provider for filtering and analytics.",
            },
            "language": {
                "type": "string",
                "description": (
                    "Programming language (e.g., 'python', 'javascript', 'typescript'). "
                    "Helps find language-specific solutions."
                ),
            },
            "framework": {
                "type": "string",
                "description": (
                    "Framework in use (e.g., 'fastapi', 'react', 'django'). "
                    "Helps find framework-specific solutions."
                ),
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (1-20). Default: 10.",
                "default": 10,
                "minimum": 1,
                "maximum": 20,
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
    # Set request context for tracing
    request_id = set_request_context()
    logger.info(f"Processing search request (request_id={request_id})")

    try:
        # Extract arguments
        error_message = arguments.get("error_message", "")
        model = arguments.get("model")
        provider = arguments.get("provider")
        language = arguments.get("language")
        framework = arguments.get("framework")
        limit = arguments.get("limit", 10)
        gim_id = arguments.get("gim_id")

        if not error_message:
            raise ValidationError("error_message is required", field="error_message")

        # Sanitize the search query
        sanitized_query, warnings = quick_sanitize(error_message)

        # Generate search embedding (structured to match stored combined vectors)
        logger.debug("Generating embedding for search query")
        try:
            query_vector = await generate_search_embedding(sanitized_query)
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise EmbeddingError(
                f"Failed to generate embedding: {str(e)}",
                original_error=e,
            )

        # Build filters
        filters: Optional[Dict[str, Any]] = None
        if provider:
            filters = filters or {}
            filters["model_provider"] = provider

        # Search Qdrant for similar issues
        vector_results = await search_similar_issues(
            query_vector=query_vector,
            limit=limit,
            score_threshold=0.2,
            filters=filters,
        )

        if not vector_results:
            # Log search event
            await _log_search_event(
                query=sanitized_query,
                results_count=0,
                model=model,
                provider=provider,
                gim_id=gim_id,
            )

            logger.info("No matching issues found")
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
                    filters={"master_issue_id": issue_id},
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
            gim_id=gim_id,
        )

        logger.info(f"Found {len(issues)} matching issues")
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

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        return create_error_response(f"Validation error: {e.message}")

    except EmbeddingError as e:
        logger.error(f"Embedding error: {e.message}")
        return create_error_response(f"Embedding error: {e.message}")

    except SupabaseError as e:
        logger.error(f"Database error: {e.message}")
        return create_error_response(f"Database error: {e.message}")

    except QdrantError as e:
        logger.error(f"Vector DB error: {e.message}")
        return create_error_response(f"Search error: {e.message}")

    except GIMError as e:
        logger.error(f"GIM error: {e.message}")
        return create_error_response(f"Error: {e.message}")

    except Exception as e:
        logger.exception("Unexpected error during search")
        return create_error_response("An unexpected error occurred during search. Please try again later.")


async def _log_search_event(
    query: str,
    results_count: int,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    gim_id: Optional[str] = None,
) -> None:
    """Log a search event for analytics.

    This is a non-critical operation that should not fail the main search.

    Args:
        query: Sanitized search query.
        results_count: Number of results returned.
        model: AI model used.
        provider: Model provider.
        gim_id: GIM user ID who triggered the search.
    """
    try:
        data = {
            "event_type": "search",
            "model": model,
            "provider": provider,
            "metadata": {
                "query_length": len(query),
                "results_count": results_count,
            },
        }
        if gim_id:
            data["gim_id"] = gim_id
        await insert_record(table="usage_events", data=data)
    except Exception as e:
        # Don't fail the search if logging fails
        logger.warning(f"Failed to log search event: {e}")


# Export for server registration
search_issues_tool.execute = execute
