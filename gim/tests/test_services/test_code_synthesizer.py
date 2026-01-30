"""Tests for code synthesizer service."""

import json

import pytest
from unittest.mock import MagicMock, patch

try:
    from src.services.sanitization.code_synthesizer import (
        CodeSynthesisResult,
        _strip_markdown_code_blocks,
        synthesize_reproduction_code,
        synthesize_fix_code,
        synthesize_fix_steps_with_code,
        synthesize_patch_diff,
        run_code_synthesis,
    )
except ImportError:
    pytest.skip(
        "Required dependencies not installed (google-genai)",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# CodeSynthesisResult dataclass
# ---------------------------------------------------------------------------


class TestCodeSynthesisResult:
    """Tests for CodeSynthesisResult dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        result = CodeSynthesisResult()
        assert result.reproduction_snippet == ""
        assert result.fix_snippet == ""
        assert result.synthesized_fix_steps == []
        assert result.patch_diff == ""
        assert result.success is True
        assert result.error is None

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        result = CodeSynthesisResult(
            reproduction_snippet="repro()",
            fix_snippet="# BEFORE\n# AFTER",
            synthesized_fix_steps=["step 1", "step 2"],
            patch_diff="--- a/file\n+++ b/file",
            success=False,
            error="something failed",
        )
        assert result.reproduction_snippet == "repro()"
        assert result.fix_snippet == "# BEFORE\n# AFTER"
        assert result.synthesized_fix_steps == ["step 1", "step 2"]
        assert result.patch_diff == "--- a/file\n+++ b/file"
        assert result.success is False
        assert result.error == "something failed"

    def test_mutable_default_not_shared(self) -> None:
        """Test that mutable default list is not shared between instances."""
        result1 = CodeSynthesisResult()
        result2 = CodeSynthesisResult()
        result1.synthesized_fix_steps.append("step")
        assert result2.synthesized_fix_steps == []


# ---------------------------------------------------------------------------
# _strip_markdown_code_blocks helper
# ---------------------------------------------------------------------------


class TestStripMarkdownCodeBlocks:
    """Tests for the _strip_markdown_code_blocks helper."""

    def test_no_code_blocks(self) -> None:
        """Test text without code blocks is returned unchanged."""
        text = "just plain text"
        assert _strip_markdown_code_blocks(text) == "just plain text"

    def test_strips_python_code_block(self) -> None:
        """Test stripping ```python fenced code block."""
        text = "```python\nprint('hello')\n```"
        assert _strip_markdown_code_blocks(text) == "print('hello')"

    def test_strips_bare_code_block(self) -> None:
        """Test stripping bare ``` fenced code block."""
        text = "```\nsome code\n```"
        assert _strip_markdown_code_blocks(text) == "some code"

    def test_empty_string(self) -> None:
        """Test empty string is returned as-is."""
        assert _strip_markdown_code_blocks("") == ""

    def test_none_input(self) -> None:
        """Test None input is returned as-is."""
        assert _strip_markdown_code_blocks(None) is None

    def test_multiline_code_block(self) -> None:
        """Test stripping multi-line code block."""
        text = "```python\nline1\nline2\nline3\n```"
        assert _strip_markdown_code_blocks(text) == "line1\nline2\nline3"

    def test_text_not_starting_with_backticks(self) -> None:
        """Test text not starting with backticks is unchanged."""
        text = "some text\n```\nblock\n```"
        assert _strip_markdown_code_blocks(text) == "some text\n```\nblock\n```"


# ---------------------------------------------------------------------------
# synthesize_reproduction_code
# ---------------------------------------------------------------------------


class TestSynthesizeReproductionCode:
    """Tests for synthesize_reproduction_code with mocked API."""

    @pytest.mark.asyncio
    async def test_returns_synthesized_code(self) -> None:
        """Test successful reproduction code synthesis."""
        mock_response = MagicMock()
        mock_response.text = "# This triggers the error\nraise ValueError('oops')"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await synthesize_reproduction_code(
                error_message="ValueError: oops",
                error_context="in function foo",
                code_snippet="def foo(): raise ValueError('oops')",
            )

            assert "This triggers the error" in result
            mock_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_strips_markdown_from_response(self) -> None:
        """Test that markdown code blocks are stripped from response."""
        mock_response = MagicMock()
        mock_response.text = "```python\nrepro_code()\n```"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await synthesize_reproduction_code(
                error_message="err",
                error_context="ctx",
                code_snippet="code",
            )

            assert result == "repro_code()"
            assert "```" not in result

    @pytest.mark.asyncio
    async def test_api_error_returns_empty_string(self) -> None:
        """Test that API errors return empty string."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await synthesize_reproduction_code(
                error_message="err",
                error_context="ctx",
                code_snippet="code",
            )

            assert result == ""


# ---------------------------------------------------------------------------
# synthesize_fix_code
# ---------------------------------------------------------------------------


class TestSynthesizeFixCode:
    """Tests for synthesize_fix_code with mocked API."""

    @pytest.mark.asyncio
    async def test_returns_fix_code(self) -> None:
        """Test successful fix code synthesis."""
        mock_response = MagicMock()
        mock_response.text = "# BEFORE (broken)\nx = None\n# AFTER (fixed)\nx = 0"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await synthesize_fix_code(
                error_message="TypeError: NoneType",
                root_cause="Variable not initialized",
                fix_steps=["Initialize variable to 0"],
                code_changes=[{"before": "x = None", "after": "x = 0"}],
            )

            assert "BEFORE" in result
            assert "AFTER" in result
            mock_client.models.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_empty_fix_steps(self) -> None:
        """Test synthesis with empty fix steps."""
        mock_response = MagicMock()
        mock_response.text = "# BEFORE (broken)\n# AFTER (fixed)"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await synthesize_fix_code(
                error_message="err",
                root_cause="cause",
                fix_steps=[],
                code_changes=[],
            )

            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_api_error_returns_empty_string(self) -> None:
        """Test that API errors return empty string."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("timeout")

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await synthesize_fix_code(
                error_message="err",
                root_cause="cause",
                fix_steps=["step"],
                code_changes=[],
            )

            assert result == ""


# ---------------------------------------------------------------------------
# synthesize_fix_steps_with_code
# ---------------------------------------------------------------------------


class TestSynthesizeFixStepsWithCode:
    """Tests for synthesize_fix_steps_with_code with mocked API."""

    @pytest.mark.asyncio
    async def test_returns_enriched_steps(self) -> None:
        """Test successful enrichment of fix steps."""
        enriched = [
            "Add null check\n```\nif x is None:\n    return\n```",
            "Handle error\n```\ntry:\n    process()\nexcept:\n    log()\n```",
        ]
        mock_response = MagicMock()
        mock_response.text = json.dumps(enriched)

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await synthesize_fix_steps_with_code(
                fix_steps=["Add null check", "Handle error"],
                code_changes=[{"before": "process()", "after": "try:\n    process()"}],
            )

            assert len(result) == 2
            assert "null check" in result[0]

    @pytest.mark.asyncio
    async def test_empty_fix_steps_returns_empty_list(self) -> None:
        """Test that empty fix steps returns empty list without calling LLM."""
        result = await synthesize_fix_steps_with_code(
            fix_steps=[],
            code_changes=[],
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_json_parse_error_returns_original_steps(self) -> None:
        """Test that JSON parse errors fall back to original steps."""
        mock_response = MagicMock()
        mock_response.text = "this is not json"

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            original = ["step 1", "step 2"]
            result = await synthesize_fix_steps_with_code(
                fix_steps=original,
                code_changes=[],
            )

            assert result == original

    @pytest.mark.asyncio
    async def test_unexpected_format_returns_original_steps(self) -> None:
        """Test that non-list JSON falls back to original steps."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"not": "a list"})

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            original = ["step a"]
            result = await synthesize_fix_steps_with_code(
                fix_steps=original,
                code_changes=[],
            )

            assert result == original

    @pytest.mark.asyncio
    async def test_api_error_returns_original_steps(self) -> None:
        """Test that API errors fall back to original steps."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API down")

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            original = ["original step"]
            result = await synthesize_fix_steps_with_code(
                fix_steps=original,
                code_changes=[],
            )

            assert result == original

    @pytest.mark.asyncio
    async def test_non_string_list_returns_original_steps(self) -> None:
        """Test that a list of non-strings falls back to original steps."""
        mock_response = MagicMock()
        mock_response.text = json.dumps([1, 2, 3])

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            original = ["step x"]
            result = await synthesize_fix_steps_with_code(
                fix_steps=original,
                code_changes=[],
            )

            assert result == original


# ---------------------------------------------------------------------------
# synthesize_patch_diff (deterministic, no mocks needed)
# ---------------------------------------------------------------------------


class TestSynthesizePatchDiff:
    """Tests for the deterministic synthesize_patch_diff function."""

    def test_empty_code_changes(self) -> None:
        """Test empty code changes returns empty string."""
        assert synthesize_patch_diff([]) == ""

    def test_single_change_produces_diff(self) -> None:
        """Test a single before/after change produces valid unified diff."""
        changes = [
            {
                "file": "app.py",
                "before": "x = None\n",
                "after": "x = 0\n",
            }
        ]
        result = synthesize_patch_diff(changes)
        assert "--- a/app.py" in result
        assert "+++ b/app.py" in result
        assert "-x = None" in result
        assert "+x = 0" in result

    def test_multiple_changes(self) -> None:
        """Test multiple changes produce concatenated diffs."""
        changes = [
            {"file": "a.py", "before": "old_a\n", "after": "new_a\n"},
            {"file": "b.py", "before": "old_b\n", "after": "new_b\n"},
        ]
        result = synthesize_patch_diff(changes)
        assert "--- a/a.py" in result
        assert "--- a/b.py" in result

    def test_missing_file_key_uses_default_label(self) -> None:
        """Test that missing 'file' key uses change_N default label."""
        changes = [{"before": "old\n", "after": "new\n"}]
        result = synthesize_patch_diff(changes)
        assert "--- a/change_1" in result
        assert "+++ b/change_1" in result

    def test_both_before_and_after_empty_skipped(self) -> None:
        """Test that changes with empty before and after are skipped."""
        changes = [{"before": "", "after": ""}]
        result = synthesize_patch_diff(changes)
        assert result == ""

    def test_only_before_present(self) -> None:
        """Test change with only 'before' (deletion)."""
        changes = [{"file": "del.py", "before": "deleted_line\n", "after": ""}]
        result = synthesize_patch_diff(changes)
        assert "--- a/del.py" in result
        assert "-deleted_line" in result

    def test_only_after_present(self) -> None:
        """Test change with only 'after' (addition)."""
        changes = [{"file": "add.py", "before": "", "after": "new_line\n"}]
        result = synthesize_patch_diff(changes)
        assert "+++ b/add.py" in result
        assert "+new_line" in result

    def test_no_before_or_after_keys(self) -> None:
        """Test change dict without before/after keys is skipped."""
        changes = [{"file": "noop.py"}]
        result = synthesize_patch_diff(changes)
        assert result == ""

    def test_identical_before_and_after(self) -> None:
        """Test identical before and after produces empty diff."""
        changes = [{"file": "same.py", "before": "same\n", "after": "same\n"}]
        result = synthesize_patch_diff(changes)
        # unified_diff produces empty output for identical inputs
        assert result.strip() == ""


# ---------------------------------------------------------------------------
# run_code_synthesis (orchestrator)
# ---------------------------------------------------------------------------


class TestRunCodeSynthesis:
    """Tests for run_code_synthesis orchestrator."""

    @pytest.mark.asyncio
    async def test_all_steps_succeed(self) -> None:
        """Test orchestrator when all synthesis steps succeed."""
        mock_response_repro = MagicMock()
        mock_response_repro.text = "repro_code()"

        mock_response_fix = MagicMock()
        mock_response_fix.text = "# BEFORE\n# AFTER"

        mock_response_steps = MagicMock()
        mock_response_steps.text = json.dumps(["enriched step 1"])

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            mock_response_repro,
            mock_response_fix,
            mock_response_steps,
        ]

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await run_code_synthesis(
                error_message="ValueError",
                error_context="in function foo",
                code_snippet="foo()",
                root_cause="missing check",
                fix_steps=["add check"],
                code_changes=[
                    {"file": "foo.py", "before": "x = None\n", "after": "x = 0\n"},
                ],
            )

            assert result.success is True
            assert result.error is None
            assert result.reproduction_snippet == "repro_code()"
            assert result.fix_snippet == "# BEFORE\n# AFTER"
            assert result.synthesized_fix_steps == ["enriched step 1"]
            assert "--- a/foo.py" in result.patch_diff

    @pytest.mark.asyncio
    async def test_llm_failures_are_non_blocking(self) -> None:
        """Test that LLM failures do not block the orchestrator."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("LLM down")

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await run_code_synthesis(
                error_message="err",
                fix_steps=["original step"],
                code_changes=[
                    {"file": "f.py", "before": "a\n", "after": "b\n"},
                ],
            )

            # LLM steps should fail gracefully
            assert result.reproduction_snippet == ""
            assert result.fix_snippet == ""
            # Fix steps should fall back to originals
            assert result.synthesized_fix_steps == ["original step"]
            # Deterministic diff should always succeed
            assert "--- a/f.py" in result.patch_diff
            # Should report partial failure
            assert result.success is False
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_default_parameters(self) -> None:
        """Test orchestrator with all default parameters."""
        mock_response = MagicMock()
        mock_response.text = ""

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await run_code_synthesis()

            assert result.patch_diff == ""
            assert result.synthesized_fix_steps == []

    @pytest.mark.asyncio
    async def test_patch_diff_always_runs(self) -> None:
        """Test that patch diff is generated even when LLM steps fail."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("fail")

        with patch(
            "src.services.sanitization.code_synthesizer._get_genai_client",
            return_value=mock_client,
        ), patch(
            "src.services.sanitization.code_synthesizer.get_settings",
        ) as mock_settings:
            mock_settings.return_value.llm_model = "gemini-2.5-flash"

            result = await run_code_synthesis(
                code_changes=[
                    {"file": "x.py", "before": "old\n", "after": "new\n"},
                ],
            )

            assert "--- a/x.py" in result.patch_diff
            assert "+++ b/x.py" in result.patch_diff
