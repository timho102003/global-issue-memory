"""Tests for the GitHub fetcher module.

Mocks PyGitHub to test discovery and fetch logic.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.crawler.github_fetcher import (
    _get_pr_diff_summary,
    _rate_limit_guard,
    discover_issues,
    fetch_issue_details,
)


@pytest.fixture
def mock_github():
    """Mock PyGitHub client.

    Yields:
        MagicMock: Mock GitHub client.
    """
    with patch("src.crawler.github_fetcher._get_github_client") as mock:
        gh = MagicMock()
        # Set up rate limit to be safe
        rate_limit = MagicMock()
        rate_limit.rate.remaining = 5000
        rate_limit.rate.reset = datetime(2030, 1, 1, tzinfo=timezone.utc)
        gh.get_rate_limit.return_value = rate_limit
        mock.return_value = gh
        yield gh


def _make_issue(
    number: int = 1,
    issue_id: int = 100,
    state_reason: str = "completed",
    title: str = "Fix bug",
    labels: list = None,
    closed_at: datetime = None,
    is_pr: bool = False,
    body: str = "Issue body",
) -> MagicMock:
    """Create a mock GitHub issue.

    Args:
        number: Issue number.
        issue_id: GitHub issue ID.
        state_reason: GitHub state_reason.
        title: Issue title.
        labels: List of label names.
        closed_at: When the issue was closed.
        is_pr: Whether this is a pull request.
        body: Issue body text.

    Returns:
        MagicMock: Mock issue object.
    """
    issue = MagicMock()
    issue.number = number
    issue.id = issue_id
    issue.state_reason = state_reason
    issue.title = title
    issue.body = body
    issue.closed_at = closed_at or datetime(2024, 6, 1, tzinfo=timezone.utc)

    if labels:
        mock_labels = []
        for label_name in labels:
            mock_label = MagicMock()
            mock_label.name = label_name
            mock_labels.append(mock_label)
        issue.labels = mock_labels
    else:
        issue.labels = []

    if is_pr:
        issue.pull_request = MagicMock()
    else:
        issue.pull_request = None

    return issue


class TestDiscoverIssues:
    """Tests for discover_issues function."""

    async def test_discovers_completed_issues(self, mock_github: MagicMock) -> None:
        """Completed issues are discovered."""
        issues = [
            _make_issue(number=1, state_reason="completed"),
            _make_issue(number=2, state_reason="not_planned"),
            _make_issue(number=3, state_reason="completed"),
        ]
        mock_github.get_repo.return_value.get_issues.return_value = issues

        results = await discover_issues("pallets/flask", max_issues=10)

        # Only completed issues are returned
        assert len(results) == 2
        assert results[0]["issue_number"] == 1
        assert results[1]["issue_number"] == 3

    async def test_skips_pull_requests(self, mock_github: MagicMock) -> None:
        """Pull requests in issue list are skipped."""
        issues = [
            _make_issue(number=1, is_pr=True, state_reason="completed"),
            _make_issue(number=2, is_pr=False, state_reason="completed"),
        ]
        mock_github.get_repo.return_value.get_issues.return_value = issues

        results = await discover_issues("pallets/flask", max_issues=10)

        assert len(results) == 1
        assert results[0]["issue_number"] == 2

    async def test_respects_max_issues(self, mock_github: MagicMock) -> None:
        """Max issues limit is respected."""
        issues = [
            _make_issue(number=i, state_reason="completed")
            for i in range(1, 20)
        ]
        mock_github.get_repo.return_value.get_issues.return_value = issues

        results = await discover_issues("pallets/flask", max_issues=5)

        assert len(results) == 5

    async def test_since_filter(self, mock_github: MagicMock) -> None:
        """Issues before since date are excluded."""
        old_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        new_date = datetime(2024, 6, 1, tzinfo=timezone.utc)

        issues = [
            _make_issue(number=1, closed_at=new_date, state_reason="completed"),
            _make_issue(number=2, closed_at=old_date, state_reason="completed"),
        ]
        mock_github.get_repo.return_value.get_issues.return_value = issues

        since = datetime(2024, 3, 1, tzinfo=timezone.utc)
        results = await discover_issues("pallets/flask", since=since, max_issues=10)

        # First issue passes, second triggers early stop
        assert len(results) == 1
        assert results[0]["issue_number"] == 1

    async def test_extracts_labels(self, mock_github: MagicMock) -> None:
        """Issue labels are extracted."""
        issues = [
            _make_issue(number=1, labels=["bug", "p1"], state_reason="completed"),
        ]
        mock_github.get_repo.return_value.get_issues.return_value = issues

        results = await discover_issues("pallets/flask", max_issues=10)

        assert results[0]["issue_labels"] == ["bug", "p1"]

    async def test_returns_metadata(self, mock_github: MagicMock) -> None:
        """All expected metadata fields are returned."""
        issues = [
            _make_issue(
                number=42,
                issue_id=12345,
                title="Fix the thing",
                state_reason="completed",
            ),
        ]
        mock_github.get_repo.return_value.get_issues.return_value = issues

        results = await discover_issues("pallets/flask", max_issues=10)

        result = results[0]
        assert result["repo"] == "pallets/flask"
        assert result["issue_number"] == 42
        assert result["github_issue_id"] == 12345
        assert result["issue_title"] == "Fix the thing"
        assert result["state_reason"] == "completed"
        assert "closed_at" in result


class TestFetchIssueDetails:
    """Tests for fetch_issue_details function."""

    async def test_fetches_basic_details(self, mock_github: MagicMock) -> None:
        """Basic issue details are fetched."""
        issue = _make_issue(number=1)
        issue.get_comments.return_value = []
        issue.get_timeline.return_value = []

        mock_github.get_repo.return_value.get_issue.return_value = issue

        result = await fetch_issue_details("pallets/flask", 1)

        assert result["raw_issue_body"] == "Issue body"
        assert result["raw_comments"] == []
        assert result["has_merged_pr"] is False

    async def test_fetches_comments(self, mock_github: MagicMock) -> None:
        """Issue comments are fetched."""
        issue = _make_issue(number=1)

        comment = MagicMock()
        comment.user.login = "testuser"
        comment.body = "This is a comment"
        comment.created_at = datetime(2024, 6, 1, tzinfo=timezone.utc)
        issue.get_comments.return_value = [comment]
        issue.get_timeline.return_value = []

        mock_github.get_repo.return_value.get_issue.return_value = issue

        result = await fetch_issue_details("pallets/flask", 1)

        assert len(result["raw_comments"]) == 1
        assert result["raw_comments"][0]["author"] == "testuser"
        assert result["raw_comments"][0]["body"] == "This is a comment"


class TestGetPrDiffSummary:
    """Tests for _get_pr_diff_summary function."""

    def test_summarizes_pr_files(self) -> None:
        """PR files are summarized correctly."""
        pr = MagicMock()
        file1 = MagicMock()
        file1.filename = "app.py"
        file1.additions = 10
        file1.deletions = 5
        file2 = MagicMock()
        file2.filename = "test_app.py"
        file2.additions = 20
        file2.deletions = 0
        pr.get_files.return_value = [file1, file2]

        summary = _get_pr_diff_summary(pr)

        assert "Total: +30/-5 in 2 files" in summary
        assert "app.py (+10/-5)" in summary
        assert "test_app.py (+20/-0)" in summary

    def test_handles_error(self) -> None:
        """Error during diff summary returns empty string."""
        pr = MagicMock()
        pr.get_files.side_effect = Exception("API error")

        summary = _get_pr_diff_summary(pr)
        assert summary == ""


class TestRateLimitGuard:
    """Tests for _rate_limit_guard function."""

    def test_does_not_sleep_when_remaining_high(self) -> None:
        """No sleep when rate limit is fine."""
        gh = MagicMock()
        rate_limit = MagicMock()
        rate_limit.rate.remaining = 5000
        rate_limit.rate.reset = datetime(2030, 1, 1, tzinfo=timezone.utc)
        gh.get_rate_limit.return_value = rate_limit

        # Should not raise or sleep
        _rate_limit_guard(gh)

    @patch("src.crawler.github_fetcher.time.sleep")
    def test_sleeps_when_remaining_low(self, mock_sleep: MagicMock) -> None:
        """Sleeps when rate limit is low."""
        gh = MagicMock()
        rate_limit = MagicMock()
        rate_limit.rate.remaining = 50  # Below threshold
        rate_limit.rate.reset = datetime(2030, 1, 1, tzinfo=timezone.utc)
        gh.get_rate_limit.return_value = rate_limit

        _rate_limit_guard(gh)

        mock_sleep.assert_called_once()
