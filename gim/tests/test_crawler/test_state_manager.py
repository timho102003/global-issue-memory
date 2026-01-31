"""Tests for the state manager module.

Mocks Supabase client for state CRUD operations.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.models.crawler_state import (
    CrawlerStateCreate,
    CrawlerStateExtracted,
    CrawlerStateFetched,
    CrawlerStatus,
)


@pytest.fixture
def mock_insert():
    """Mock insert_record.

    Yields:
        AsyncMock: Mock insert function.
    """
    with patch("src.crawler.state_manager.insert_record", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": str(uuid4())}
        yield mock


@pytest.fixture
def mock_update():
    """Mock update_record.

    Yields:
        AsyncMock: Mock update function.
    """
    with patch("src.crawler.state_manager.update_record", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": str(uuid4()), "status": "FETCHED"}
        yield mock


@pytest.fixture
def mock_query():
    """Mock query_records.

    Yields:
        AsyncMock: Mock query function.
    """
    with patch("src.crawler.state_manager.query_records", new_callable=AsyncMock) as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_count():
    """Mock count_records.

    Yields:
        AsyncMock: Mock count function.
    """
    with patch("src.crawler.state_manager.count_records", new_callable=AsyncMock) as mock:
        mock.return_value = 0
        yield mock


class TestCreatePendingIssues:
    """Tests for create_pending_issues."""

    async def test_creates_new_issues(self, mock_insert: AsyncMock, mock_query: AsyncMock) -> None:
        """New issues are inserted."""
        from src.crawler.state_manager import create_pending_issues

        mock_query.return_value = []  # No duplicates

        issues = [
            CrawlerStateCreate(
                repo="pallets/flask",
                issue_number=1,
                github_issue_id=100,
                issue_title="Fix TypeError",
            ),
            CrawlerStateCreate(
                repo="pallets/flask",
                issue_number=2,
                github_issue_id=200,
                issue_title="Fix ValueError",
            ),
        ]

        created = await create_pending_issues(issues)
        assert created == 2
        assert mock_insert.call_count == 2

    async def test_skips_duplicates(self, mock_insert: AsyncMock, mock_query: AsyncMock) -> None:
        """Duplicate issues are skipped."""
        from src.crawler.state_manager import create_pending_issues

        mock_query.return_value = [{"id": str(uuid4())}]  # Already exists

        issues = [
            CrawlerStateCreate(
                repo="pallets/flask",
                issue_number=1,
                github_issue_id=100,
                issue_title="Fix TypeError",
            ),
        ]

        created = await create_pending_issues(issues)
        assert created == 0
        mock_insert.assert_not_called()

    async def test_handles_insert_error(
        self, mock_insert: AsyncMock, mock_query: AsyncMock
    ) -> None:
        """Insert errors are handled gracefully."""
        from src.crawler.state_manager import create_pending_issues

        mock_query.return_value = []
        mock_insert.side_effect = Exception("DB error")

        issues = [
            CrawlerStateCreate(
                repo="pallets/flask",
                issue_number=1,
                github_issue_id=100,
                issue_title="Fix TypeError",
            ),
        ]

        created = await create_pending_issues(issues)
        assert created == 0


class TestUpdateToFetched:
    """Tests for update_to_fetched."""

    async def test_updates_status(self, mock_update: AsyncMock) -> None:
        """Record is updated to FETCHED with data."""
        from src.crawler.state_manager import update_to_fetched

        record_id = str(uuid4())
        data = CrawlerStateFetched(
            has_merged_pr=True,
            pr_number=42,
            raw_issue_body="Issue body",
            raw_comments=[{"author": "user", "body": "comment"}],
        )

        await update_to_fetched(record_id, data)

        mock_update.assert_called_once()
        call_kwargs = mock_update.call_args
        update_data = call_kwargs.kwargs.get("data") or call_kwargs[1].get("data")
        if update_data is None:
            # Positional args
            update_data = call_kwargs[0][2] if len(call_kwargs[0]) > 2 else call_kwargs.kwargs["data"]
        assert update_data["status"] == "FETCHED"
        assert update_data["has_merged_pr"] is True
        assert update_data["pr_number"] == 42


class TestUpdateToExtracted:
    """Tests for update_to_extracted."""

    async def test_updates_with_extraction_results(self, mock_update: AsyncMock) -> None:
        """Record is updated with extraction results."""
        from src.crawler.state_manager import update_to_extracted

        record_id = str(uuid4())
        data = CrawlerStateExtracted(
            extracted_error="TypeError: test",
            extracted_root_cause="None check missing",
            extracted_fix_summary="Added guard",
            extracted_fix_steps=["Step 1"],
            extraction_confidence=0.85,
            quality_score=0.7,
        )

        await update_to_extracted(record_id, data)

        mock_update.assert_called_once()
        call_args = mock_update.call_args
        update_data = call_args.kwargs.get("data") or call_args[0][2]
        assert update_data["status"] == "EXTRACTED"
        assert update_data["extracted_error"] == "TypeError: test"
        assert update_data["quality_score"] == 0.7


class TestUpdateToSubmitted:
    """Tests for update_to_submitted."""

    async def test_updates_with_gim_id(self, mock_update: AsyncMock) -> None:
        """Record is updated with GIM issue ID."""
        from src.crawler.state_manager import update_to_submitted

        record_id = str(uuid4())
        gim_id = str(uuid4())

        await update_to_submitted(record_id, gim_id)

        mock_update.assert_called_once()
        call_args = mock_update.call_args
        update_data = call_args.kwargs.get("data") or call_args[0][2]
        assert update_data["status"] == "SUBMITTED"
        assert update_data["gim_issue_id"] == gim_id


class TestUpdateToDropped:
    """Tests for update_to_dropped."""

    async def test_sets_drop_reason(self, mock_update: AsyncMock) -> None:
        """Record is dropped with reason."""
        from src.crawler.state_manager import update_to_dropped

        record_id = str(uuid4())
        await update_to_dropped(record_id, "LOW_QUALITY")

        mock_update.assert_called_once()
        call_args = mock_update.call_args
        update_data = call_args.kwargs.get("data") or call_args[0][2]
        assert update_data["status"] == "DROPPED"
        assert update_data["drop_reason"] == "LOW_QUALITY"


class TestUpdateToError:
    """Tests for update_to_error."""

    async def test_increments_retry_count(
        self, mock_update: AsyncMock, mock_query: AsyncMock
    ) -> None:
        """Retry count is incremented on error."""
        from src.crawler.state_manager import update_to_error

        mock_query.return_value = [{"retry_count": 2}]
        record_id = str(uuid4())

        await update_to_error(record_id, "Some error")

        mock_update.assert_called_once()
        call_args = mock_update.call_args
        update_data = call_args.kwargs.get("data") or call_args[0][2]
        assert update_data["status"] == "ERROR"
        assert update_data["retry_count"] == 3
        assert update_data["last_error"] == "Some error"


class TestGetIssuesByStatus:
    """Tests for get_issues_by_status."""

    async def test_queries_by_status(self, mock_query: AsyncMock) -> None:
        """Issues are queried by status."""
        from src.crawler.state_manager import get_issues_by_status

        mock_query.return_value = [
            {"id": str(uuid4()), "status": "PENDING", "repo": "pallets/flask"}
        ]

        result = await get_issues_by_status(CrawlerStatus.PENDING)
        assert len(result) == 1
        mock_query.assert_called_once()

    async def test_filters_by_repo(self, mock_query: AsyncMock) -> None:
        """Optional repo filter is applied."""
        from src.crawler.state_manager import get_issues_by_status

        await get_issues_by_status(CrawlerStatus.PENDING, repo="pallets/flask")

        call_args = mock_query.call_args
        filters = call_args.kwargs.get("filters") or call_args[0][0]
        if isinstance(filters, dict):
            assert filters.get("repo") == "pallets/flask"


class TestGetStats:
    """Tests for get_stats."""

    async def test_returns_all_statuses(self, mock_count: AsyncMock) -> None:
        """Stats include all statuses."""
        from src.crawler.state_manager import get_stats

        mock_count.return_value = 5

        stats = await get_stats()
        assert len(stats) == len(CrawlerStatus)
        for status in CrawlerStatus:
            assert status.value in stats
            assert stats[status.value] == 5


class TestIssueExists:
    """Tests for issue_exists."""

    async def test_exists(self, mock_query: AsyncMock) -> None:
        """Returns True when issue exists."""
        from src.crawler.state_manager import issue_exists

        mock_query.return_value = [{"id": str(uuid4())}]
        assert await issue_exists("pallets/flask", 1) is True

    async def test_not_exists(self, mock_query: AsyncMock) -> None:
        """Returns False when issue doesn't exist."""
        from src.crawler.state_manager import issue_exists

        mock_query.return_value = []
        assert await issue_exists("pallets/flask", 999) is False
