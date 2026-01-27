"""Tests for analytics models."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.analytics import (
    EventType,
    GlobalUsageStats,
    IssueUsageStats,
    UsageEventCreate,
    UsageEventResponse,
)


class TestEventType:
    """Tests for EventType enum."""

    def test_all_event_types(self) -> None:
        """Test all event types have correct values."""
        assert EventType.SEARCH.value == "search"
        assert EventType.FIX_RETRIEVED.value == "fix_retrieved"
        assert EventType.FIX_APPLIED.value == "fix_applied"
        assert EventType.FIX_CONFIRMED.value == "fix_confirmed"
        assert EventType.ISSUE_SUBMITTED.value == "issue_submitted"


class TestUsageEventCreate:
    """Tests for UsageEventCreate model."""

    def test_valid_usage_event(self) -> None:
        """Test creating a valid usage event."""
        event = UsageEventCreate(
            event_type=EventType.SEARCH,
            session_id="session-123",
            model_name="claude-3-opus",
            model_provider="anthropic",
        )
        assert event.event_type == EventType.SEARCH
        assert event.session_id == "session-123"

    def test_with_issue_id(self) -> None:
        """Test usage event with issue ID."""
        issue_id = uuid4()
        event = UsageEventCreate(
            event_type=EventType.FIX_RETRIEVED,
            issue_id=issue_id,
            session_id="session-456",
        )
        assert event.issue_id == issue_id

    def test_session_id_required(self) -> None:
        """Test that session_id is required."""
        with pytest.raises(ValidationError):
            UsageEventCreate(
                event_type=EventType.SEARCH,
            )

    def test_session_id_min_length(self) -> None:
        """Test that session_id must have minimum length."""
        with pytest.raises(ValidationError):
            UsageEventCreate(
                event_type=EventType.SEARCH,
                session_id="",
            )

    def test_optional_fields(self) -> None:
        """Test that optional fields default correctly."""
        event = UsageEventCreate(
            event_type=EventType.ISSUE_SUBMITTED,
            session_id="session-789",
        )
        assert event.issue_id is None
        assert event.model_name is None
        assert event.model_provider is None
        assert event.success is None
        assert event.metadata == {}

    def test_with_success_flag(self) -> None:
        """Test usage event with success flag."""
        event = UsageEventCreate(
            event_type=EventType.FIX_CONFIRMED,
            session_id="session-abc",
            success=True,
        )
        assert event.success is True

    def test_with_metadata(self) -> None:
        """Test usage event with metadata."""
        event = UsageEventCreate(
            event_type=EventType.SEARCH,
            session_id="session-def",
            metadata={"query_length": 150, "filters_used": ["model", "provider"]},
        )
        assert event.metadata["query_length"] == 150


class TestUsageEventResponse:
    """Tests for UsageEventResponse model."""

    def test_valid_response(self) -> None:
        """Test creating a valid usage event response."""
        response = UsageEventResponse(
            id=uuid4(),
            event_type=EventType.SEARCH,
            session_id="session-123",
            created_at=datetime.now(),
        )
        assert response.event_type == EventType.SEARCH


class TestIssueUsageStats:
    """Tests for IssueUsageStats model."""

    def test_valid_issue_stats(self) -> None:
        """Test creating valid issue usage stats."""
        stats = IssueUsageStats(
            issue_id=uuid4(),
            total_queries=100,
            total_fix_retrieved=80,
            total_fix_applied=60,
            total_resolved=45,
            resolution_rate=0.75,
        )
        assert stats.total_queries == 100
        assert stats.resolution_rate == 0.75

    def test_counts_must_be_non_negative(self) -> None:
        """Test that counts must be >= 0."""
        with pytest.raises(ValidationError):
            IssueUsageStats(
                issue_id=uuid4(),
                total_queries=-1,
                total_fix_retrieved=0,
                total_fix_applied=0,
                total_resolved=0,
                resolution_rate=0.0,
            )

    def test_resolution_rate_bounds(self) -> None:
        """Test that resolution_rate must be between 0 and 1."""
        with pytest.raises(ValidationError):
            IssueUsageStats(
                issue_id=uuid4(),
                total_queries=100,
                total_fix_retrieved=80,
                total_fix_applied=60,
                total_resolved=45,
                resolution_rate=1.5,
            )

    def test_optional_timestamps(self) -> None:
        """Test that timestamps are optional."""
        stats = IssueUsageStats(
            issue_id=uuid4(),
            total_queries=10,
            total_fix_retrieved=5,
            total_fix_applied=3,
            total_resolved=2,
            resolution_rate=0.67,
        )
        assert stats.last_queried_at is None
        assert stats.last_resolved_at is None


class TestGlobalUsageStats:
    """Tests for GlobalUsageStats model."""

    def test_valid_global_stats(self) -> None:
        """Test creating valid global usage stats."""
        stats = GlobalUsageStats(
            total_queries=10000,
            total_issues_resolved=5000,
            total_issues_submitted=1000,
            active_sessions_24h=500,
            queries_24h=2000,
            resolutions_24h=1000,
        )
        assert stats.total_queries == 10000
        assert stats.active_sessions_24h == 500

    def test_with_top_issues(self) -> None:
        """Test global stats with top issues."""
        issue_ids = [uuid4() for _ in range(5)]
        stats = GlobalUsageStats(
            total_queries=10000,
            total_issues_resolved=5000,
            total_issues_submitted=1000,
            active_sessions_24h=500,
            queries_24h=2000,
            resolutions_24h=1000,
            top_queried_issues=issue_ids[:3],
            top_resolved_issues=issue_ids[2:],
        )
        assert len(stats.top_queried_issues) == 3
        assert len(stats.top_resolved_issues) == 3

    def test_counts_must_be_non_negative(self) -> None:
        """Test that counts must be >= 0."""
        with pytest.raises(ValidationError):
            GlobalUsageStats(
                total_queries=-1,
                total_issues_resolved=0,
                total_issues_submitted=0,
                active_sessions_24h=0,
                queries_24h=0,
                resolutions_24h=0,
            )

    def test_default_empty_lists(self) -> None:
        """Test that top issues default to empty lists."""
        stats = GlobalUsageStats(
            total_queries=100,
            total_issues_resolved=50,
            total_issues_submitted=10,
            active_sessions_24h=5,
            queries_24h=20,
            resolutions_24h=10,
        )
        assert stats.top_queried_issues == []
        assert stats.top_resolved_issues == []
