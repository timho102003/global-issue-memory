"""Tests for Supabase client wrapper, focusing on query_records and gte_filters.

Run with: pytest tests/test_db/test_supabase_client.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from functools import partial

from src.db.supabase_client import _sync_query


class TestSyncQueryGteFilters:
    """Tests for _sync_query gte_filters parameter."""

    def _make_mock_client(self) -> MagicMock:
        """Create a mock Supabase client with chained query methods.

        Returns:
            MagicMock: A mock client supporting .table().select().eq().gte().order().limit().execute().
        """
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_client.table.return_value.select.return_value = mock_query

        # Make all chainable methods return the same mock_query
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[{"id": "1"}])

        return mock_client

    def test_sync_query_no_gte_filters(self) -> None:
        """Test _sync_query without gte_filters does not call .gte()."""
        client = self._make_mock_client()
        query_mock = client.table.return_value.select.return_value

        _sync_query(
            client=client,
            table="master_issues",
            filters=None,
            select="*",
            limit=10,
            order_by="created_at",
            ascending=False,
        )

        query_mock.gte.assert_not_called()

    def test_sync_query_with_gte_filters(self) -> None:
        """Test _sync_query with gte_filters calls .gte() for each filter."""
        client = self._make_mock_client()
        query_mock = client.table.return_value.select.return_value

        _sync_query(
            client=client,
            table="master_issues",
            filters=None,
            select="*",
            limit=10,
            order_by="created_at",
            ascending=False,
            gte_filters={"created_at": "2024-01-01T00:00:00+00:00"},
        )

        query_mock.gte.assert_called_once_with("created_at", "2024-01-01T00:00:00+00:00")

    def test_sync_query_with_multiple_gte_filters(self) -> None:
        """Test _sync_query with multiple gte_filters calls .gte() for each."""
        client = self._make_mock_client()
        query_mock = client.table.return_value.select.return_value

        _sync_query(
            client=client,
            table="master_issues",
            filters=None,
            select="*",
            limit=10,
            order_by=None,
            ascending=False,
            gte_filters={
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-06-01T00:00:00+00:00",
            },
        )

        assert query_mock.gte.call_count == 2

    def test_sync_query_with_both_filters_and_gte_filters(self) -> None:
        """Test _sync_query applies both eq filters and gte filters."""
        client = self._make_mock_client()
        query_mock = client.table.return_value.select.return_value

        _sync_query(
            client=client,
            table="master_issues",
            filters={"status": "active"},
            select="*",
            limit=10,
            order_by="created_at",
            ascending=False,
            gte_filters={"created_at": "2024-01-01T00:00:00+00:00"},
        )

        query_mock.eq.assert_called_once_with("status", "active")
        query_mock.gte.assert_called_once_with("created_at", "2024-01-01T00:00:00+00:00")

    def test_sync_query_with_empty_gte_filters(self) -> None:
        """Test _sync_query with empty gte_filters dict does not call .gte()."""
        client = self._make_mock_client()
        query_mock = client.table.return_value.select.return_value

        _sync_query(
            client=client,
            table="master_issues",
            filters=None,
            select="*",
            limit=10,
            order_by=None,
            ascending=False,
            gte_filters={},
        )

        query_mock.gte.assert_not_called()

    def test_sync_query_gte_filters_none_default(self) -> None:
        """Test _sync_query defaults gte_filters to None when not provided."""
        client = self._make_mock_client()
        query_mock = client.table.return_value.select.return_value

        # Call without gte_filters argument at all
        _sync_query(
            client=client,
            table="master_issues",
            filters=None,
            select="*",
            limit=10,
            order_by=None,
            ascending=False,
        )

        query_mock.gte.assert_not_called()
