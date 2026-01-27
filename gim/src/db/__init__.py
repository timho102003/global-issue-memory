"""Database clients and repositories for GIM."""

from src.db.supabase_client import (
    get_supabase_client,
    insert_record,
    update_record,
    get_record,
    query_records,
    delete_record,
)
from src.db.qdrant_client import (
    get_qdrant_client,
    ensure_collection_exists,
    upsert_issue_vectors,
    search_similar_issues,
    delete_issue_vectors,
)

__all__ = [
    "get_supabase_client",
    "insert_record",
    "update_record",
    "get_record",
    "query_records",
    "delete_record",
    "get_qdrant_client",
    "ensure_collection_exists",
    "upsert_issue_vectors",
    "search_similar_issues",
    "delete_issue_vectors",
]
