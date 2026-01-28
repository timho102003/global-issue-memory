"""Qdrant vector database client wrapper."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    VectorParams,
    SearchParams,
)

from src.config import get_settings


_client: Optional[QdrantClient] = None

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

    Returns:
        QdrantClient: Qdrant client instance.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
    return _client


async def ensure_collection_exists() -> None:
    """Ensure the GIM issues collection exists with proper configuration."""
    client = get_qdrant_client()
    vector_dim = _get_vector_dim()

    # Check if collection exists
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if COLLECTION_NAME not in collection_names:
        # Create collection with multi-vector config
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "error_signature": VectorParams(
                    size=vector_dim,
                    distance=Distance.COSINE,
                ),
                "root_cause": VectorParams(
                    size=vector_dim,
                    distance=Distance.COSINE,
                ),
                "fix_summary": VectorParams(
                    size=vector_dim,
                    distance=Distance.COSINE,
                ),
            },
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


async def upsert_issue_vectors(
    issue_id: str,
    error_signature_vector: List[float],
    root_cause_vector: List[float],
    fix_summary_vector: List[float],
    payload: Dict[str, Any],
) -> None:
    """Upsert issue vectors into Qdrant.

    Args:
        issue_id: Unique issue ID.
        error_signature_vector: Vector for error signature.
        root_cause_vector: Vector for root cause description.
        fix_summary_vector: Vector for fix summary.
        payload: Additional metadata payload.
    """
    client = get_qdrant_client()
    await ensure_collection_exists()

    point = PointStruct(
        id=issue_id,
        vector={
            "error_signature": error_signature_vector,
            "root_cause": root_cause_vector,
            "fix_summary": fix_summary_vector,
        },
        payload=payload,
    )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[point],
    )


async def search_similar_issues(
    query_vector: List[float],
    vector_name: str = "error_signature",
    limit: int = 10,
    score_threshold: float = 0.5,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Search for similar issues using vector similarity.

    Args:
        query_vector: Query embedding vector.
        vector_name: Which vector to search against.
        limit: Maximum results to return.
        score_threshold: Minimum similarity score.
        filters: Optional filters (e.g., root_cause_category, model_provider).

    Returns:
        List[Dict[str, Any]]: List of matching issues with scores.
    """
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

    # Use query_points with 'using' parameter for named vectors
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        using=vector_name,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=query_filter,
        with_payload=True,
    )

    return [
        {
            "id": str(point.id),
            "score": point.score,
            "payload": point.payload,
        }
        for point in response.points
    ]


async def delete_issue_vectors(issue_id: str) -> bool:
    """Delete issue vectors from Qdrant.

    Args:
        issue_id: Issue ID to delete.

    Returns:
        bool: True if deleted successfully.
    """
    client = get_qdrant_client()

    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[issue_id],
        )
        return True
    except Exception:
        return False


async def get_issue_by_id(issue_id: str) -> Optional[Dict[str, Any]]:
    """Get issue vectors and payload by ID.

    Args:
        issue_id: Issue ID.

    Returns:
        Optional[Dict[str, Any]]: Issue data or None if not found.
    """
    client = get_qdrant_client()

    try:
        results = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[issue_id],
            with_payload=True,
            with_vectors=False,
        )
        if results:
            return {
                "id": str(results[0].id),
                "payload": results[0].payload,
            }
        return None
    except Exception:
        return None
