"""Qdrant vector database client wrapper with error handling and logging."""

import threading
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
    ScalarQuantization,
    ScalarQuantizationConfig,
    ScalarType,
    SearchParams,
    QuantizationSearchParams,
)
from qdrant_client.http.exceptions import UnexpectedResponse

from src.config import get_settings
from src.exceptions import QdrantError
from src.logging_config import get_logger, log_operation


_client: Optional[QdrantClient] = None
_client_lock = threading.Lock()
logger = get_logger("db.qdrant")

# Collection name for GIM issues
COLLECTION_NAME = "gim_issues"


def _get_vector_dim() -> int:
    """Get vector dimensions from settings.

    Returns:
        int: Vector dimensions for embedding model.
    """
    return get_settings().embedding_dimensions


def get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client singleton.

    Thread-safe singleton pattern using double-checked locking.

    Returns:
        QdrantClient: Qdrant client instance.

    Raises:
        QdrantError: If client creation fails.
    """
    global _client
    if _client is None:
        with _client_lock:
            # Double-check after acquiring lock
            if _client is None:
                try:
                    settings = get_settings()
                    _client = QdrantClient(
                        url=settings.qdrant_url,
                        api_key=settings.qdrant_api_key,
                    )
                    logger.info("Qdrant client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Qdrant client: {e}")
                    raise QdrantError(
                        "Failed to initialize Qdrant client",
                        operation="connect",
                        original_error=e,
                    )
    return _client


@log_operation("qdrant.ensure_collection")
async def ensure_collection_exists() -> None:
    """Ensure the GIM issues collection exists with proper configuration.

    Raises:
        QdrantError: If collection creation fails.
    """
    try:
        client = get_qdrant_client()
        vector_dim = _get_vector_dim()

        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if COLLECTION_NAME not in collection_names:
            logger.info(f"Creating collection {COLLECTION_NAME}")
            # Create collection with single combined vector + scalar quantization
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=vector_dim,
                    distance=Distance.COSINE,
                ),
                quantization_config=ScalarQuantization(
                    scalar=ScalarQuantizationConfig(
                        type=ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True,
                    ),
                ),
            )

            # Create payload indexes for filtering
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="root_cause_category",
                field_schema="keyword",
            )
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="model_provider",
                field_schema="keyword",
            )
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="status",
                field_schema="keyword",
            )
            logger.info(f"Collection {COLLECTION_NAME} created successfully")
        else:
            logger.debug(f"Collection {COLLECTION_NAME} already exists")
    except UnexpectedResponse as e:
        logger.error(f"Qdrant API error during collection check/creation: {e}")
        raise QdrantError(
            f"Failed to ensure collection exists: {e}",
            collection=COLLECTION_NAME,
            operation="ensure_collection",
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during collection check/creation: {e}")
        raise QdrantError(
            f"Failed to ensure collection exists: {str(e)}",
            collection=COLLECTION_NAME,
            operation="ensure_collection",
            original_error=e,
        )


@log_operation("qdrant.upsert")
async def upsert_issue_vectors(
    issue_id: str,
    vector: List[float],
    payload: Dict[str, Any],
) -> None:
    """Upsert issue vector into Qdrant.

    Args:
        issue_id: Unique issue ID.
        vector: Combined embedding vector for the issue.
        payload: Additional metadata payload.

    Raises:
        QdrantError: If upsert fails.
    """
    try:
        client = get_qdrant_client()
        await ensure_collection_exists()

        point = PointStruct(
            id=issue_id,
            vector=vector,
            payload=payload,
        )

        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point],
        )
        logger.debug(f"Upserted vectors for issue {issue_id}")
    except UnexpectedResponse as e:
        logger.error(f"Qdrant API error during upsert for issue {issue_id}: {e}")
        raise QdrantError(
            f"Failed to upsert issue vectors: {e}",
            collection=COLLECTION_NAME,
            operation="upsert",
            details={"issue_id": issue_id},
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during upsert for issue {issue_id}: {e}")
        raise QdrantError(
            f"Failed to upsert issue vectors: {str(e)}",
            collection=COLLECTION_NAME,
            operation="upsert",
            details={"issue_id": issue_id},
            original_error=e,
        )


@log_operation("qdrant.search")
async def search_similar_issues(
    query_vector: List[float],
    limit: int = 10,
    score_threshold: float = 0.2,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Search for similar issues using vector similarity.

    Uses scalar quantization re-scoring for high precision and speed.

    Args:
        query_vector: Query embedding vector.
        limit: Maximum results to return.
        score_threshold: Minimum similarity score.
        filters: Optional filters (e.g., root_cause_category, model_provider).

    Returns:
        List[Dict[str, Any]]: List of matching issues with scores.

    Raises:
        QdrantError: If search fails.
    """
    try:
        client = get_qdrant_client()
        await ensure_collection_exists()

        # Build filter if provided
        query_filter = None
        if filters:
            conditions = []
            for field, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=value),
                    )
                )
            query_filter = Filter(must=conditions)

        # Query with quantization re-scoring for precision
        response = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
            search_params=SearchParams(
                quantization=QuantizationSearchParams(
                    ignore=False,
                    rescore=True,
                    oversampling=2.0,
                ),
            ),
        )

        results = [
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload,
            }
            for point in response.points
        ]
        logger.debug(f"Found {len(results)} similar issues")
        return results
    except UnexpectedResponse as e:
        logger.error(f"Qdrant API error during search: {e}")
        raise QdrantError(
            f"Failed to search similar issues: {e}",
            collection=COLLECTION_NAME,
            operation="search",
            details={"limit": limit},
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        raise QdrantError(
            f"Failed to search similar issues: {str(e)}",
            collection=COLLECTION_NAME,
            operation="search",
            details={"limit": limit},
            original_error=e,
        )


@log_operation("qdrant.delete")
async def delete_issue_vectors(issue_id: str) -> bool:
    """Delete issue vectors from Qdrant.

    Args:
        issue_id: Issue ID to delete.

    Returns:
        bool: True if deleted successfully.

    Raises:
        QdrantError: If deletion fails.
    """
    try:
        client = get_qdrant_client()
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[issue_id],
        )
        logger.debug(f"Deleted vectors for issue {issue_id}")
        return True
    except UnexpectedResponse as e:
        logger.error(f"Qdrant API error during delete for issue {issue_id}: {e}")
        raise QdrantError(
            f"Failed to delete issue vectors: {e}",
            collection=COLLECTION_NAME,
            operation="delete",
            details={"issue_id": issue_id},
            original_error=e,
        )
    except Exception as e:
        logger.warning(f"Failed to delete issue vectors for {issue_id}: {e}")
        raise QdrantError(
            f"Failed to delete issue vectors: {str(e)}",
            collection=COLLECTION_NAME,
            operation="delete",
            details={"issue_id": issue_id},
            original_error=e,
        )


@log_operation("qdrant.get")
async def get_issue_by_id(issue_id: str) -> Optional[Dict[str, Any]]:
    """Get issue vectors and payload by ID.

    Args:
        issue_id: Issue ID.

    Returns:
        Optional[Dict[str, Any]]: Issue data or None if not found.

    Raises:
        QdrantError: If retrieval fails.
    """
    try:
        client = get_qdrant_client()
        results = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[issue_id],
            with_payload=True,
            with_vectors=False,
        )
        if results:
            logger.debug(f"Retrieved issue {issue_id} from Qdrant")
            return {
                "id": str(results[0].id),
                "payload": results[0].payload,
            }
        logger.debug(f"Issue {issue_id} not found in Qdrant")
        return None
    except UnexpectedResponse as e:
        logger.error(f"Qdrant API error during get for issue {issue_id}: {e}")
        raise QdrantError(
            f"Failed to get issue by ID: {e}",
            collection=COLLECTION_NAME,
            operation="get",
            details={"issue_id": issue_id},
            original_error=e,
        )
    except Exception as e:
        logger.warning(f"Failed to get issue {issue_id} from Qdrant: {e}")
        raise QdrantError(
            f"Failed to get issue by ID: {str(e)}",
            collection=COLLECTION_NAME,
            operation="get",
            details={"issue_id": issue_id},
            original_error=e,
        )
