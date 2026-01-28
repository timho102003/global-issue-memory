"""Tests for contribution classifier service."""

import pytest

from src.models.issue import ContributionType
from src.services.contribution_classifier import classify_contribution_type


class TestClassifyContributionType:
    """Test cases for classify_contribution_type function."""

    def test_validation_with_explicit_success(self) -> None:
        """Test classification returns VALIDATION when validation_success is provided."""
        result = classify_contribution_type(
            error_message="Some error",
            root_cause="Some cause",
            fix_steps=["Step 1"],
            validation_success=True,
        )
        assert result == ContributionType.VALIDATION

    def test_validation_with_explicit_failure(self) -> None:
        """Test classification returns VALIDATION even with False validation_success."""
        result = classify_contribution_type(
            error_message="Some error",
            root_cause="Some cause",
            fix_steps=["Step 1"],
            validation_success=False,
        )
        assert result == ContributionType.VALIDATION

    def test_environment_with_actions(self) -> None:
        """Test classification returns ENVIRONMENT when environment_actions provided."""
        result = classify_contribution_type(
            error_message="Some error",
            root_cause="Some cause",
            fix_steps=["Step 1"],
            environment_actions=[{"action": "install", "package": "requests"}],
        )
        assert result == ContributionType.ENVIRONMENT

    def test_environment_with_keywords_in_error(self) -> None:
        """Test classification returns ENVIRONMENT when env keywords in error."""
        result = classify_contribution_type(
            error_message="Package dependency not found",
            root_cause="Missing pip install",
            fix_steps=["Run pip install requests"],
        )
        assert result == ContributionType.ENVIRONMENT

    def test_environment_with_keywords_in_steps(self) -> None:
        """Test classification returns ENVIRONMENT when env keywords in fix steps."""
        result = classify_contribution_type(
            error_message="Error occurred",
            root_cause="Wrong version",
            fix_steps=["npm install lodash", "Upgrade the library"],
        )
        assert result == ContributionType.ENVIRONMENT

    def test_model_quirk_with_notes(self) -> None:
        """Test classification returns MODEL_QUIRK when model_behavior_notes provided."""
        result = classify_contribution_type(
            error_message="Some error",
            root_cause="Some cause",
            fix_steps=["Step 1"],
            model_behavior_notes=["Claude tends to hallucinate tool names"],
        )
        assert result == ContributionType.MODEL_QUIRK

    def test_model_quirk_with_keywords_in_error(self) -> None:
        """Test classification returns MODEL_QUIRK when model keywords in error."""
        result = classify_contribution_type(
            error_message="Claude model returned invalid response",
            root_cause="LLM hallucination in tool call",
            fix_steps=["Adjust the prompt"],
        )
        assert result == ContributionType.MODEL_QUIRK

    def test_model_quirk_with_keywords_in_cause(self) -> None:
        """Test classification returns MODEL_QUIRK when model keywords in root cause."""
        result = classify_contribution_type(
            error_message="Function failed",
            root_cause="GPT token limit exceeded in context",
            fix_steps=["Reduce context size"],
        )
        assert result == ContributionType.MODEL_QUIRK

    def test_symptom_default(self) -> None:
        """Test classification returns SYMPTOM as default."""
        result = classify_contribution_type(
            error_message="Some random error",
            root_cause="Unknown cause",
            fix_steps=["Try something"],
        )
        assert result == ContributionType.SYMPTOM

    def test_symptom_with_empty_lists(self) -> None:
        """Test classification returns SYMPTOM with empty optional lists."""
        result = classify_contribution_type(
            error_message="Error",
            root_cause="Cause",
            fix_steps=["Fix"],
            environment_actions=[],
            model_behavior_notes=[],
        )
        assert result == ContributionType.SYMPTOM

    def test_priority_validation_over_environment(self) -> None:
        """Test VALIDATION takes priority over ENVIRONMENT."""
        result = classify_contribution_type(
            error_message="Package not found",
            root_cause="Missing dependency",
            fix_steps=["pip install package"],
            environment_actions=[{"action": "install"}],
            validation_success=True,
        )
        assert result == ContributionType.VALIDATION

    def test_priority_environment_over_model_quirk(self) -> None:
        """Test ENVIRONMENT takes priority over MODEL_QUIRK."""
        result = classify_contribution_type(
            error_message="Claude model package not found",
            root_cause="Need to install library",
            fix_steps=["pip install langchain"],
            model_behavior_notes=["Note about model"],
        )
        assert result == ContributionType.ENVIRONMENT

    def test_none_values_for_optional_params(self) -> None:
        """Test with None values for optional parameters."""
        result = classify_contribution_type(
            error_message="Error",
            root_cause="Cause",
            fix_steps=["Fix"],
            environment_actions=None,
            model_behavior_notes=None,
            validation_success=None,
        )
        assert result == ContributionType.SYMPTOM

    def test_case_insensitive_keyword_matching(self) -> None:
        """Test keyword matching is case insensitive."""
        result = classify_contribution_type(
            error_message="DOCKER CONTAINER failed",
            root_cause="KUBERNETES pod error",
            fix_steps=["Check ENVIRONMENT variables"],
        )
        assert result == ContributionType.ENVIRONMENT
