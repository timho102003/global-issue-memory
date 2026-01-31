"""Multi-signal filter pipeline for GitHub issues.

Filters crawled issues to identify those most likely to contain
globally useful bug fix information for GIM.
"""

import re
from typing import Optional, Tuple

from src.logging_config import get_logger

logger = get_logger("crawler.issue_filter")

# Labels that indicate the issue is not a bug fix
EXCLUDED_LABELS = frozenset({
    "enhancement",
    "feature",
    "feature-request",
    "feature request",
    "question",
    "documentation",
    "docs",
    "wontfix",
    "won't fix",
    "duplicate",
    "invalid",
    "good first issue",
    "help wanted",
    "hacktoberfest",
})

# Regex patterns that indicate an error message in issue body
ERROR_PATTERNS = [
    re.compile(r"Error:", re.IGNORECASE),
    re.compile(r"Exception:", re.IGNORECASE),
    re.compile(r"Traceback\s*\(most recent call last\)", re.IGNORECASE),
    re.compile(
        r"(TypeError|ValueError|KeyError|AttributeError|ImportError|"
        r"RuntimeError|IndexError|NameError|FileNotFoundError|"
        r"ModuleNotFoundError|SyntaxError|OSError|IOError|"
        r"ConnectionError|TimeoutError|PermissionError)",
    ),
    re.compile(r"(FAILED|FAILURE|failed to)\b", re.IGNORECASE),
    re.compile(r"(panic:|fatal error:)", re.IGNORECASE),
    re.compile(r"npm ERR!", re.IGNORECASE),
    re.compile(r"```[\s\S]*?(error|exception|traceback|failed)[\s\S]*?```", re.IGNORECASE),
]

# Minimum PR additions to be considered a non-trivial code change
MIN_PR_ADDITIONS = 5


def filter_issue(
    state_reason: Optional[str],
    has_merged_pr: bool,
    issue_labels: list,
    issue_body: Optional[str],
    pr_additions: int = 0,
) -> Tuple[bool, Optional[str]]:
    """Apply multi-signal filter to determine if an issue is a valid bug fix.

    Args:
        state_reason: GitHub's state_reason for the closed issue.
        has_merged_pr: Whether the issue has a linked merged PR.
        issue_labels: List of label name strings on the issue.
        issue_body: The issue body text.
        pr_additions: Number of line additions in the linked PR.

    Returns:
        Tuple of (passes_filter, drop_reason).
        If passes_filter is True, drop_reason is None.
        If passes_filter is False, drop_reason explains why.
    """
    # 1. state_reason must be "completed"
    if state_reason != "completed":
        logger.debug(f"Filtered: state_reason={state_reason} (not 'completed')")
        return False, "NOT_A_FIX"

    # 2. Must have a linked merged PR
    if not has_merged_pr:
        logger.debug("Filtered: no linked merged PR")
        return False, "NOT_A_FIX"

    # 3. No excluded labels
    normalized_labels = {label.lower().strip() for label in issue_labels}
    excluded_found = normalized_labels & EXCLUDED_LABELS
    if excluded_found:
        logger.debug(f"Filtered: excluded labels {excluded_found}")
        return False, "NOT_A_FIX"

    # 4. Must have an error pattern in the issue body
    if not issue_body or not _has_error_pattern(issue_body):
        logger.debug("Filtered: no error pattern in issue body")
        return False, "NO_ERROR_MESSAGE"

    # 5. PR must have non-trivial code changes
    if pr_additions < MIN_PR_ADDITIONS:
        logger.debug(f"Filtered: PR additions={pr_additions} < {MIN_PR_ADDITIONS}")
        return False, "NOT_A_FIX"

    return True, None


def _has_error_pattern(text: str) -> bool:
    """Check if text contains any recognized error pattern.

    Args:
        text: Text to search for error patterns.

    Returns:
        bool: True if any error pattern is found.
    """
    for pattern in ERROR_PATTERNS:
        if pattern.search(text):
            return True
    return False
