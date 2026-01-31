"""Tests for the LLM extractor module.

Mocks the Gemini API to test extraction and scoring logic.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.crawler.llm_extractor import (
    ExtractionResult,
    _format_comments,
    _truncate,
    extract_issue_data,
    score_quality,
)


class TestTruncate:
    """Tests for _truncate helper."""

    def test_short_text_unchanged(self) -> None:
        """Short text is not truncated."""
        assert _truncate("hello", 100) == "hello"

    def test_long_text_truncated(self) -> None:
        """Long text is truncated with indicator."""
        result = _truncate("a" * 200, 100)
        assert len(result) > 100
        assert result.endswith("... (truncated)")

    def test_none_returns_empty(self) -> None:
        """None input returns empty string."""
        assert _truncate(None) == ""

    def test_empty_returns_empty(self) -> None:
        """Empty string returns empty string."""
        assert _truncate("") == ""


class TestFormatComments:
    """Tests for _format_comments helper."""

    def test_empty_comments(self) -> None:
        """Empty list returns 'No comments.'."""
        assert _format_comments([]) == "No comments."

    def test_formats_comments(self) -> None:
        """Comments are formatted with author prefix."""
        comments = [
            {"author": "user1", "body": "First comment"},
            {"author": "user2", "body": "Second comment"},
        ]
        result = _format_comments(comments)
        assert "@user1: First comment" in result
        assert "@user2: Second comment" in result

    def test_respects_max_comments(self) -> None:
        """Only max_comments are included."""
        comments = [{"author": f"u{i}", "body": f"c{i}"} for i in range(20)]
        result = _format_comments(comments, max_comments=3)
        assert "@u0:" in result
        assert "@u2:" in result
        assert "@u3:" not in result


class TestExtractIssueData:
    """Tests for extract_issue_data function."""

    @pytest.fixture
    def mock_genai(self) -> MagicMock:
        """Create a mock Gemini client.

        Returns:
            MagicMock: Mock genai client.
        """
        with patch("src.crawler.llm_extractor._get_genai_client") as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings.

        Returns:
            MagicMock: Mock settings.
        """
        with patch("src.crawler.llm_extractor.get_settings") as mock:
            settings = MagicMock()
            settings.llm_model = "gemini-3.0-flash-preview"
            mock.return_value = settings
            yield settings

    async def test_successful_extraction(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Successful extraction returns correct data."""
        response_data = {
            "error_message": "TypeError: 'NoneType' has no attribute 'get'",
            "root_cause": "Variable not checked for None before access",
            "fix_summary": "Added None guard clause",
            "fix_steps": ["Add if check", "Add test case"],
            "language": "python",
            "framework": "flask",
            "confidence": 0.85,
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(response_data)
        mock_genai.models.generate_content.return_value = mock_response

        result = await extract_issue_data(
            issue_title="Fix TypeError in request handling",
            issue_body="Got TypeError when request is None",
            comments=[],
            pr_body="Added None check",
            pr_diff_summary="+5/-0",
        )

        assert result.success is True
        assert result.error_message == "TypeError: 'NoneType' has no attribute 'get'"
        assert result.confidence == 0.85
        assert result.language == "python"
        assert len(result.fix_steps) == 2

    async def test_not_found_error_message(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """NOT_FOUND error message triggers failure."""
        response_data = {
            "error_message": "NOT_FOUND",
            "root_cause": "",
            "fix_summary": "",
            "fix_steps": [],
            "language": None,
            "framework": None,
            "confidence": 0.1,
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(response_data)
        mock_genai.models.generate_content.return_value = mock_response

        result = await extract_issue_data(
            issue_title="Test",
            issue_body="Some body",
            comments=[],
            pr_body=None,
            pr_diff_summary=None,
        )

        assert result.success is False
        assert "no clear error" in result.error.lower() or "low confidence" in result.error.lower()

    async def test_low_confidence_triggers_failure(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Confidence < 0.3 triggers failure."""
        response_data = {
            "error_message": "Some error",
            "root_cause": "Unknown",
            "fix_summary": "Unknown fix",
            "fix_steps": ["Step"],
            "confidence": 0.2,
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(response_data)
        mock_genai.models.generate_content.return_value = mock_response

        result = await extract_issue_data(
            issue_title="Test",
            issue_body="Body",
            comments=[],
            pr_body=None,
            pr_diff_summary=None,
        )

        assert result.success is False

    async def test_invalid_json_handling(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Invalid JSON from LLM is handled gracefully."""
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        mock_genai.models.generate_content.return_value = mock_response

        result = await extract_issue_data(
            issue_title="Test",
            issue_body="Body",
            comments=[],
            pr_body=None,
            pr_diff_summary=None,
        )

        assert result.success is False
        assert "JSON" in result.error

    async def test_api_failure_handling(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """API exception is handled gracefully."""
        mock_genai.models.generate_content.side_effect = Exception("API error")

        result = await extract_issue_data(
            issue_title="Test",
            issue_body="Body",
            comments=[],
            pr_body=None,
            pr_diff_summary=None,
        )

        assert result.success is False
        assert "API error" in result.error

    async def test_markdown_code_blocks_stripped(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Markdown code blocks are stripped from LLM response."""
        response_data = {
            "error_message": "TypeError: test",
            "root_cause": "Test cause",
            "fix_summary": "Test fix",
            "fix_steps": ["Step 1"],
            "confidence": 0.8,
        }
        mock_response = MagicMock()
        mock_response.text = f"```json\n{json.dumps(response_data)}\n```"
        mock_genai.models.generate_content.return_value = mock_response

        result = await extract_issue_data(
            issue_title="Test",
            issue_body="Body with Error:",
            comments=[],
            pr_body=None,
            pr_diff_summary=None,
        )

        assert result.success is True
        assert result.error_message == "TypeError: test"


class TestScoreQuality:
    """Tests for score_quality function."""

    @pytest.fixture
    def mock_genai(self) -> MagicMock:
        """Create a mock Gemini client.

        Returns:
            MagicMock: Mock genai client.
        """
        with patch("src.crawler.llm_extractor._get_genai_client") as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings.

        Returns:
            MagicMock: Mock settings.
        """
        with patch("src.crawler.llm_extractor.get_settings") as mock:
            settings = MagicMock()
            settings.llm_model = "gemini-3.0-flash-preview"
            mock.return_value = settings
            yield settings

    async def test_valid_score(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Valid score is returned."""
        mock_response = MagicMock()
        mock_response.text = "0.75"
        mock_genai.models.generate_content.return_value = mock_response

        score = await score_quality(
            error_message="TypeError: test",
            root_cause="None check missing",
            fix_summary="Added guard clause",
        )
        assert score == 0.75

    async def test_score_clamped_to_max(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Score > 1.0 is clamped to 1.0."""
        mock_response = MagicMock()
        mock_response.text = "1.5"
        mock_genai.models.generate_content.return_value = mock_response

        score = await score_quality(
            error_message="Error",
            root_cause="Cause",
            fix_summary="Fix",
        )
        assert score == 1.0

    async def test_score_clamped_to_min(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Score < 0.0 is clamped to 0.0."""
        mock_response = MagicMock()
        mock_response.text = "-0.5"
        mock_genai.models.generate_content.return_value = mock_response

        score = await score_quality(
            error_message="Error",
            root_cause="Cause",
            fix_summary="Fix",
        )
        assert score == 0.0

    async def test_invalid_response_returns_zero(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Non-numeric response returns 0.0."""
        mock_response = MagicMock()
        mock_response.text = "Not a number"
        mock_genai.models.generate_content.return_value = mock_response

        score = await score_quality(
            error_message="Error",
            root_cause="Cause",
            fix_summary="Fix",
        )
        assert score == 0.0

    async def test_api_error_returns_zero(
        self, mock_genai: MagicMock, mock_settings: MagicMock
    ) -> None:
        """API error returns 0.0."""
        mock_genai.models.generate_content.side_effect = Exception("API error")

        score = await score_quality(
            error_message="Error",
            root_cause="Cause",
            fix_summary="Fix",
        )
        assert score == 0.0
