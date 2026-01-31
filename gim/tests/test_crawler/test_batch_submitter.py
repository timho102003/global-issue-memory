"""Tests for the batch submitter orchestrator.

Mocks state_manager and batch_submission_service.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.services.batch_submission_service import SubmissionResult


@pytest.fixture
def mock_get_issues():
    """Mock get_issues_by_status.

    Yields:
        AsyncMock: Mock function.
    """
    with patch(
        "src.crawler.batch_submitter.get_issues_by_status",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_submit():
    """Mock submit_crawled_issue.

    Yields:
        AsyncMock: Mock function.
    """
    with patch(
        "src.crawler.batch_submitter.submit_crawled_issue",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_update_submitted():
    """Mock update_to_submitted.

    Yields:
        AsyncMock: Mock function.
    """
    with patch(
        "src.crawler.batch_submitter.update_to_submitted",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_update_dropped():
    """Mock update_to_dropped.

    Yields:
        AsyncMock: Mock function.
    """
    with patch(
        "src.crawler.batch_submitter.update_to_dropped",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_update_error():
    """Mock update_to_error.

    Yields:
        AsyncMock: Mock function.
    """
    with patch(
        "src.crawler.batch_submitter.update_to_error",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


def _make_extracted_record(
    quality_score: float = 0.8,
    repo: str = "pallets/flask",
    issue_number: int = 1,
) -> dict:
    """Create a mock EXTRACTED record.

    Args:
        quality_score: Quality score.
        repo: Repository name.
        issue_number: Issue number.

    Returns:
        dict: Mock record.
    """
    return {
        "id": str(uuid4()),
        "repo": repo,
        "issue_number": issue_number,
        "quality_score": quality_score,
        "extracted_error": "TypeError: test",
        "extracted_root_cause": "None check missing",
        "extracted_fix_summary": "Added guard clause",
        "extracted_fix_steps": ["Step 1"],
        "extracted_language": "python",
        "extracted_framework": "flask",
    }


class TestProcessExtractedIssues:
    """Tests for process_extracted_issues function."""

    async def test_submits_high_quality(
        self,
        mock_get_issues: AsyncMock,
        mock_submit: AsyncMock,
        mock_update_submitted: AsyncMock,
        mock_update_dropped: AsyncMock,
        mock_update_error: AsyncMock,
    ) -> None:
        """High-quality records are submitted."""
        from src.crawler.batch_submitter import process_extracted_issues

        issue_id = str(uuid4())
        mock_get_issues.return_value = [_make_extracted_record(quality_score=0.8)]
        mock_submit.return_value = SubmissionResult(
            success=True,
            issue_id=issue_id,
            issue_type="master_issue",
        )

        counts = await process_extracted_issues(quality_threshold=0.6)

        assert counts["submitted"] == 1
        assert counts["dropped"] == 0
        mock_submit.assert_called_once()
        mock_update_submitted.assert_called_once()

    async def test_drops_low_quality(
        self,
        mock_get_issues: AsyncMock,
        mock_submit: AsyncMock,
        mock_update_submitted: AsyncMock,
        mock_update_dropped: AsyncMock,
        mock_update_error: AsyncMock,
    ) -> None:
        """Low-quality records are dropped."""
        from src.crawler.batch_submitter import process_extracted_issues

        mock_get_issues.return_value = [_make_extracted_record(quality_score=0.3)]

        counts = await process_extracted_issues(quality_threshold=0.6)

        assert counts["dropped"] == 1
        assert counts["submitted"] == 0
        mock_submit.assert_not_called()
        mock_update_dropped.assert_called_once()

    async def test_dry_run_no_submit(
        self,
        mock_get_issues: AsyncMock,
        mock_submit: AsyncMock,
        mock_update_submitted: AsyncMock,
        mock_update_dropped: AsyncMock,
        mock_update_error: AsyncMock,
    ) -> None:
        """Dry run does not submit or update state."""
        from src.crawler.batch_submitter import process_extracted_issues

        mock_get_issues.return_value = [_make_extracted_record(quality_score=0.8)]

        counts = await process_extracted_issues(dry_run=True, quality_threshold=0.6)

        assert counts["submitted"] == 1
        mock_submit.assert_not_called()
        mock_update_submitted.assert_not_called()

    async def test_dry_run_does_not_drop(
        self,
        mock_get_issues: AsyncMock,
        mock_submit: AsyncMock,
        mock_update_submitted: AsyncMock,
        mock_update_dropped: AsyncMock,
        mock_update_error: AsyncMock,
    ) -> None:
        """Dry run does not update dropped state."""
        from src.crawler.batch_submitter import process_extracted_issues

        mock_get_issues.return_value = [_make_extracted_record(quality_score=0.3)]

        counts = await process_extracted_issues(dry_run=True, quality_threshold=0.6)

        assert counts["dropped"] == 1
        mock_update_dropped.assert_not_called()

    async def test_submission_error_handled(
        self,
        mock_get_issues: AsyncMock,
        mock_submit: AsyncMock,
        mock_update_submitted: AsyncMock,
        mock_update_dropped: AsyncMock,
        mock_update_error: AsyncMock,
    ) -> None:
        """Submission errors are handled gracefully."""
        from src.crawler.batch_submitter import process_extracted_issues

        mock_get_issues.return_value = [_make_extracted_record(quality_score=0.8)]
        mock_submit.return_value = SubmissionResult(
            success=False,
            error="Sanitization failed",
        )

        counts = await process_extracted_issues(quality_threshold=0.6)

        assert counts["errored"] == 1
        mock_update_error.assert_called_once()

    async def test_exception_during_submit_handled(
        self,
        mock_get_issues: AsyncMock,
        mock_submit: AsyncMock,
        mock_update_submitted: AsyncMock,
        mock_update_dropped: AsyncMock,
        mock_update_error: AsyncMock,
    ) -> None:
        """Exceptions during submission are caught."""
        from src.crawler.batch_submitter import process_extracted_issues

        mock_get_issues.return_value = [_make_extracted_record(quality_score=0.8)]
        mock_submit.side_effect = Exception("Unexpected error")

        counts = await process_extracted_issues(quality_threshold=0.6)

        assert counts["errored"] == 1
        mock_update_error.assert_called_once()

    async def test_empty_queue(
        self,
        mock_get_issues: AsyncMock,
        mock_submit: AsyncMock,
        mock_update_submitted: AsyncMock,
        mock_update_dropped: AsyncMock,
        mock_update_error: AsyncMock,
    ) -> None:
        """Empty queue returns zero counts."""
        from src.crawler.batch_submitter import process_extracted_issues

        mock_get_issues.return_value = []

        counts = await process_extracted_issues()

        assert counts["total"] == 0
        assert counts["submitted"] == 0

    async def test_mixed_quality_records(
        self,
        mock_get_issues: AsyncMock,
        mock_submit: AsyncMock,
        mock_update_submitted: AsyncMock,
        mock_update_dropped: AsyncMock,
        mock_update_error: AsyncMock,
    ) -> None:
        """Mix of high and low quality records is processed correctly."""
        from src.crawler.batch_submitter import process_extracted_issues

        issue_id = str(uuid4())
        mock_get_issues.return_value = [
            _make_extracted_record(quality_score=0.8, issue_number=1),
            _make_extracted_record(quality_score=0.3, issue_number=2),
            _make_extracted_record(quality_score=0.9, issue_number=3),
        ]
        mock_submit.return_value = SubmissionResult(
            success=True,
            issue_id=issue_id,
            issue_type="master_issue",
        )

        counts = await process_extracted_issues(quality_threshold=0.6)

        assert counts["submitted"] == 2
        assert counts["dropped"] == 1
        assert counts["total"] == 3
