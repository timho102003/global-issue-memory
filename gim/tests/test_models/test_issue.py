"""Tests for issue models."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.models.issue import (
    ChildIssueCreate,
    ContributionType,
    IssueStatus,
    MasterIssueCreate,
    MasterIssueResponse,
    RootCauseCategory,
)


class TestMasterIssueCreate:
    """Tests for MasterIssueCreate model."""

    def test_valid_master_issue_create(self) -> None:
        """Test creating a valid master issue."""
        issue = MasterIssueCreate(
            canonical_title="LangChain tool decorator import error",
            description="The @tool decorator was moved to langchain_core in version 0.2.x",
            root_cause_category=RootCauseCategory.ENVIRONMENT,
            root_cause_subcategory="dependency_version_mismatch",
        )
        assert issue.canonical_title == "LangChain tool decorator import error"
        assert issue.root_cause_category == RootCauseCategory.ENVIRONMENT

    def test_title_too_short(self) -> None:
        """Test that short titles are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MasterIssueCreate(
                canonical_title="Short",
                description="This is a valid description for the issue.",
                root_cause_category=RootCauseCategory.ENVIRONMENT,
            )
        assert "canonical_title" in str(exc_info.value)

    def test_description_too_short(self) -> None:
        """Test that short descriptions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MasterIssueCreate(
                canonical_title="Valid title for the issue here",
                description="Too short",
                root_cause_category=RootCauseCategory.ENVIRONMENT,
            )
        assert "description" in str(exc_info.value)

    def test_whitespace_stripping(self) -> None:
        """Test that whitespace is stripped from strings."""
        issue = MasterIssueCreate(
            canonical_title="  LangChain tool decorator import error  ",
            description="  The @tool decorator was moved to langchain_core  ",
            root_cause_category=RootCauseCategory.ENVIRONMENT,
        )
        assert issue.canonical_title == "LangChain tool decorator import error"
        assert issue.description == "The @tool decorator was moved to langchain_core"

    def test_optional_subcategory(self) -> None:
        """Test that subcategory is optional."""
        issue = MasterIssueCreate(
            canonical_title="Valid title for the issue here",
            description="This is a valid description for the issue.",
            root_cause_category=RootCauseCategory.CODE_GENERATION,
        )
        assert issue.root_cause_subcategory is None


class TestMasterIssueResponse:
    """Tests for MasterIssueResponse model."""

    def test_valid_master_issue_response(self) -> None:
        """Test creating a valid master issue response."""
        issue = MasterIssueResponse(
            id=uuid4(),
            canonical_title="LangChain tool decorator import error",
            description="The @tool decorator was moved to langchain_core in version 0.2.x",
            root_cause_category=RootCauseCategory.ENVIRONMENT,
            confidence_score=0.85,
            child_issue_count=5,
            environment_coverage=["python 3.11", "macOS"],
            verification_count=10,
            status=IssueStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert issue.confidence_score == 0.85
        assert issue.child_issue_count == 5
        assert len(issue.environment_coverage) == 2

    def test_confidence_score_bounds(self) -> None:
        """Test that confidence score must be between 0 and 1."""
        with pytest.raises(ValidationError):
            MasterIssueResponse(
                id=uuid4(),
                canonical_title="Valid title for the issue here",
                description="This is a valid description for the issue.",
                root_cause_category=RootCauseCategory.ENVIRONMENT,
                confidence_score=1.5,
                child_issue_count=0,
                verification_count=0,
                status=IssueStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

    def test_negative_counts_rejected(self) -> None:
        """Test that negative counts are rejected."""
        with pytest.raises(ValidationError):
            MasterIssueResponse(
                id=uuid4(),
                canonical_title="Valid title for the issue here",
                description="This is a valid description for the issue.",
                root_cause_category=RootCauseCategory.ENVIRONMENT,
                confidence_score=0.5,
                child_issue_count=-1,
                verification_count=0,
                status=IssueStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )


class TestChildIssueCreate:
    """Tests for ChildIssueCreate model."""

    def test_valid_child_issue_create(self) -> None:
        """Test creating a valid child issue."""
        child = ChildIssueCreate(
            master_issue_id=uuid4(),
            contribution_type=ContributionType.ENVIRONMENT,
            sanitized_error="AttributeError: module 'langchain.tools' has no attribute 'tool'",
            model_provider="anthropic",
            model_name="claude-3-opus",
        )
        assert child.contribution_type == ContributionType.ENVIRONMENT
        assert child.model_provider == "anthropic"

    def test_sanitized_error_too_short(self) -> None:
        """Test that short sanitized errors are rejected."""
        with pytest.raises(ValidationError):
            ChildIssueCreate(
                master_issue_id=uuid4(),
                contribution_type=ContributionType.SYMPTOM,
                sanitized_error="Err",
                model_provider="anthropic",
                model_name="claude-3-opus",
            )

    def test_optional_fields_default(self) -> None:
        """Test that optional fields have correct defaults."""
        child = ChildIssueCreate(
            master_issue_id=uuid4(),
            contribution_type=ContributionType.VALIDATION,
            sanitized_error="Valid error message here",
            model_provider="openai",
            model_name="gpt-4",
        )
        assert child.sanitized_context is None
        assert child.sanitized_mre is None
        assert child.environment == {}
        assert child.model_behavior_notes == []
        assert child.validation_success is None


class TestEnums:
    """Tests for issue-related enums."""

    def test_issue_status_values(self) -> None:
        """Test IssueStatus enum values."""
        assert IssueStatus.ACTIVE.value == "active"
        assert IssueStatus.SUPERSEDED.value == "superseded"
        assert IssueStatus.INVALID.value == "invalid"

    def test_contribution_type_values(self) -> None:
        """Test ContributionType enum values."""
        assert ContributionType.ENVIRONMENT.value == "environment"
        assert ContributionType.SYMPTOM.value == "symptom"
        assert ContributionType.MODEL_QUIRK.value == "model_quirk"
        assert ContributionType.VALIDATION.value == "validation"

    def test_root_cause_category_values(self) -> None:
        """Test RootCauseCategory enum values."""
        assert RootCauseCategory.ENVIRONMENT.value == "environment"
        assert RootCauseCategory.MODEL_BEHAVIOR.value == "model_behavior"
        assert RootCauseCategory.API_INTEGRATION.value == "api_integration"
        assert RootCauseCategory.CODE_GENERATION.value == "code_generation"
        assert RootCauseCategory.FRAMEWORK_SPECIFIC.value == "framework_specific"
