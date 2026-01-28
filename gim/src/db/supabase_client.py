"""Supabase database client wrapper with error handling and logging."""

import asyncio
import threading
from functools import partial
from typing import Any, Dict, List, Optional

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError

from src.config import get_settings
from src.exceptions import SupabaseError
from src.logging_config import get_logger, log_operation


_client: Optional[Client] = None
_client_lock = threading.Lock()
logger = get_logger("db.supabase")


def get_supabase_client() -> Client:
    """Get or create Supabase client singleton.

    Thread-safe singleton pattern using double-checked locking.

    Returns:
        Client: Supabase client instance.

    Raises:
        SupabaseError: If client creation fails.
    """
    global _client
    if _client is None:
        with _client_lock:
            # Double-check after acquiring lock
            if _client is None:
                try:
                    settings = get_settings()
                    _client = create_client(settings.supabase_url, settings.supabase_key)
                    logger.info("Supabase client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Supabase client: {e}")
                    raise SupabaseError(
                        "Failed to initialize Supabase client",
                        operation="connect",
                        original_error=e,
                    )
    return _client


def _sync_insert(client: Client, table: str, data: Dict[str, Any]) -> Any:
    """Synchronous insert operation."""
    return client.table(table).insert(data).execute()


@log_operation("supabase.insert")
async def insert_record(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a record into a table.

    Args:
        table: Table name.
        data: Record data.

    Returns:
        Dict[str, Any]: Inserted record.

    Raises:
        SupabaseError: If insertion fails.
    """
    try:
        client = get_supabase_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, partial(_sync_insert, client, table, data)
        )
        logger.debug(f"Inserted record into {table}")
        return result.data[0] if result.data else {}
    except APIError as e:
        logger.error(f"Supabase API error during insert to {table}: {e.message}")
        raise SupabaseError(
            f"Failed to insert record: {e.message}",
            table=table,
            operation="insert",
            details={"code": e.code} if hasattr(e, "code") else None,
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during insert to {table}: {e}")
        raise SupabaseError(
            f"Failed to insert record: {str(e)}",
            table=table,
            operation="insert",
            original_error=e,
        )


def _sync_update(
    client: Client, table: str, record_id: str, data: Dict[str, Any], id_column: str
) -> Any:
    """Synchronous update operation."""
    return client.table(table).update(data).eq(id_column, record_id).execute()


@log_operation("supabase.update")
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

    Raises:
        SupabaseError: If update fails.
    """
    try:
        client = get_supabase_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, partial(_sync_update, client, table, record_id, data, id_column)
        )
        logger.debug(f"Updated record {record_id} in {table}")
        return result.data[0] if result.data else {}
    except APIError as e:
        logger.error(f"Supabase API error during update in {table}: {e.message}")
        raise SupabaseError(
            f"Failed to update record: {e.message}",
            table=table,
            operation="update",
            details={"record_id": record_id, "code": e.code if hasattr(e, "code") else None},
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during update in {table}: {e}")
        raise SupabaseError(
            f"Failed to update record: {str(e)}",
            table=table,
            operation="update",
            details={"record_id": record_id},
            original_error=e,
        )


def _sync_get(client: Client, table: str, record_id: str, id_column: str) -> Any:
    """Synchronous get operation."""
    return client.table(table).select("*").eq(id_column, record_id).execute()


@log_operation("supabase.get")
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

    Raises:
        SupabaseError: If query fails.
    """
    try:
        client = get_supabase_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, partial(_sync_get, client, table, record_id, id_column)
        )
        if result.data:
            logger.debug(f"Retrieved record {record_id} from {table}")
            return result.data[0]
        logger.debug(f"Record {record_id} not found in {table}")
        return None
    except APIError as e:
        logger.error(f"Supabase API error during get from {table}: {e.message}")
        raise SupabaseError(
            f"Failed to get record: {e.message}",
            table=table,
            operation="get",
            details={"record_id": record_id},
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during get from {table}: {e}")
        raise SupabaseError(
            f"Failed to get record: {str(e)}",
            table=table,
            operation="get",
            details={"record_id": record_id},
            original_error=e,
        )


def _sync_query(
    client: Client,
    table: str,
    filters: Optional[Dict[str, Any]],
    select: str,
    limit: int,
    order_by: Optional[str],
    ascending: bool,
) -> Any:
    """Synchronous query operation."""
    query = client.table(table).select(select)

    if filters:
        for column, value in filters.items():
            query = query.eq(column, value)

    if order_by:
        query = query.order(order_by, desc=not ascending)

    query = query.limit(limit)
    return query.execute()


@log_operation("supabase.query")
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

    Raises:
        SupabaseError: If query fails.
    """
    try:
        client = get_supabase_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(_sync_query, client, table, filters, select, limit, order_by, ascending),
        )
        record_count = len(result.data or [])
        logger.debug(f"Queried {record_count} records from {table}")
        return result.data or []
    except APIError as e:
        logger.error(f"Supabase API error during query on {table}: {e.message}")
        raise SupabaseError(
            f"Failed to query records: {e.message}",
            table=table,
            operation="query",
            details={"filters": filters, "limit": limit},
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during query on {table}: {e}")
        raise SupabaseError(
            f"Failed to query records: {str(e)}",
            table=table,
            operation="query",
            details={"filters": filters, "limit": limit},
            original_error=e,
        )


def _sync_delete(client: Client, table: str, record_id: str, id_column: str) -> Any:
    """Synchronous delete operation."""
    return client.table(table).delete().eq(id_column, record_id).execute()


@log_operation("supabase.delete")
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

    Raises:
        SupabaseError: If deletion fails.
    """
    try:
        client = get_supabase_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, partial(_sync_delete, client, table, record_id, id_column)
        )
        deleted = len(result.data or []) > 0
        if deleted:
            logger.debug(f"Deleted record {record_id} from {table}")
        else:
            logger.debug(f"Record {record_id} not found in {table} for deletion")
        return deleted
    except APIError as e:
        logger.error(f"Supabase API error during delete from {table}: {e.message}")
        raise SupabaseError(
            f"Failed to delete record: {e.message}",
            table=table,
            operation="delete",
            details={"record_id": record_id},
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during delete from {table}: {e}")
        raise SupabaseError(
            f"Failed to delete record: {str(e)}",
            table=table,
            operation="delete",
            details={"record_id": record_id},
            original_error=e,
        )


def _sync_increment(
    client: Client, table: str, record_id: str, field: str, amount: int
) -> Any:
    """Synchronous increment operation."""
    return client.rpc(
        "increment_field",
        {
            "p_table": table,
            "p_id": record_id,
            "p_field": field,
            "p_amount": amount,
        }
    ).execute()


@log_operation("supabase.increment")
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

    Raises:
        SupabaseError: If increment fails.
    """
    try:
        client = get_supabase_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, partial(_sync_increment, client, table, record_id, field, amount)
        )
        logger.debug(f"Incremented {field} by {amount} for record {record_id} in {table}")
        return result.data if result.data else {}
    except APIError as e:
        logger.error(f"Supabase API error during increment in {table}: {e.message}")
        raise SupabaseError(
            f"Failed to increment field: {e.message}",
            table=table,
            operation="increment",
            details={"record_id": record_id, "field": field, "amount": amount},
            original_error=e,
        )
    except Exception as e:
        logger.error(f"Unexpected error during increment in {table}: {e}")
        raise SupabaseError(
            f"Failed to increment field: {str(e)}",
            table=table,
            operation="increment",
            details={"record_id": record_id, "field": field, "amount": amount},
            original_error=e,
        )
