"""Tests for supabase_client.py database layer.

These tests verify the query and count functions work correctly,
including offset-based pagination via .range() and exact counts.

Run with: pytest tests/test_supabase_client.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from functools import partial

pytestmark = pytest.mark.integration


class TestSyncQuery:
    """Tests for _sync_query function."""

    def test_sync_query_uses_range_with_offset(self) -> None:
        """Test that _sync_query calls .range(offset, offset+limit-1) instead of .limit()."""
        try:
            from src.db.supabase_client import _sync_query
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_range = MagicMock()
        mock_select.range.return_value = mock_range
        mock_range.execute.return_value = MagicMock(data=[])

        _sync_query(
            client=mock_client,
            table="test_table",
            filters=None,
            select="*",
            limit=20,
            order_by=None,
            ascending=False,
            gte_filters=None,
            offset=40,
        )

        # Should call .range(40, 59) not .limit(20)
        mock_select.range.assert_called_once_with(40, 59)
        mock_select.limit.assert_not_called()

    def test_sync_query_default_offset_zero(self) -> None:
        """Test that _sync_query defaults offset to 0."""
        try:
            from src.db.supabase_client import _sync_query
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_range = MagicMock()
        mock_select.range.return_value = mock_range
        mock_range.execute.return_value = MagicMock(data=[])

        _sync_query(
            client=mock_client,
            table="test_table",
            filters=None,
            select="*",
            limit=10,
            order_by=None,
            ascending=False,
        )

        # offset defaults to 0: .range(0, 9)
        mock_select.range.assert_called_once_with(0, 9)

    def test_sync_query_applies_filters_before_range(self) -> None:
        """Test that filters are applied before range."""
        try:
            from src.db.supabase_client import _sync_query
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_eq = MagicMock()
        mock_select.eq.return_value = mock_eq
        mock_order = MagicMock()
        mock_eq.order.return_value = mock_order
        mock_range = MagicMock()
        mock_order.range.return_value = mock_range
        mock_range.execute.return_value = MagicMock(data=[])

        _sync_query(
            client=mock_client,
            table="test_table",
            filters={"status": "active"},
            select="*",
            limit=20,
            order_by="created_at",
            ascending=False,
            offset=20,
        )

        mock_select.eq.assert_called_once_with("status", "active")
        mock_eq.order.assert_called_once_with("created_at", desc=True)
        mock_order.range.assert_called_once_with(20, 39)


class TestSyncCount:
    """Tests for _sync_count function."""

    def test_sync_count_uses_exact_count_with_zero_limit(self) -> None:
        """Test that _sync_count calls .select('*', count='exact').limit(0)."""
        try:
            from src.db.supabase_client import _sync_count
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_limit = MagicMock()
        mock_select.limit.return_value = mock_limit
        mock_limit.execute.return_value = MagicMock(count=42)

        result = _sync_count(
            client=mock_client,
            table="master_issues",
            filters=None,
        )

        mock_table.select.assert_called_once_with("*", count="exact")
        mock_select.limit.assert_called_once_with(0)
        assert result == 42

    def test_sync_count_applies_filters(self) -> None:
        """Test that _sync_count applies eq and gte filters."""
        try:
            from src.db.supabase_client import _sync_count
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        mock_limit = MagicMock()
        mock_select.limit.return_value = mock_limit
        mock_eq = MagicMock()
        mock_limit.eq.return_value = mock_eq
        mock_gte = MagicMock()
        mock_eq.gte.return_value = mock_gte
        mock_gte.execute.return_value = MagicMock(count=5)

        # Chain properly: select -> limit -> eq -> gte -> execute
        mock_select.limit.return_value = mock_limit
        mock_limit.eq = MagicMock(return_value=mock_eq)
        mock_eq.gte = MagicMock(return_value=mock_gte)

        # Actually, PostgREST chains differently: select -> limit then we add filters
        # Let me set up the chain correctly. The code does:
        # query = client.table(table).select("*", count="exact").limit(0)
        # then query = query.eq(...)
        # then query = query.gte(...)

        # Reset and set up correct chain
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.execute.return_value = MagicMock(count=5)

        result = _sync_count(
            client=mock_client,
            table="master_issues",
            filters={"status": "active"},
            gte_filters={"created_at": "2024-01-01T00:00:00Z"},
        )

        mock_table.select.assert_called_once_with("*", count="exact")
        mock_query.limit.assert_called_once_with(0)
        mock_query.eq.assert_called_once_with("status", "active")
        mock_query.gte.assert_called_once_with("created_at", "2024-01-01T00:00:00Z")
        assert result == 5

    def test_sync_count_returns_zero_when_count_is_none(self) -> None:
        """Test that _sync_count returns 0 when count is None."""
        try:
            from src.db.supabase_client import _sync_count
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_query = MagicMock()
        mock_table.select.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = MagicMock(count=None)

        result = _sync_count(
            client=mock_client,
            table="master_issues",
            filters=None,
        )

        assert result == 0


class TestCountRecords:
    """Tests for count_records async wrapper."""

    @pytest.mark.asyncio
    async def test_count_records_returns_count(self) -> None:
        """Test that count_records returns the count from _sync_count."""
        try:
            from src.db.supabase_client import count_records
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.supabase_client.get_supabase_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            mock_query = MagicMock()
            mock_client.table.return_value = mock_query
            mock_query.select.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.execute.return_value = MagicMock(count=25)

            result = await count_records(table="master_issues")
            assert result == 25

    @pytest.mark.asyncio
    async def test_count_records_passes_filters(self) -> None:
        """Test that count_records forwards filters to _sync_count."""
        try:
            from src.db.supabase_client import count_records
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.supabase_client.get_supabase_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            mock_query = MagicMock()
            mock_client.table.return_value = mock_query
            mock_query.select.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.eq.return_value = mock_query
            mock_query.execute.return_value = MagicMock(count=10)

            result = await count_records(
                table="master_issues",
                filters={"status": "active"},
            )
            assert result == 10
            mock_query.eq.assert_called_once_with("status", "active")

    @pytest.mark.asyncio
    async def test_count_records_raises_supabase_error_on_api_error(self) -> None:
        """Test that count_records wraps APIError in SupabaseError."""
        try:
            from src.db.supabase_client import count_records
            from src.exceptions import SupabaseError
            from postgrest.exceptions import APIError
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.supabase_client.get_supabase_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            mock_query = MagicMock()
            mock_client.table.return_value = mock_query
            mock_query.select.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.execute.side_effect = APIError({"message": "test error"})

            with pytest.raises(SupabaseError, match="Failed to count records"):
                await count_records(table="master_issues")


class TestQueryRecordsOffset:
    """Tests for offset parameter in query_records."""

    @pytest.mark.asyncio
    async def test_query_records_passes_offset(self) -> None:
        """Test that query_records forwards offset to _sync_query."""
        try:
            from src.db.supabase_client import query_records
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.supabase_client.get_supabase_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            mock_query = MagicMock()
            mock_client.table.return_value = mock_query
            mock_query.select.return_value = mock_query
            mock_query.range.return_value = mock_query
            mock_query.execute.return_value = MagicMock(data=[])

            result = await query_records(
                table="master_issues",
                limit=20,
                offset=40,
            )
            assert result == []
            # .range(40, 59) should be called
            mock_query.range.assert_called_once_with(40, 59)

    @pytest.mark.asyncio
    async def test_query_records_default_offset_zero(self) -> None:
        """Test that query_records defaults offset to 0."""
        try:
            from src.db.supabase_client import query_records
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.supabase_client.get_supabase_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            mock_query = MagicMock()
            mock_client.table.return_value = mock_query
            mock_query.select.return_value = mock_query
            mock_query.range.return_value = mock_query
            mock_query.execute.return_value = MagicMock(data=[{"id": "1"}])

            result = await query_records(table="master_issues", limit=10)
            assert len(result) == 1
            mock_query.range.assert_called_once_with(0, 9)
