"""Tests for the issue filter module.

Pure logic tests — no mocks needed.
"""

import pytest

from src.crawler.issue_filter import (
    EXCLUDED_LABELS,
    MIN_PR_ADDITIONS,
    _has_error_pattern,
    filter_issue,
)


class TestFilterIssue:
    """Tests for filter_issue function."""

    def _valid_kwargs(self, **overrides: object) -> dict:
        """Helper to build valid filter kwargs with optional overrides.

        Args:
            **overrides: Fields to override in the default kwargs.

        Returns:
            dict: Filter kwargs.
        """
        defaults = {
            "state_reason": "completed",
            "has_merged_pr": True,
            "issue_labels": ["bug"],
            "issue_body": "Got TypeError: 'NoneType' has no attribute 'get'",
            "pr_additions": 10,
        }
        defaults.update(overrides)
        return defaults

    def test_valid_issue_passes(self) -> None:
        """Issue with all valid signals passes the filter."""
        passes, reason = filter_issue(**self._valid_kwargs())
        assert passes is True
        assert reason is None

    def test_state_reason_not_completed_drops(self) -> None:
        """Issue with state_reason != 'completed' is dropped."""
        passes, reason = filter_issue(**self._valid_kwargs(state_reason="not_planned"))
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_state_reason_none_drops(self) -> None:
        """Issue with state_reason=None is dropped."""
        passes, reason = filter_issue(**self._valid_kwargs(state_reason=None))
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_no_merged_pr_drops(self) -> None:
        """Issue without linked merged PR is dropped."""
        passes, reason = filter_issue(**self._valid_kwargs(has_merged_pr=False))
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_excluded_label_enhancement_drops(self) -> None:
        """Issue with 'enhancement' label is dropped."""
        passes, reason = filter_issue(
            **self._valid_kwargs(issue_labels=["enhancement", "bug"])
        )
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_excluded_label_documentation_drops(self) -> None:
        """Issue with 'documentation' label is dropped."""
        passes, reason = filter_issue(
            **self._valid_kwargs(issue_labels=["documentation"])
        )
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_excluded_label_case_insensitive(self) -> None:
        """Label matching is case-insensitive."""
        passes, reason = filter_issue(
            **self._valid_kwargs(issue_labels=["Enhancement"])
        )
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_excluded_label_feature_request_drops(self) -> None:
        """Issue with 'feature-request' label is dropped."""
        passes, reason = filter_issue(
            **self._valid_kwargs(issue_labels=["feature-request"])
        )
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_excluded_label_question_drops(self) -> None:
        """Issue with 'question' label is dropped."""
        passes, reason = filter_issue(
            **self._valid_kwargs(issue_labels=["question"])
        )
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_no_error_pattern_drops(self) -> None:
        """Issue without error pattern in body is dropped."""
        passes, reason = filter_issue(
            **self._valid_kwargs(issue_body="Please add support for feature X")
        )
        assert passes is False
        assert reason == "NO_ERROR_MESSAGE"

    def test_empty_body_drops(self) -> None:
        """Issue with empty body is dropped."""
        passes, reason = filter_issue(**self._valid_kwargs(issue_body=""))
        assert passes is False
        assert reason == "NO_ERROR_MESSAGE"

    def test_none_body_drops(self) -> None:
        """Issue with None body is dropped."""
        passes, reason = filter_issue(**self._valid_kwargs(issue_body=None))
        assert passes is False
        assert reason == "NO_ERROR_MESSAGE"

    def test_low_pr_additions_drops(self) -> None:
        """Issue with < MIN_PR_ADDITIONS is dropped."""
        passes, reason = filter_issue(
            **self._valid_kwargs(pr_additions=MIN_PR_ADDITIONS - 1)
        )
        assert passes is False
        assert reason == "NOT_A_FIX"

    def test_exact_min_pr_additions_passes(self) -> None:
        """Issue with exactly MIN_PR_ADDITIONS passes."""
        passes, reason = filter_issue(
            **self._valid_kwargs(pr_additions=MIN_PR_ADDITIONS)
        )
        assert passes is True
        assert reason is None

    def test_non_excluded_labels_pass(self) -> None:
        """Issue with non-excluded labels passes."""
        passes, reason = filter_issue(
            **self._valid_kwargs(issue_labels=["bug", "p1", "regression"])
        )
        assert passes is True
        assert reason is None

    def test_empty_labels_pass(self) -> None:
        """Issue with no labels passes."""
        passes, reason = filter_issue(**self._valid_kwargs(issue_labels=[]))
        assert passes is True
        assert reason is None


class TestHasErrorPattern:
    """Tests for _has_error_pattern function."""

    def test_traceback_detected(self) -> None:
        """Python traceback is detected."""
        text = "Traceback (most recent call last):\n  File ..."
        assert _has_error_pattern(text) is True

    def test_type_error_detected(self) -> None:
        """TypeError is detected."""
        assert _has_error_pattern("TypeError: cannot unpack non-iterable") is True

    def test_value_error_detected(self) -> None:
        """ValueError is detected."""
        assert _has_error_pattern("ValueError: invalid literal") is True

    def test_attribute_error_detected(self) -> None:
        """AttributeError is detected."""
        assert _has_error_pattern("AttributeError: 'NoneType' has no attr") is True

    def test_import_error_detected(self) -> None:
        """ImportError is detected."""
        assert _has_error_pattern("ImportError: cannot import name 'foo'") is True

    def test_module_not_found_detected(self) -> None:
        """ModuleNotFoundError is detected."""
        assert _has_error_pattern("ModuleNotFoundError: No module named 'x'") is True

    def test_npm_error_detected(self) -> None:
        """npm ERR! is detected."""
        assert _has_error_pattern("npm ERR! code ENOENT") is True

    def test_failed_to_detected(self) -> None:
        """'failed to' pattern is detected."""
        assert _has_error_pattern("failed to compile module") is True

    def test_panic_detected(self) -> None:
        """Go panic is detected."""
        assert _has_error_pattern("panic: runtime error: invalid memory") is True

    def test_error_in_code_block_detected(self) -> None:
        """Error inside markdown code block is detected."""
        text = "```\nError: something went wrong\n```"
        assert _has_error_pattern(text) is True

    def test_generic_error_detected(self) -> None:
        """Generic 'Error:' is detected."""
        assert _has_error_pattern("Error: connection refused") is True

    def test_case_insensitive_error(self) -> None:
        """'error:' in lowercase is detected."""
        assert _has_error_pattern("error: something broke") is True

    def test_no_error_pattern(self) -> None:
        """Normal text without error patterns returns False."""
        assert _has_error_pattern("Please add support for dark mode") is False

    def test_empty_string(self) -> None:
        """Empty string has no error pattern."""
        assert _has_error_pattern("") is False

    def test_syntax_error_detected(self) -> None:
        """SyntaxError is detected."""
        assert _has_error_pattern("SyntaxError: invalid syntax") is True

    def test_exception_keyword_detected(self) -> None:
        """Generic 'Exception:' is detected."""
        assert _has_error_pattern("Exception: unexpected state") is True
