"""Tests for model parser service."""

import pytest

from src.services.model_parser import (
    parse_model_info,
    get_model_family,
    _extract_version,
    _detect_provider,
)


class TestParseModelInfo:
    """Test cases for parse_model_info function."""

    def test_none_model(self) -> None:
        """Test with None model returns None values."""
        provider, name, version = parse_model_info(None, None)
        assert provider is None
        assert name is None
        assert version is None

    def test_explicit_provider_with_none_model(self) -> None:
        """Test explicit provider is returned even with None model."""
        provider, name, version = parse_model_info(None, "anthropic")
        assert provider == "anthropic"
        assert name is None
        assert version is None

    def test_claude_model_with_date_version(self) -> None:
        """Test Claude model with date version."""
        provider, name, version = parse_model_info("claude-3-opus-20240229")
        assert provider == "anthropic"
        assert name == "claude-3-opus"
        assert version == "20240229"

    def test_claude_model_with_hyphenated_date(self) -> None:
        """Test Claude model with hyphenated date version."""
        provider, name, version = parse_model_info("claude-3-opus-2024-02-29")
        assert provider == "anthropic"
        assert name == "claude-3-opus"
        assert version == "2024-02-29"

    def test_gpt_model_with_date(self) -> None:
        """Test GPT model with date version."""
        provider, name, version = parse_model_info("gpt-4-turbo-2024-04-09")
        assert provider == "openai"
        assert name == "gpt-4-turbo"
        assert version == "2024-04-09"

    def test_gpt_model_without_version(self) -> None:
        """Test GPT model without version."""
        provider, name, version = parse_model_info("gpt-4-turbo")
        assert provider == "openai"
        assert name == "gpt-4-turbo"
        assert version is None

    def test_gemini_model(self) -> None:
        """Test Gemini model detection."""
        provider, name, version = parse_model_info("gemini-1.5-pro")
        assert provider == "google"
        assert name == "gemini-1.5-pro"
        assert version is None

    def test_llama_model(self) -> None:
        """Test Llama model detection."""
        provider, name, version = parse_model_info("llama-3-70b")
        assert provider == "meta"
        assert name == "llama-3-70b"
        assert version is None

    def test_mistral_model(self) -> None:
        """Test Mistral model detection."""
        provider, name, version = parse_model_info("mistral-large")
        assert provider == "mistral"
        assert name == "mistral-large"
        assert version is None

    def test_mixtral_model(self) -> None:
        """Test Mixtral model detection."""
        provider, name, version = parse_model_info("mixtral-8x7b")
        assert provider == "mistral"
        assert name == "mixtral-8x7b"
        assert version is None

    def test_explicit_provider_overrides_detection(self) -> None:
        """Test explicit provider overrides auto-detection."""
        provider, name, version = parse_model_info("claude-3-opus", "custom-provider")
        assert provider == "custom-provider"
        assert name == "claude-3-opus"

    def test_unknown_model(self) -> None:
        """Test unknown model returns None provider."""
        provider, name, version = parse_model_info("some-random-model")
        assert provider is None
        assert name == "some-random-model"
        assert version is None

    def test_case_insensitive(self) -> None:
        """Test model parsing is case insensitive."""
        provider, name, version = parse_model_info("CLAUDE-3-OPUS")
        assert provider == "anthropic"


class TestExtractVersion:
    """Test cases for _extract_version helper."""

    def test_date_version_compact(self) -> None:
        """Test extraction of compact date version."""
        name, version = _extract_version("model-20240229")
        assert name == "model"
        assert version == "20240229"

    def test_date_version_hyphenated(self) -> None:
        """Test extraction of hyphenated date version."""
        name, version = _extract_version("model-2024-04-09")
        assert name == "model"
        assert version == "2024-04-09"

    def test_semver(self) -> None:
        """Test extraction of semantic version."""
        name, version = _extract_version("model-1.5.0")
        assert name == "model"
        assert version == "1.5.0"

    def test_semver_with_v_prefix(self) -> None:
        """Test extraction of version with v prefix."""
        name, version = _extract_version("model-v2.0")
        assert name == "model"
        assert version == "2.0"

    def test_revision_suffix(self) -> None:
        """Test extraction of revision suffix."""
        name, version = _extract_version("model-rev1")
        assert name == "model"
        assert version == "rev1"

    def test_no_version(self) -> None:
        """Test model with no version."""
        name, version = _extract_version("simple-model-name")
        assert name == "simple-model-name"
        assert version is None


class TestDetectProvider:
    """Test cases for _detect_provider helper."""

    def test_anthropic_detection(self) -> None:
        """Test Anthropic provider detection."""
        assert _detect_provider("claude-3-opus") == "anthropic"
        assert _detect_provider("claude-instant") == "anthropic"

    def test_openai_detection(self) -> None:
        """Test OpenAI provider detection."""
        assert _detect_provider("gpt-4") == "openai"
        assert _detect_provider("gpt-4-turbo") == "openai"
        assert _detect_provider("o1-preview") == "openai"
        assert _detect_provider("text-embedding-3-small") == "openai"

    def test_google_detection(self) -> None:
        """Test Google provider detection."""
        assert _detect_provider("gemini-1.5-pro") == "google"
        assert _detect_provider("palm-2") == "google"

    def test_meta_detection(self) -> None:
        """Test Meta provider detection."""
        assert _detect_provider("llama-3-70b") == "meta"
        assert _detect_provider("llama2") == "meta"

    def test_unknown_provider(self) -> None:
        """Test unknown model returns None."""
        assert _detect_provider("random-model") is None


class TestGetModelFamily:
    """Test cases for get_model_family function."""

    def test_claude_family(self) -> None:
        """Test Claude model family extraction."""
        assert get_model_family("claude-3-opus") == "claude-3"
        assert get_model_family("claude-3.5-sonnet") == "claude-3.5"
        assert get_model_family("claude-2") == "claude-2"

    def test_gpt_family(self) -> None:
        """Test GPT model family extraction."""
        assert get_model_family("gpt-4-turbo") == "gpt-4"
        assert get_model_family("gpt-3.5-turbo") == "gpt-3"

    def test_gemini_family(self) -> None:
        """Test Gemini model family extraction."""
        assert get_model_family("gemini-1.5-pro") == "gemini-1.5"
        assert get_model_family("gemini-2-flash") == "gemini-2"

    def test_llama_family(self) -> None:
        """Test Llama model family extraction."""
        assert get_model_family("llama-3-70b") == "llama-3"
        assert get_model_family("llama2-7b") == "llama2"

    def test_none_input(self) -> None:
        """Test None input returns None."""
        assert get_model_family(None) is None

    def test_unrecognized_model(self) -> None:
        """Test unrecognized model returns None."""
        assert get_model_family("random-model") is None
