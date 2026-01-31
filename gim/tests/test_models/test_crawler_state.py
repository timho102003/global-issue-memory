"""Tests for crawler state Pydantic models."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.crawler_state import (
    CrawlerStateCreate,
    CrawlerStateExtracted,
    CrawlerStateFetched,
    CrawlerStateResponse,
    CrawlerStatus,
    DropReason,
)


class TestCrawlerStatus:
    """Tests for CrawlerStatus enum."""

    def test_all_values_present(self) -> None:
        """All pipeline statuses are defined."""
        assert CrawlerStatus.PENDING == "PENDING"
        assert CrawlerStatus.FETCHED == "FETCHED"
        assert CrawlerStatus.EXTRACTED == "EXTRACTED"
        assert CrawlerStatus.SUBMITTED == "SUBMITTED"
        assert CrawlerStatus.DROPPED == "DROPPED"
        assert CrawlerStatus.ERROR == "ERROR"

    def test_status_count(self) -> None:
        """Exactly 6 statuses are defined."""
        assert len(CrawlerStatus) == 6


class TestDropReason:
    """Tests for DropReason enum."""

    def test_all_values_present(self) -> None:
        """All drop reasons are defined."""
        assert DropReason.NOT_A_FIX == "NOT_A_FIX"
        assert DropReason.NO_ERROR_MESSAGE == "NO_ERROR_MESSAGE"
        assert DropReason.EXTRACTION_FAILED == "EXTRACTION_FAILED"
        assert DropReason.LOW_QUALITY == "LOW_QUALITY"
        assert DropReason.SANITIZATION_FAILED == "SANITIZATION_FAILED"


class TestCrawlerStateCreate:
    """Tests for CrawlerStateCreate model."""

    def test_valid_creation(self) -> None:
        """Valid data creates model successfully."""
        state = CrawlerStateCreate(
            repo="pallets/flask",
            issue_number=123,
            github_issue_id=456789,
            closed_at=datetime.now(timezone.utc),
            state_reason="completed",
            issue_title="Fix TypeError in request handling",
            issue_labels=["bug", "fix"],
        )
        assert state.repo == "pallets/flask"
        assert state.issue_number == 123
        assert state.github_issue_id == 456789

    def test_valid_repo_with_dots(self) -> None:
        """Repo name with dots is accepted."""
        state = CrawlerStateCreate(
            repo="org.name/repo.name",
            issue_number=1,
            github_issue_id=1,
            issue_title="Test",
        )
        assert state.repo == "org.name/repo.name"

    def test_valid_repo_with_hyphens(self) -> None:
        """Repo name with hyphens is accepted."""
        state = CrawlerStateCreate(
            repo="langchain-ai/langchain",
            issue_number=1,
            github_issue_id=1,
            issue_title="Test",
        )
        assert state.repo == "langchain-ai/langchain"

    def test_invalid_repo_format_no_slash(self) -> None:
        """Repo without slash is rejected."""
        with pytest.raises(ValidationError):
            CrawlerStateCreate(
                repo="flask",
                issue_number=1,
                github_issue_id=1,
                issue_title="Test",
            )

    def test_invalid_repo_format_spaces(self) -> None:
        """Repo with spaces is rejected."""
        with pytest.raises(ValidationError):
            CrawlerStateCreate(
                repo="pallets /flask",
                issue_number=1,
                github_issue_id=1,
                issue_title="Test",
            )

    def test_issue_number_must_be_positive(self) -> None:
        """Issue number must be > 0."""
        with pytest.raises(ValidationError):
            CrawlerStateCreate(
                repo="pallets/flask",
                issue_number=0,
                github_issue_id=1,
                issue_title="Test",
            )

    def test_issue_title_required(self) -> None:
        """Issue title cannot be empty."""
        with pytest.raises(ValidationError):
            CrawlerStateCreate(
                repo="pallets/flask",
                issue_number=1,
                github_issue_id=1,
                issue_title="",
            )

    def test_labels_default_empty(self) -> None:
        """Labels default to empty list."""
        state = CrawlerStateCreate(
            repo="pallets/flask",
            issue_number=1,
            github_issue_id=1,
            issue_title="Test",
        )
        assert state.issue_labels == []

    def test_optional_fields_default_none(self) -> None:
        """Optional fields default to None."""
        state = CrawlerStateCreate(
            repo="pallets/flask",
            issue_number=1,
            github_issue_id=1,
            issue_title="Test",
        )
        assert state.closed_at is None
        assert state.state_reason is None


class TestCrawlerStateFetched:
    """Tests for CrawlerStateFetched model."""

    def test_valid_fetched_data(self) -> None:
        """Valid fetched data creates model successfully."""
        fetched = CrawlerStateFetched(
            has_merged_pr=True,
            pr_number=42,
            raw_issue_body="Some issue body",
            raw_comments=[{"author": "user", "body": "comment"}],
            raw_pr_body="PR description",
            raw_pr_diff_summary="Total: +10/-5 in 2 files",
        )
        assert fetched.has_merged_pr is True
        assert fetched.pr_number == 42

    def test_defaults(self) -> None:
        """Default values are correct."""
        fetched = CrawlerStateFetched()
        assert fetched.has_merged_pr is False
        assert fetched.pr_number is None
        assert fetched.raw_issue_body is None
        assert fetched.raw_comments == []

    def test_pr_number_must_be_positive(self) -> None:
        """PR number must be > 0 when provided."""
        with pytest.raises(ValidationError):
            CrawlerStateFetched(pr_number=0)


class TestCrawlerStateExtracted:
    """Tests for CrawlerStateExtracted model."""

    def test_valid_extraction(self) -> None:
        """Valid extracted data creates model successfully."""
        extracted = CrawlerStateExtracted(
            extracted_error="TypeError: 'NoneType' has no attribute 'get'",
            extracted_root_cause="Variable not initialized before use",
            extracted_fix_summary="Add None check before accessing attribute",
            extracted_fix_steps=["Add guard clause", "Test with None input"],
            extracted_language="python",
            extracted_framework="flask",
            extraction_confidence=0.85,
            quality_score=0.7,
        )
        assert extracted.extraction_confidence == 0.85
        assert extracted.quality_score == 0.7

    def test_confidence_out_of_range_high(self) -> None:
        """Confidence > 1.0 is rejected."""
        with pytest.raises(ValidationError):
            CrawlerStateExtracted(
                extracted_error="Error",
                extracted_root_cause="Cause",
                extracted_fix_summary="Fix",
                extracted_fix_steps=["Step 1"],
                extraction_confidence=1.5,
                quality_score=0.5,
            )

    def test_confidence_out_of_range_low(self) -> None:
        """Confidence < 0.0 is rejected."""
        with pytest.raises(ValidationError):
            CrawlerStateExtracted(
                extracted_error="Error",
                extracted_root_cause="Cause",
                extracted_fix_summary="Fix",
                extracted_fix_steps=["Step 1"],
                extraction_confidence=-0.1,
                quality_score=0.5,
            )

    def test_quality_score_bounds(self) -> None:
        """Quality score must be 0.0-1.0."""
        with pytest.raises(ValidationError):
            CrawlerStateExtracted(
                extracted_error="Error",
                extracted_root_cause="Cause",
                extracted_fix_summary="Fix",
                extracted_fix_steps=["Step 1"],
                extraction_confidence=0.5,
                quality_score=1.1,
            )

    def test_empty_fix_steps_rejected(self) -> None:
        """Empty fix_steps list is rejected."""
        with pytest.raises(ValidationError):
            CrawlerStateExtracted(
                extracted_error="Error",
                extracted_root_cause="Cause",
                extracted_fix_summary="Fix",
                extracted_fix_steps=[],
                extraction_confidence=0.5,
                quality_score=0.5,
            )

    def test_whitespace_only_fix_steps_rejected(self) -> None:
        """Fix steps with only whitespace are rejected."""
        with pytest.raises(ValidationError):
            CrawlerStateExtracted(
                extracted_error="Error",
                extracted_root_cause="Cause",
                extracted_fix_summary="Fix",
                extracted_fix_steps=["  ", ""],
                extraction_confidence=0.5,
                quality_score=0.5,
            )

    def test_empty_error_rejected(self) -> None:
        """Empty extracted_error is rejected."""
        with pytest.raises(ValidationError):
            CrawlerStateExtracted(
                extracted_error="",
                extracted_root_cause="Cause",
                extracted_fix_summary="Fix",
                extracted_fix_steps=["Step"],
                extraction_confidence=0.5,
                quality_score=0.5,
            )


class TestCrawlerStateResponse:
    """Tests for CrawlerStateResponse model."""

    def test_full_response(self) -> None:
        """Full response model with all fields."""
        now = datetime.now(timezone.utc)
        response = CrawlerStateResponse(
            id=uuid4(),
            repo="pallets/flask",
            issue_number=123,
            github_issue_id=456789,
            status=CrawlerStatus.SUBMITTED,
            closed_at=now,
            state_reason="completed",
            has_merged_pr=True,
            pr_number=42,
            issue_title="Fix TypeError",
            issue_labels=["bug"],
            extracted_error="TypeError",
            extracted_root_cause="None check missing",
            extracted_fix_summary="Added guard clause",
            extracted_fix_steps=["Step 1"],
            extracted_language="python",
            extracted_framework="flask",
            extraction_confidence=0.9,
            quality_score=0.8,
            gim_issue_id=uuid4(),
            retry_count=0,
            created_at=now,
            updated_at=now,
        )
        assert response.status == CrawlerStatus.SUBMITTED
        assert response.has_merged_pr is True

    def test_minimal_response(self) -> None:
        """Minimal response with only required fields."""
        now = datetime.now(timezone.utc)
        response = CrawlerStateResponse(
            id=uuid4(),
            repo="pallets/flask",
            issue_number=1,
            status=CrawlerStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        assert response.status == CrawlerStatus.PENDING
        assert response.drop_reason is None
        assert response.gim_issue_id is None
