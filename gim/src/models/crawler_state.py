"""Pydantic models for GitHub issue crawler state management."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CrawlerStatus(str, Enum):
    """Pipeline status for a crawled issue.

    Attributes:
        PENDING: Issue discovered, awaiting fetch.
        FETCHED: Raw data fetched from GitHub.
        EXTRACTED: LLM extraction completed.
        SUBMITTED: Successfully submitted to GIM.
        DROPPED: Filtered out or below quality threshold.
        ERROR: Processing failed with error.
    """

    PENDING = "PENDING"
    FETCHED = "FETCHED"
    EXTRACTED = "EXTRACTED"
    SUBMITTED = "SUBMITTED"
    DROPPED = "DROPPED"
    ERROR = "ERROR"


class DropReason(str, Enum):
    """Reason a crawled issue was dropped from the pipeline.

    Attributes:
        NOT_A_FIX: Issue does not represent a bug fix.
        NO_ERROR_MESSAGE: No error pattern found in issue body.
        EXTRACTION_FAILED: LLM extraction returned invalid results.
        LOW_QUALITY: Quality score below submission threshold.
        SANITIZATION_FAILED: Content sanitization failed.
    """

    NOT_A_FIX = "NOT_A_FIX"
    NO_ERROR_MESSAGE = "NO_ERROR_MESSAGE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    LOW_QUALITY = "LOW_QUALITY"
    SANITIZATION_FAILED = "SANITIZATION_FAILED"


class CrawlerStateCreate(BaseModel):
    """Model for creating a new crawler state record (discovery phase).

    Attributes:
        repo: GitHub repository in 'owner/name' format.
        issue_number: GitHub issue number.
        github_issue_id: GitHub's unique issue ID.
        closed_at: When the issue was closed.
        state_reason: GitHub's state_reason (e.g. 'completed').
        issue_title: Title of the GitHub issue.
        issue_labels: List of label names on the issue.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    repo: str = Field(
        ...,
        pattern=r"^[\w.\-]+/[\w.\-]+$",
        description="GitHub repository in 'owner/name' format",
    )
    issue_number: int = Field(..., gt=0, description="GitHub issue number")
    github_issue_id: int = Field(..., gt=0, description="GitHub unique issue ID")
    closed_at: Optional[datetime] = Field(None, description="When the issue was closed")
    state_reason: Optional[str] = Field(None, description="GitHub state_reason")
    issue_title: str = Field(..., min_length=1, description="Issue title")
    issue_labels: List[str] = Field(default_factory=list, description="Label names")


class CrawlerStateFetched(BaseModel):
    """Model for updating a crawler record after fetching details.

    Attributes:
        has_merged_pr: Whether the issue has a linked merged PR.
        pr_number: PR number if linked.
        raw_issue_body: Full issue body text.
        raw_comments: List of comment dicts.
        raw_pr_body: PR body text.
        raw_pr_diff_summary: Summary of PR diff (files, additions, deletions).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    has_merged_pr: bool = Field(default=False, description="Has linked merged PR")
    pr_number: Optional[int] = Field(None, gt=0, description="Linked PR number")
    raw_issue_body: Optional[str] = Field(None, description="Issue body text")
    raw_comments: List[dict] = Field(default_factory=list, description="Issue comments")
    raw_pr_body: Optional[str] = Field(None, description="PR body text")
    raw_pr_diff_summary: Optional[str] = Field(None, description="PR diff summary")


class CrawlerStateExtracted(BaseModel):
    """Model for updating a crawler record after LLM extraction.

    Attributes:
        extracted_error: Extracted error message.
        extracted_root_cause: Extracted root cause.
        extracted_fix_summary: Extracted fix summary.
        extracted_fix_steps: List of fix step strings.
        extracted_language: Detected programming language.
        extracted_framework: Detected framework.
        extraction_confidence: LLM confidence in extraction (0-1).
        quality_score: Global usefulness score (0-1).
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    extracted_error: str = Field(..., min_length=1, description="Extracted error message")
    extracted_root_cause: str = Field(..., min_length=1, description="Extracted root cause")
    extracted_fix_summary: str = Field(..., min_length=1, description="Extracted fix summary")
    extracted_fix_steps: List[str] = Field(
        ..., min_length=1, description="List of fix steps"
    )
    extracted_language: Optional[str] = Field(None, description="Programming language")
    extracted_framework: Optional[str] = Field(None, description="Framework name")
    extraction_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Extraction confidence"
    )
    quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Global usefulness score"
    )

    @field_validator("extracted_fix_steps")
    @classmethod
    def validate_fix_steps_not_empty(cls, v: List[str]) -> List[str]:
        """Ensure fix_steps contains at least one non-empty step.

        Args:
            v: List of fix step strings.

        Returns:
            List[str]: Validated fix steps.

        Raises:
            ValueError: If all steps are empty.
        """
        if not any(step.strip() for step in v):
            raise ValueError("fix_steps must contain at least one non-empty step")
        return v


class CrawlerStateResponse(BaseModel):
    """Full crawler state record as returned from the database.

    Attributes:
        id: Unique record identifier.
        repo: GitHub repository.
        issue_number: GitHub issue number.
        github_issue_id: GitHub unique issue ID.
        status: Pipeline status.
        drop_reason: Why the issue was dropped (if applicable).
        closed_at: When the issue was closed.
        state_reason: GitHub state_reason.
        has_merged_pr: Whether linked PR was merged.
        pr_number: Linked PR number.
        issue_title: Issue title.
        issue_labels: Label names.
        raw_issue_body: Issue body text.
        raw_comments: Issue comments.
        raw_pr_body: PR body text.
        raw_pr_diff_summary: PR diff summary.
        extracted_error: Extracted error message.
        extracted_root_cause: Extracted root cause.
        extracted_fix_summary: Extracted fix summary.
        extracted_fix_steps: Extracted fix steps.
        extracted_language: Detected language.
        extracted_framework: Detected framework.
        extraction_confidence: Extraction confidence score.
        quality_score: Global usefulness score.
        gim_issue_id: GIM master/child issue ID after submission.
        last_error: Last error message if status is ERROR.
        retry_count: Number of retry attempts.
        created_at: Record creation timestamp.
        updated_at: Record last update timestamp.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    repo: str
    issue_number: int
    github_issue_id: Optional[int] = None
    status: CrawlerStatus
    drop_reason: Optional[str] = None
    closed_at: Optional[datetime] = None
    state_reason: Optional[str] = None
    has_merged_pr: bool = False
    pr_number: Optional[int] = None
    issue_title: Optional[str] = None
    issue_labels: List[str] = Field(default_factory=list)
    raw_issue_body: Optional[str] = None
    raw_comments: List[dict] = Field(default_factory=list)
    raw_pr_body: Optional[str] = None
    raw_pr_diff_summary: Optional[str] = None
    extracted_error: Optional[str] = None
    extracted_root_cause: Optional[str] = None
    extracted_fix_summary: Optional[str] = None
    extracted_fix_steps: Optional[List[str]] = None
    extracted_language: Optional[str] = None
    extracted_framework: Optional[str] = None
    extraction_confidence: Optional[float] = None
    quality_score: Optional[float] = None
    gim_issue_id: Optional[UUID] = None
    last_error: Optional[str] = None
    retry_count: int = 0
    created_at: datetime
    updated_at: datetime
