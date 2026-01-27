"""Tests for environment models."""

import pytest
from pydantic import ValidationError

from src.models.environment import (
    EnvironmentInfo,
    ModelInfo,
    ModelProvider,
)


class TestModelProvider:
    """Tests for ModelProvider enum."""

    def test_all_providers(self) -> None:
        """Test all model providers have correct values."""
        assert ModelProvider.ANTHROPIC.value == "anthropic"
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.GOOGLE.value == "google"
        assert ModelProvider.GROQ.value == "groq"
        assert ModelProvider.TOGETHER.value == "together"
        assert ModelProvider.LOCAL.value == "local"
        assert ModelProvider.OTHER.value == "other"


class TestModelInfo:
    """Tests for ModelInfo model."""

    def test_valid_model_info(self) -> None:
        """Test creating valid model info."""
        model = ModelInfo(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-opus",
            model_version="20240229",
            behavior_notes=["strong at tool calling", "strict JSON schema"],
        )
        assert model.provider == ModelProvider.ANTHROPIC
        assert model.model_name == "claude-3-opus"
        assert len(model.behavior_notes) == 2

    def test_model_name_required(self) -> None:
        """Test that model_name is required."""
        with pytest.raises(ValidationError):
            ModelInfo(
                provider=ModelProvider.OPENAI,
            )

    def test_model_name_min_length(self) -> None:
        """Test that model_name must have minimum length."""
        with pytest.raises(ValidationError):
            ModelInfo(
                provider=ModelProvider.OPENAI,
                model_name="",
            )

    def test_model_version_optional(self) -> None:
        """Test that model_version is optional."""
        model = ModelInfo(
            provider=ModelProvider.GOOGLE,
            model_name="gemini-pro",
        )
        assert model.model_version is None

    def test_behavior_notes_default_empty(self) -> None:
        """Test that behavior_notes defaults to empty list."""
        model = ModelInfo(
            provider=ModelProvider.GROQ,
            model_name="llama-3-70b",
        )
        assert model.behavior_notes == []

    def test_whitespace_stripping(self) -> None:
        """Test that whitespace is stripped from model name."""
        model = ModelInfo(
            provider=ModelProvider.TOGETHER,
            model_name="  mixtral-8x7b  ",
        )
        assert model.model_name == "mixtral-8x7b"


class TestEnvironmentInfo:
    """Tests for EnvironmentInfo model."""

    def test_valid_environment_info(self) -> None:
        """Test creating valid environment info."""
        env = EnvironmentInfo(
            language="python",
            language_version="3.11",
            framework="langchain",
            framework_version="0.2.0",
            os="macOS",
        )
        assert env.language == "python"
        assert env.framework_version == "0.2.0"

    def test_all_fields_optional(self) -> None:
        """Test that all fields are optional."""
        env = EnvironmentInfo()
        assert env.language is None
        assert env.language_version is None
        assert env.framework is None
        assert env.framework_version is None
        assert env.os is None
        assert env.additional == {}

    def test_additional_field(self) -> None:
        """Test the additional field for extra info."""
        env = EnvironmentInfo(
            language="python",
            additional={
                "docker": True,
                "ci": "github-actions",
            },
        )
        assert env.additional["docker"] is True
        assert env.additional["ci"] == "github-actions"

    def test_to_search_string_full(self) -> None:
        """Test to_search_string with all fields."""
        env = EnvironmentInfo(
            language="python",
            language_version="3.11",
            framework="fastapi",
            framework_version="0.100.0",
            os="Ubuntu 22.04",
        )
        search_str = env.to_search_string()
        assert "python 3.11" in search_str
        assert "fastapi 0.100.0" in search_str
        assert "Ubuntu 22.04" in search_str

    def test_to_search_string_partial(self) -> None:
        """Test to_search_string with partial fields."""
        env = EnvironmentInfo(
            language="python",
            os="Windows",
        )
        search_str = env.to_search_string()
        assert "python" in search_str
        assert "Windows" in search_str

    def test_to_search_string_empty(self) -> None:
        """Test to_search_string with no fields."""
        env = EnvironmentInfo()
        search_str = env.to_search_string()
        assert search_str == ""

    def test_whitespace_stripping(self) -> None:
        """Test that whitespace is stripped."""
        env = EnvironmentInfo(
            language="  python  ",
            framework="  django  ",
        )
        assert env.language == "python"
        assert env.framework == "django"
