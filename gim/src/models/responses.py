"""Pydantic models for MCP tool responses."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .analytics import IssueUsageStats
from .fix_bundle import FixBundleResponse
from .issue import MasterIssueResponse


class SearchResult(BaseModel):
    """Single search result with relevance score.

    Attributes:
        issue: The matching master issue.
        relevance_score: How relevant the match is (0.0 to 1.0).
        match_type: Type of match (exact, semantic, partial).
        usage_stats: Optional usage statistics for the issue.
    """

    issue: MasterIssueResponse
    relevance_score: float = Field(ge=0.0, le=1.0)
    match_type: str = Field(description="Type of match: 'exact', 'semantic', 'partial'")
    usage_stats: Optional[IssueUsageStats] = None


class SearchIssuesResponse(BaseModel):
    """Response model for gim_search_issues tool.

    Attributes:
        results: List of search results.
        total_found: Total number of matching issues.
        query_id: Unique ID for this query (for analytics).
    """

    results: List[SearchResult]
    total_found: int = Field(ge=0)
    query_id: str = Field(description="Unique ID for this query (for analytics)")


class GetFixBundleResponse(BaseModel):
    """Response model for gim_get_fix_bundle tool.

    Attributes:
        issue_id: ID of the master issue.
        issue_title: Title of the issue.
        fix_bundle: The fix bundle data.
        confidence_score: Trust score of the fix.
        verification_count: Number of successful verifications.
    """

    issue_id: UUID
    issue_title: str
    fix_bundle: FixBundleResponse
    confidence_score: float = Field(ge=0.0, le=1.0)
    verification_count: int = Field(ge=0)


class SubmitIssueResponse(BaseModel):
    """Response model for gim_submit_issue tool.

    Attributes:
        success: Whether submission was successful.
        issue_id: ID of created or merged issue.
        action: Action taken (created_new or merged_to_existing).
        merged_to_id: ID of existing issue if merged.
        sanitization_warnings: Warnings from sanitization.
        message: Human-readable result message.
    """

    success: bool
    issue_id: Optional[UUID] = None
    action: str = Field(description="'created_new' or 'merged_to_existing'")
    merged_to_id: Optional[UUID] = None
    sanitization_warnings: List[str] = Field(default_factory=list)
    message: str


class ConfirmFixResponse(BaseModel):
    """Response model for gim_confirm_fix tool.

    Attributes:
        success: Whether confirmation was recorded.
        issue_id: ID of the issue.
        new_confidence_score: Updated confidence score.
        verification_count: Updated verification count.
        message: Human-readable result message.
    """

    success: bool
    issue_id: UUID
    new_confidence_score: float = Field(ge=0.0, le=1.0)
    verification_count: int = Field(ge=0)
    message: str
