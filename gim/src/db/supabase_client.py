"""Supabase database client wrapper."""

from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from src.config import get_settings


_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client singleton.

    Returns:
        Client: Supabase client instance.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


async def insert_record(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a record into a table.

    Args:
        table: Table name.
        data: Record data.

    Returns:
        Dict[str, Any]: Inserted record.
    """
    client = get_supabase_client()
    result = client.table(table).insert(data).execute()
    return result.data[0] if result.data else {}


async def update_record(
    table: str,
    record_id: str,
    data: Dict[str, Any],
    id_column: str = "id",
) -> Dict[str, Any]:
    """Update a record in a table.

    Args:
        table: Table name.
        record_id: Record ID.
        data: Updated data.
        id_column: ID column name.

    Returns:
        Dict[str, Any]: Updated record.
    """
    client = get_supabase_client()
    result = client.table(table).update(data).eq(id_column, record_id).execute()
    return result.data[0] if result.data else {}


async def get_record(
    table: str,
    record_id: str,
    id_column: str = "id",
) -> Optional[Dict[str, Any]]:
    """Get a record by ID.

    Args:
        table: Table name.
        record_id: Record ID.
        id_column: ID column name.

    Returns:
        Optional[Dict[str, Any]]: Record or None if not found.
    """
    client = get_supabase_client()
    result = client.table(table).select("*").eq(id_column, record_id).execute()
    return result.data[0] if result.data else None


async def query_records(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    select: str = "*",
    limit: int = 100,
    order_by: Optional[str] = None,
    ascending: bool = False,
) -> List[Dict[str, Any]]:
    """Query records from a table.

    Args:
        table: Table name.
        filters: Dictionary of column->value filters.
        select: Columns to select.
        limit: Maximum records to return.
        order_by: Column to order by.
        ascending: Sort order.

    Returns:
        List[Dict[str, Any]]: List of records.
    """
    client = get_supabase_client()
    query = client.table(table).select(select)

    if filters:
        for column, value in filters.items():
            query = query.eq(column, value)

    if order_by:
        query = query.order(order_by, desc=not ascending)

    query = query.limit(limit)
    result = query.execute()
    return result.data or []


async def delete_record(
    table: str,
    record_id: str,
    id_column: str = "id",
) -> bool:
    """Delete a record by ID.

    Args:
        table: Table name.
        record_id: Record ID.
        id_column: ID column name.

    Returns:
        bool: True if deleted, False otherwise.
    """
    client = get_supabase_client()
    result = client.table(table).delete().eq(id_column, record_id).execute()
    return len(result.data or []) > 0


async def increment_field(
    table: str,
    record_id: str,
    field: str,
    amount: int = 1,
    id_column: str = "id",
) -> Dict[str, Any]:
    """Increment a numeric field.

    Args:
        table: Table name.
        record_id: Record ID.
        field: Field to increment.
        amount: Amount to increment by.
        id_column: ID column name.

    Returns:
        Dict[str, Any]: Updated record.
    """
    client = get_supabase_client()
    # Use RPC for atomic increment
    result = client.rpc(
        "increment_field",
        {
            "p_table": table,
            "p_id": record_id,
            "p_field": field,
            "p_amount": amount,
        }
    ).execute()
    return result.data if result.data else {}
