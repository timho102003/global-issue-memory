"""Tests for issue_resolver module.

Covers resolve_issue_id which maps any issue ID (master or child) to its
master issue record, handling child->master lookup with graceful fallbacks.

Run with: pytest tests/test_db/test_issue_resolver.py -v
"""

import pytest
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from src.db.issue_resolver import resolve_issue_id


@pytest.fixture
def master_issue_id() -> str:
    """Generate a UUID representing a master issue ID.

    Returns:
        str: A UUID string for a master issue.
    """
    return str(uuid4())


@pytest.fixture
def child_issue_id() -> str:
    """Generate a UUID representing a child issue ID.

    Returns:
        str: A UUID string for a child issue.
    """
    return str(uuid4())


@pytest.fixture
def master_record(master_issue_id: str) -> Dict[str, Any]:
    """Build a sample master issue record.

    Args:
        master_issue_id: UUID string for the master issue.

    Returns:
        Dict[str, Any]: A dictionary resembling a master_issues row.
    """
    return {
        "id": master_issue_id,
        "title": "Sample master issue",
        "status": "open",
    }


@pytest.fixture
def child_record(child_issue_id: str, master_issue_id: str) -> Dict[str, Any]:
    """Build a sample child issue record that references a master issue.

    Args:
        child_issue_id: UUID string for the child issue.
        master_issue_id: UUID string for the parent master issue.

    Returns:
        Dict[str, Any]: A dictionary resembling a child_issues row.
    """
    return {
        "id": child_issue_id,
        "master_issue_id": master_issue_id,
        "title": "Sample child issue",
    }


@pytest.mark.asyncio
@pytest.mark.integration
async def test_resolve_master_issue_directly(
    master_issue_id: str,
    master_record: Dict[str, Any],
) -> None:
    """Resolve an ID that exists in master_issues returns (master, None, False)."""

    async def _mock_get_record(
        table: str, record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return the master record when queried against master_issues.

        Args:
            table: Table name being queried.
            record_id: ID to look up.

        Returns:
            Optional[Dict[str, Any]]: The master record or None.
        """
        if table == "master_issues" and record_id == master_issue_id:
            return master_record
        return None

    with patch(
        "src.db.issue_resolver.get_record",
        new=AsyncMock(side_effect=_mock_get_record),
    ):
        master, child, is_child = await resolve_issue_id(master_issue_id)

    assert master == master_record
    assert child is None
    assert is_child is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_resolve_child_to_master(
    master_issue_id: str,
    child_issue_id: str,
    master_record: Dict[str, Any],
    child_record: Dict[str, Any],
) -> None:
    """Resolve a child ID fetches the child, then its master, returning (master, child, True)."""

    async def _mock_get_record(
        table: str, record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return the correct record based on table and ID.

        Args:
            table: Table name being queried.
            record_id: ID to look up.

        Returns:
            Optional[Dict[str, Any]]: Matching record or None.
        """
        if table == "master_issues" and record_id == master_issue_id:
            return master_record
        if table == "child_issues" and record_id == child_issue_id:
            return child_record
        return None

    with patch(
        "src.db.issue_resolver.get_record",
        new=AsyncMock(side_effect=_mock_get_record),
    ):
        master, child, is_child = await resolve_issue_id(child_issue_id)

    assert master == master_record
    assert child == child_record
    assert is_child is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_resolve_not_found() -> None:
    """Resolve a non-existent ID returns (None, None, False)."""
    nonexistent_id = str(uuid4())

    with patch(
        "src.db.issue_resolver.get_record",
        new=AsyncMock(return_value=None),
    ):
        master, child, is_child = await resolve_issue_id(nonexistent_id)

    assert master is None
    assert child is None
    assert is_child is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_resolve_child_with_missing_master(
    child_issue_id: str,
    child_record: Dict[str, Any],
) -> None:
    """Resolve a child whose master no longer exists returns (None, child, True)."""

    async def _mock_get_record(
        table: str, record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return only the child record; master lookup always returns None.

        Args:
            table: Table name being queried.
            record_id: ID to look up.

        Returns:
            Optional[Dict[str, Any]]: The child record or None.
        """
        if table == "child_issues" and record_id == child_issue_id:
            return child_record
        return None

    with patch(
        "src.db.issue_resolver.get_record",
        new=AsyncMock(side_effect=_mock_get_record),
    ):
        master, child, is_child = await resolve_issue_id(child_issue_id)

    assert master is None
    assert child == child_record
    assert is_child is True
