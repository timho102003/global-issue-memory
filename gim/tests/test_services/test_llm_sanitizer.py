"""Tests for LLM sanitizer service."""

import pytest
from unittest.mock import MagicMock, patch

from src.services.sanitization.llm_sanitizer import (
    LLMSanitizationResult,
    sanitize_code_with_llm,
    sanitize_error_message_with_llm,
    sanitize_context_with_llm,
)


class TestLLMSanitizationResult:
    """Tests for LLMSanitizationResult dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        result = LLMSanitizationResult()
        assert result.original_text == ""
        assert result.sanitized_text == ""
        assert result.changes_made == []
        assert result.success is True
        assert result.error is None

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        result = LLMSanitizationResult(
            original_text="original",
            sanitized_text="sanitized",
            changes_made=["change1"],
            success=False,
            error="error message",
        )
        assert result.original_text == "original"
        assert result.sanitized_text == "sanitized"
        assert result.changes_made == ["change1"]
        assert result.success is False
        assert result.error == "error message"


class TestSanitizeCodeWithLLMMocked:
    """Tests for sanitize_code_with_llm with mocked API."""

    @pytest.mark.asyncio
    async def test_empty_code_returns_empty(self) -> None:
        """Test that empty code returns empty result."""
        result = await sanitize_code_with_llm("")
        assert result.original_text == ""
        assert result.sanitized_text == ""
        assert result.success is True

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_empty(self) -> None:
        """Test that whitespace-only code returns empty result."""
        result = await sanitize_code_with_llm("   \n\t  ")
        assert result.sanitized_text == ""
        assert result.success is True

    @pytest.mark.asyncio
    async def test_valid_code_calls_api(self) -> None:
        """Test that valid code calls the LLM API."""
        mock_response = MagicMock()
        mock_response.text = "sanitized_code()"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("src.services.sanitization.llm_sanitizer._get_genai_client", return_value=mock_client), \
             patch("src.services.sanitization.llm_sanitizer.get_settings") as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash-preview-05-20"

            result = await sanitize_code_with_llm("secret_code()")

            assert result.success is True
            assert result.sanitized_text == "sanitized_code()"
            mock_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_removes_markdown_code_blocks(self) -> None:
        """Test that markdown code blocks are removed from response."""
        mock_response = MagicMock()
        mock_response.text = "```python\nclean_code()\n```"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("src.services.sanitization.llm_sanitizer._get_genai_client", return_value=mock_client), \
             patch("src.services.sanitization.llm_sanitizer.get_settings") as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash-preview-05-20"

            result = await sanitize_code_with_llm("code()")

            assert result.sanitized_text == "clean_code()"
            assert "```" not in result.sanitized_text

    @pytest.mark.asyncio
    async def test_api_error_returns_original(self) -> None:
        """Test that API errors return original code."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")

        with patch("src.services.sanitization.llm_sanitizer._get_genai_client", return_value=mock_client), \
             patch("src.services.sanitization.llm_sanitizer.get_settings") as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash-preview-05-20"

            result = await sanitize_code_with_llm("original_code()")

            assert result.success is False
            assert result.sanitized_text == "original_code()"
            assert "API Error" in result.error

    @pytest.mark.asyncio
    async def test_with_error_context(self) -> None:
        """Test sanitization with error context."""
        mock_response = MagicMock()
        mock_response.text = "sanitized()"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("src.services.sanitization.llm_sanitizer._get_genai_client", return_value=mock_client), \
             patch("src.services.sanitization.llm_sanitizer.get_settings") as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash-preview-05-20"

            result = await sanitize_code_with_llm(
                "code()",
                error_context="TypeError at line 5"
            )

            assert result.success is True
            # Verify error context was included in prompt
            call_args = mock_client.models.generate_content.call_args
            assert "TypeError at line 5" in call_args.kwargs["contents"]


class TestSanitizeErrorMessageWithLLMMocked:
    """Tests for sanitize_error_message_with_llm with mocked API."""

    @pytest.mark.asyncio
    async def test_empty_message_returns_empty(self) -> None:
        """Test that empty message returns empty result."""
        result = await sanitize_error_message_with_llm("")
        assert result.original_text == ""
        assert result.sanitized_text == ""
        assert result.success is True

    @pytest.mark.asyncio
    async def test_valid_message_calls_api(self) -> None:
        """Test that valid message calls the LLM API."""
        mock_response = MagicMock()
        mock_response.text = "Error at /path/to/file.py"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("src.services.sanitization.llm_sanitizer._get_genai_client", return_value=mock_client), \
             patch("src.services.sanitization.llm_sanitizer.get_settings") as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash-preview-05-20"

            result = await sanitize_error_message_with_llm(
                "Error at /Users/john/project/file.py"
            )

            assert result.success is True
            assert result.sanitized_text == "Error at /path/to/file.py"
            assert len(result.changes_made) > 0

    @pytest.mark.asyncio
    async def test_api_error_returns_original(self) -> None:
        """Test that API errors return original message."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Network Error")

        with patch("src.services.sanitization.llm_sanitizer._get_genai_client", return_value=mock_client), \
             patch("src.services.sanitization.llm_sanitizer.get_settings") as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash-preview-05-20"

            result = await sanitize_error_message_with_llm("original error")

            assert result.success is False
            assert result.sanitized_text == "original error"
            assert "Network Error" in result.error


class TestSanitizeContextWithLLMMocked:
    """Tests for sanitize_context_with_llm with mocked API."""

    @pytest.mark.asyncio
    async def test_empty_context_returns_empty(self) -> None:
        """Test that empty context returns empty result."""
        result = await sanitize_context_with_llm("")
        assert result.original_text == ""
        assert result.sanitized_text == ""
        assert result.success is True

    @pytest.mark.asyncio
    async def test_valid_context_calls_api(self) -> None:
        """Test that valid context calls the LLM API."""
        mock_response = MagicMock()
        mock_response.text = "User encountered an error in the app"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("src.services.sanitization.llm_sanitizer._get_genai_client", return_value=mock_client), \
             patch("src.services.sanitization.llm_sanitizer.get_settings") as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash-preview-05-20"

            result = await sanitize_context_with_llm(
                "John Doe at Acme Corp encountered an error in the app"
            )

            assert result.success is True
            assert "John Doe" not in result.sanitized_text
            assert "Acme Corp" not in result.sanitized_text


class TestLLMSanitizerIntegration:
    """Integration tests for LLM sanitizer (requires API key)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_code_sanitization(self) -> None:
        """Test real code sanitization with small code."""
        try:
            from src.config import get_settings
            settings = get_settings()
            if not settings.google_api_key:
                pytest.skip("GOOGLE_API_KEY not configured")
        except Exception:
            pytest.skip("Settings not configured")

        code = """
api_key = "sk-secret123"
user = "john@acme.com"
print(f"Hello {user}")
"""
        result = await sanitize_code_with_llm(code)

        assert result.success is True
        # Should remove or replace sensitive values
        assert "sk-secret123" not in result.sanitized_text
        assert "john@acme.com" not in result.sanitized_text

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_error_message_sanitization(self) -> None:
        """Test real error message sanitization."""
        try:
            from src.config import get_settings
            settings = get_settings()
            if not settings.google_api_key:
                pytest.skip("GOOGLE_API_KEY not configured")
        except Exception:
            pytest.skip("Settings not configured")

        error = "FileNotFoundError: /Users/john/secret/project/main.py"
        result = await sanitize_error_message_with_llm(error)

        assert result.success is True
        # Should remove username from path
        assert "/Users/john/" not in result.sanitized_text
        # Should preserve error type
        assert "FileNotFoundError" in result.sanitized_text

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_context_sanitization(self) -> None:
        """Test real context sanitization."""
        try:
            from src.config import get_settings
            settings = get_settings()
            if not settings.google_api_key:
                pytest.skip("GOOGLE_API_KEY not configured")
        except Exception:
            pytest.skip("Settings not configured")

        context = "Developer Jane Smith at BigCorp Inc had an issue"
        result = await sanitize_context_with_llm(context)

        assert result.success is True
        # Should remove personal/company info
        assert "Jane Smith" not in result.sanitized_text
        assert "BigCorp" not in result.sanitized_text
