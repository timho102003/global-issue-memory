"""Tests for GIM MCP tools."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.tools.base import ToolDefinition, create_text_response, create_error_response
from src.tools.gim_search_issues import search_issues_tool, execute as search_execute
from src.tools.gim_get_fix_bundle import get_fix_bundle_tool, execute as get_fix_execute
from src.tools.gim_submit_issue import submit_issue_tool, execute as submit_execute
from src.tools.gim_confirm_fix import confirm_fix_tool, execute as confirm_execute
from src.tools.gim_report_usage import report_usage_tool, execute as report_execute


class TestToolDefinitions:
    """Tests for tool definitions."""

    def test_search_issues_tool_definition(self) -> None:
        """Test search issues tool has correct definition."""
        assert search_issues_tool.name == "gim_search_issues"
        assert "error_message" in search_issues_tool.input_schema["properties"]
        assert "error_message" in search_issues_tool.input_schema["required"]

    def test_get_fix_bundle_tool_definition(self) -> None:
        """Test get fix bundle tool has correct definition."""
        assert get_fix_bundle_tool.name == "gim_get_fix_bundle"
        assert "issue_id" in get_fix_bundle_tool.input_schema["properties"]
        assert "issue_id" in get_fix_bundle_tool.input_schema["required"]

    def test_submit_issue_tool_definition(self) -> None:
        """Test submit issue tool has correct definition."""
        assert submit_issue_tool.name == "gim_submit_issue"
        required = submit_issue_tool.input_schema["required"]
        assert "error_message" in required
        assert "root_cause" in required
        assert "fix_summary" in required
        assert "fix_steps" in required

    def test_confirm_fix_tool_definition(self) -> None:
        """Test confirm fix tool has correct definition."""
        assert confirm_fix_tool.name == "gim_confirm_fix"
        assert "issue_id" in confirm_fix_tool.input_schema["required"]
        assert "success" in confirm_fix_tool.input_schema["required"]

    def test_report_usage_tool_definition(self) -> None:
        """Test report usage tool has correct definition."""
        assert report_usage_tool.name == "gim_report_usage"
        assert "event_type" in report_usage_tool.input_schema["required"]


class TestBaseUtils:
    """Tests for base tool utilities."""

    def test_create_text_response_string(self) -> None:
        """Test text response with string content."""
        result = create_text_response("Hello")
        assert len(result) == 1
        assert result[0].text == "Hello"

    def test_create_text_response_dict(self) -> None:
        """Test text response with dict content."""
        result = create_text_response({"key": "value"})
        assert len(result) == 1
        parsed = json.loads(result[0].text)
        assert parsed["key"] == "value"

    def test_create_error_response(self) -> None:
        """Test error response creation."""
        result = create_error_response("Test error")
        assert len(result) == 1
        parsed = json.loads(result[0].text)
        assert parsed["error"] == "Test error"


class TestSearchIssuesTool:
    """Tests for search issues tool."""

    @pytest.mark.asyncio
    async def test_missing_error_message(self) -> None:
        """Test error when error_message is missing."""
        result = await search_execute({})
        assert len(result) == 1
        parsed = json.loads(result[0].text)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_search_with_no_results(self) -> None:
        """Test search returning no results."""
        with patch("src.tools.gim_search_issues.quick_sanitize") as mock_sanitize, \
             patch("src.tools.gim_search_issues.generate_embedding") as mock_embed, \
             patch("src.tools.gim_search_issues.search_similar_issues") as mock_search, \
             patch("src.tools.gim_search_issues.insert_record") as mock_insert:

            mock_sanitize.return_value = ("sanitized error", [])
            mock_embed.return_value = [0.0] * 768
            mock_search.return_value = []
            mock_insert.return_value = {}

            result = await search_execute({"error_message": "Test error"})
            parsed = json.loads(result[0].text)

            assert parsed["success"] is True
            assert parsed["results"] == []


class TestGetFixBundleTool:
    """Tests for get fix bundle tool."""

    @pytest.mark.asyncio
    async def test_missing_issue_id(self) -> None:
        """Test error when issue_id is missing."""
        result = await get_fix_execute({})
        parsed = json.loads(result[0].text)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_issue_not_found(self) -> None:
        """Test when issue is not found."""
        with patch("src.tools.gim_get_fix_bundle.get_record") as mock_get:
            mock_get.return_value = None

            result = await get_fix_execute({"issue_id": "nonexistent"})
            parsed = json.loads(result[0].text)
            assert "error" in parsed
            assert "not found" in parsed["error"]


class TestSubmitIssueTool:
    """Tests for submit issue tool."""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self) -> None:
        """Test error when required fields are missing."""
        result = await submit_execute({})
        parsed = json.loads(result[0].text)
        assert "error" in parsed

        result = await submit_execute({"error_message": "Test"})
        parsed = json.loads(result[0].text)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_submit_new_issue(self) -> None:
        """Test submitting a new master issue."""
        with patch("src.tools.gim_submit_issue.run_sanitization_pipeline") as mock_sanitize, \
             patch("src.tools.gim_submit_issue.quick_sanitize") as mock_quick, \
             patch("src.tools.gim_submit_issue.generate_issue_embeddings") as mock_embed, \
             patch("src.tools.gim_submit_issue.search_similar_issues") as mock_search, \
             patch("src.tools.gim_submit_issue.insert_record") as mock_insert, \
             patch("src.tools.gim_submit_issue.upsert_issue_vectors") as mock_upsert:

            # Mock sanitization result
            mock_result = AsyncMock()
            mock_result.sanitized_error = "Sanitized error"
            mock_result.sanitized_context = ""
            mock_result.sanitized_mre = ""
            mock_result.confidence_score = 0.9
            mock_result.llm_sanitization_used = True
            mock_result.warnings = []
            mock_sanitize.return_value = mock_result

            mock_quick.return_value = ("Sanitized text", [])
            mock_embed.return_value = {
                "error_signature": [0.0] * 768,
                "root_cause": [0.0] * 768,
                "fix_summary": [0.0] * 768,
            }
            mock_search.return_value = []  # No similar issues
            mock_insert.return_value = {"id": "test-id"}
            mock_upsert.return_value = None

            result = await submit_execute({
                "error_message": "Test error",
                "root_cause": "Test cause",
                "fix_summary": "Test fix",
                "fix_steps": ["Step 1", "Step 2"],
            })
            parsed = json.loads(result[0].text)

            assert parsed["success"] is True
            assert parsed["type"] == "master_issue"


class TestConfirmFixTool:
    """Tests for confirm fix tool."""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self) -> None:
        """Test error when required fields are missing."""
        result = await confirm_execute({})
        parsed = json.loads(result[0].text)
        assert "error" in parsed

        result = await confirm_execute({"issue_id": "test"})
        parsed = json.loads(result[0].text)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_issue_not_found(self) -> None:
        """Test when issue is not found."""
        with patch("src.tools.gim_confirm_fix.get_record") as mock_get:
            mock_get.return_value = None

            result = await confirm_execute({
                "issue_id": "nonexistent",
                "success": True,
            })
            parsed = json.loads(result[0].text)
            assert "error" in parsed

    @pytest.mark.asyncio
    async def test_confirm_success(self) -> None:
        """Test successful fix confirmation."""
        with patch("src.tools.gim_confirm_fix.get_record") as mock_get, \
             patch("src.tools.gim_confirm_fix.update_record") as mock_update, \
             patch("src.tools.gim_confirm_fix.insert_record") as mock_insert:

            mock_get.return_value = {
                "id": "test-id",
                "verification_count": 1,
            }
            mock_update.return_value = {}
            mock_insert.return_value = {}

            result = await confirm_execute({
                "issue_id": "test-id",
                "success": True,
            })
            parsed = json.loads(result[0].text)

            assert parsed["success"] is True
            assert parsed["fix_succeeded"] is True


class TestReportUsageTool:
    """Tests for report usage tool."""

    @pytest.mark.asyncio
    async def test_missing_event_type(self) -> None:
        """Test error when event_type is missing."""
        result = await report_execute({})
        parsed = json.loads(result[0].text)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_invalid_event_type(self) -> None:
        """Test error for invalid event type."""
        result = await report_execute({"event_type": "invalid"})
        parsed = json.loads(result[0].text)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_valid_event(self) -> None:
        """Test reporting a valid event."""
        with patch("src.tools.gim_report_usage.insert_record") as mock_insert:
            mock_insert.return_value = {}

            result = await report_execute({"event_type": "search"})
            parsed = json.loads(result[0].text)

            assert parsed["success"] is True
            assert parsed["event_type"] == "search"
