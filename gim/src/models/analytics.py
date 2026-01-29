"""Pydantic models for usage analytics."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Type of usage event.

    Attributes:
        SEARCH: User searched for issues.
        FIX_RETRIEVED: Fix bundle was retrieved.
        FIX_APPLIED: Fix was applied by user.
        FIX_CONFIRMED: Fix success/failure was confirmed.
        ISSUE_SUBMITTED: New issue was submitted.
    """

    SEARCH = "search"
    FIX_RETRIEVED = "fix_retrieved"
    FIX_APPLIED = "fix_applied"
    FIX_CONFIRMED = "fix_confirmed"
    ISSUE_SUBMITTED = "issue_submitted"


class UsageEventCreate(BaseModel):
    """Model for creating a usage event.

    Attributes:
        event_type: Type of the event.
        issue_id: Related issue ID if applicable.
        model: Name of the AI model.
        provider: Provider of the AI model.
        metadata: Additional event metadata.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    event_type: EventType
    issue_id: Optional[UUID] = None
    model: Optional[str] = Field(None, max_length=100)
    provider: Optional[str] = Field(None, max_length=50)
    metadata: dict = Field(default_factory=dict)


class UsageEventResponse(UsageEventCreate):
    """Model for usage event API responses.

    Attributes:
        id: Unique identifier for the event.
        created_at: Timestamp when event was created.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class IssueUsageStats(BaseModel):
    """Usage statistics for a specific issue.

    Attributes:
        issue_id: ID of the issue.
        total_queries: Times this issue appeared in search results.
        total_fix_retrieved: Times fix bundle was fetched.
        total_fix_applied: Times fix was reported as applied.
        total_resolved: Times fix was confirmed successful.
        resolution_rate: Success rate (resolved / applied).
        last_queried_at: When issue was last searched.
        last_resolved_at: When issue was last resolved.
    """

    issue_id: UUID
    total_queries: int = Field(ge=0)
    total_fix_retrieved: int = Field(ge=0)
    total_fix_applied: int = Field(ge=0)
    total_resolved: int = Field(ge=0)
    resolution_rate: float = Field(ge=0.0, le=1.0)
    last_queried_at: Optional[datetime] = None
    last_resolved_at: Optional[datetime] = None


class GlobalUsageStats(BaseModel):
    """Global GIM usage statistics.

    Attributes:
        total_queries: All-time GIM search queries.
        total_issues_resolved: All-time successful fix confirmations.
        total_issues_submitted: All-time issues submitted by AI.
        queries_24h: Queries in last 24 hours.
        resolutions_24h: Resolutions in last 24 hours.
        top_queried_issues: IDs of most queried issues.
        top_resolved_issues: IDs of most resolved issues.
    """

    total_queries: int = Field(ge=0)
    total_issues_resolved: int = Field(ge=0)
    total_issues_submitted: int = Field(ge=0)
    queries_24h: int = Field(ge=0)
    resolutions_24h: int = Field(ge=0)
    top_queried_issues: List[UUID] = Field(default_factory=list)
    top_resolved_issues: List[UUID] = Field(default_factory=list)
