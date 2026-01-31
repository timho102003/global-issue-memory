"""Pydantic models for Master and Child issues."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IssueStatus(str, Enum):
    """Status of a master issue.

    Attributes:
        ACTIVE: Issue is currently active and valid.
        SUPERSEDED: Issue has been replaced by a newer issue.
        INVALID: Issue has been marked as invalid.
    """

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    INVALID = "invalid"


class ContributionType(str, Enum):
    """Type of contribution a child issue makes.

    Attributes:
        ENVIRONMENT: Adds new environment information.
        SYMPTOM: Adds new symptoms or error variations.
        MODEL_QUIRK: Documents model-specific behavior.
        VALIDATION: Confirms or validates the fix.
    """

    ENVIRONMENT = "environment"
    SYMPTOM = "symptom"
    MODEL_QUIRK = "model_quirk"
    VALIDATION = "validation"


class RootCauseCategory(str, Enum):
    """Root cause classification categories.

    Attributes:
        ENVIRONMENT: Environment-related issues (dependencies, config).
        MODEL_BEHAVIOR: AI model behavior issues (tool calling, schema).
        API_INTEGRATION: API/integration issues (auth, network).
        CODE_GENERATION: Code generation issues (syntax, types).
        FRAMEWORK_SPECIFIC: Framework-specific issues.
    """

    ENVIRONMENT = "environment"
    MODEL_BEHAVIOR = "model_behavior"
    API_INTEGRATION = "api_integration"
    CODE_GENERATION = "code_generation"
    FRAMEWORK_SPECIFIC = "framework_specific"


class MasterIssueBase(BaseModel):
    """Base model for master issue data.

    Attributes:
        canonical_title: Searchable title for the issue.
        description: Detailed description of the issue.
        root_cause_category: Primary root cause classification.
        root_cause_subcategory: Specific subcategory within root cause.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    canonical_title: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Canonical, searchable title for the issue",
    )
    description: str = Field(
        ...,
        min_length=20,
        description="Detailed description of the issue",
    )
    root_cause_category: RootCauseCategory = Field(
        ...,
        description="Primary root cause classification",
    )
    root_cause_subcategory: Optional[str] = Field(
        None,
        max_length=100,
        description="Specific subcategory within root cause",
    )


class MasterIssueCreate(MasterIssueBase):
    """Model for creating a new master issue.

    Inherits all fields from MasterIssueBase.
    """

    pass


class MasterIssueResponse(MasterIssueBase):
    """Model for master issue API responses.

    Attributes:
        id: Unique identifier for the issue.
        confidence_score: Trust score between 0.0 and 1.0.
        child_issue_count: Number of child issues.
        environment_coverage: List of environments where fix is confirmed.
        verification_count: Number of successful fix verifications.
        last_confirmed_at: Timestamp of last successful confirmation.
        status: Current status of the issue.
        created_at: Timestamp when issue was created.
        updated_at: Timestamp when issue was last updated.
        source: Origin of the issue ('mcp_tool' or 'github_crawler').
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    confidence_score: float = Field(ge=0.0, le=1.0)
    child_issue_count: int = Field(ge=0)
    environment_coverage: List[str] = Field(default_factory=list)
    verification_count: int = Field(ge=0)
    last_confirmed_at: Optional[datetime] = None
    status: IssueStatus
    created_at: datetime
    updated_at: datetime
    source: Optional[str] = None


class ChildIssueCreate(BaseModel):
    """Model for creating a child issue contribution.

    Attributes:
        master_issue_id: ID of the parent master issue.
        contribution_type: Type of contribution being made.
        sanitized_error: Sanitized error message.
        sanitized_context: Sanitized context around the error.
        sanitized_mre: Sanitized minimal reproducible example.
        environment: Environment information as dict.
        model_provider: Provider of the AI model.
        model_name: Name of the AI model.
        model_version: Version of the AI model.
        model_behavior_notes: Notes about model-specific behavior.
        validation_success: Whether the fix was validated successfully.
        validation_notes: Notes about the validation.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    master_issue_id: UUID
    contribution_type: ContributionType
    sanitized_error: str = Field(..., min_length=5)
    sanitized_context: Optional[str] = None
    sanitized_mre: Optional[str] = None
    environment: dict = Field(default_factory=dict)
    model_provider: str = Field(..., min_length=1, max_length=50)
    model_name: str = Field(..., min_length=1, max_length=100)
    model_version: Optional[str] = None
    model_behavior_notes: List[str] = Field(default_factory=list)
    validation_success: Optional[bool] = None
    validation_notes: Optional[str] = None


class ChildIssueResponse(ChildIssueCreate):
    """Model for child issue API responses.

    Attributes:
        id: Unique identifier for the child issue.
        created_at: Timestamp when child issue was created.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
