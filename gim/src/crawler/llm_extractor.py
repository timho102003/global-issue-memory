"""LLM-based extraction and quality scoring using Gemini.

Extracts structured error/fix data from raw GitHub issue content
and scores its global usefulness for the GIM knowledge base.
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import List, Optional

from google import genai
from google.genai import errors as genai_errors

from src.config import get_settings
from src.logging_config import get_logger

logger = get_logger("crawler.llm_extractor")

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


@dataclass
class ExtractionResult:
    """Result of LLM issue extraction.

    Attributes:
        error_message: Extracted error message.
        root_cause: Extracted root cause explanation.
        fix_summary: Extracted fix summary.
        fix_steps: List of fix step strings.
        language: Detected programming language.
        framework: Detected framework.
        confidence: LLM confidence in extraction (0-1).
        success: Whether extraction was successful.
        error: Error message if extraction failed.
    """

    error_message: str = ""
    root_cause: str = ""
    fix_summary: str = ""
    fix_steps: List[str] = field(default_factory=list)
    language: Optional[str] = None
    framework: Optional[str] = None
    confidence: float = 0.0
    success: bool = True
    error: Optional[str] = None


EXTRACT_PROMPT = """You are an expert at analyzing GitHub issues and extracting structured bug fix information.

Given a GitHub issue and its linked pull request, extract the following information as JSON:

**Issue Title:** {issue_title}

**Issue Body:**
{issue_body}

**Issue Comments (most relevant):**
{comments}

**PR Body:**
{pr_body}

**PR Diff Summary:**
{pr_diff_summary}

Extract the following JSON structure. Be precise and concise:
{{
    "error_message": "The exact or closest error message/traceback from the issue. If no clear error, write 'NOT_FOUND'.",
    "root_cause": "A clear explanation of WHY the error occurs (not just WHAT). 1-3 sentences.",
    "fix_summary": "Brief description of the solution. 1-2 sentences.",
    "fix_steps": ["Step 1...", "Step 2...", "..."],
    "language": "Primary programming language (e.g. 'python', 'javascript', 'typescript', 'go', 'rust') or null",
    "framework": "Primary framework/library (e.g. 'flask', 'react', 'fastapi', 'express') or null",
    "confidence": 0.0
}}

Rules for confidence score:
- 0.9-1.0: Clear error message, clear root cause, clear fix with code changes
- 0.7-0.8: Good error message, reasonable root cause, fix steps present
- 0.5-0.6: Partial error info, some root cause reasoning, basic fix
- 0.3-0.4: Vague error, unclear root cause, minimal fix info
- 0.0-0.2: Cannot extract meaningful information

Output ONLY valid JSON, no markdown code blocks, no explanations."""

QUALITY_SCORE_PROMPT = """Rate the global usefulness of this bug fix for other developers on a scale of 0.0 to 1.0.

**Error:** {error_message}
**Root Cause:** {root_cause}
**Fix Summary:** {fix_summary}
**Language:** {language}
**Framework:** {framework}

Scoring criteria:
- 0.9-1.0: Universally applicable — common error in popular library, affects many users
- 0.7-0.8: Broadly useful — common pattern, multiple projects could hit this
- 0.5-0.6: Moderately useful — specific but well-documented fix for a known issue
- 0.3-0.4: Narrow applicability — very specific configuration or edge case
- 0.0-0.2: Not useful — project-specific, trivial, or not a real fix

Output ONLY a single float number between 0.0 and 1.0, nothing else."""


def _get_genai_client() -> genai.Client:
    """Get configured Gemini client.

    Returns:
        genai.Client: Configured Gemini client.
    """
    settings = get_settings()
    return genai.Client(api_key=settings.google_api_key.get_secret_value())


def _truncate(text: Optional[str], max_chars: int = 5000) -> str:
    """Truncate text to max characters with indicator.

    Args:
        text: Text to truncate.
        max_chars: Maximum character count.

    Returns:
        str: Truncated text.
    """
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (truncated)"


def _format_comments(comments: list, max_comments: int = 10) -> str:
    """Format comments list into readable text.

    Args:
        comments: List of comment dicts with 'author' and 'body'.
        max_comments: Maximum number of comments to include.

    Returns:
        str: Formatted comments string.
    """
    if not comments:
        return "No comments."

    formatted = []
    for c in comments[:max_comments]:
        author = c.get("author", "unknown")
        body = _truncate(c.get("body", ""), 1000)
        formatted.append(f"@{author}: {body}")

    return "\n\n".join(formatted)


def _is_retryable(error: Exception) -> bool:
    """Check if a Gemini API error is retryable.

    Args:
        error: The exception to check.

    Returns:
        bool: True if the error is transient and should be retried.
    """
    if isinstance(error, genai_errors.APIError):
        return error.code in (429, 503)
    error_str = str(error).lower()
    return "503" in error_str or "overloaded" in error_str or "unavailable" in error_str


async def _call_genai_with_retry(
    client: genai.Client,
    model: str,
    contents: str,
    max_retries: int = MAX_RETRIES,
    base_delay: float = RETRY_BASE_DELAY,
) -> str:
    """Call Gemini API with exponential backoff retry.

    Args:
        client: Gemini client instance.
        model: Model name to use.
        contents: Prompt contents.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.

    Returns:
        str: Raw response text from the model.

    Raises:
        Exception: The last error if all retries are exhausted.
    """
    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=contents,
            )
            return response.text.strip()
        except Exception as e:
            last_error = e
            if attempt < max_retries and _is_retryable(e):
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Gemini API error (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)
            else:
                raise
    raise last_error  # type: ignore[misc]


async def extract_issue_data(
    issue_title: str,
    issue_body: Optional[str],
    comments: list,
    pr_body: Optional[str],
    pr_diff_summary: Optional[str],
) -> ExtractionResult:
    """Extract structured error/fix data from a GitHub issue using Gemini.

    Args:
        issue_title: Title of the GitHub issue.
        issue_body: Body text of the issue.
        comments: List of comment dicts.
        pr_body: Body text of the linked PR.
        pr_diff_summary: Summary of PR diff changes.

    Returns:
        ExtractionResult: Extracted data or error.
    """
    try:
        settings = get_settings()
        client = _get_genai_client()

        prompt = EXTRACT_PROMPT.format(
            issue_title=issue_title or "Untitled",
            issue_body=_truncate(issue_body),
            comments=_format_comments(comments),
            pr_body=_truncate(pr_body, 3000),
            pr_diff_summary=_truncate(pr_diff_summary, 2000),
        )

        raw_text = await _call_genai_with_retry(
            client=client,
            model=settings.llm_model,
            contents=prompt,
        )

        # Strip markdown code blocks if present
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_text = "\n".join(lines)

        data = json.loads(raw_text)

        error_message = data.get("error_message", "")
        confidence = float(data.get("confidence", 0.0))

        # Validate extraction
        if error_message == "NOT_FOUND" or confidence < 0.3:
            return ExtractionResult(
                success=False,
                error="Extraction failed: no clear error message or low confidence",
                confidence=confidence,
            )

        return ExtractionResult(
            error_message=error_message,
            root_cause=data.get("root_cause", ""),
            fix_summary=data.get("fix_summary", ""),
            fix_steps=data.get("fix_steps", []),
            language=data.get("language"),
            framework=data.get("framework"),
            confidence=confidence,
            success=True,
        )

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error during extraction: {e}")
        return ExtractionResult(
            success=False,
            error=f"Invalid JSON from LLM: {e}",
        )
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return ExtractionResult(
            success=False,
            error=str(e),
        )


async def score_quality(
    error_message: str,
    root_cause: str,
    fix_summary: str,
    language: Optional[str] = None,
    framework: Optional[str] = None,
) -> float:
    """Score the global usefulness of an extracted fix using Gemini.

    Args:
        error_message: Extracted error message.
        root_cause: Extracted root cause.
        fix_summary: Extracted fix summary.
        language: Detected programming language.
        framework: Detected framework.

    Returns:
        float: Quality score between 0.0 and 1.0.
    """
    try:
        settings = get_settings()
        client = _get_genai_client()

        prompt = QUALITY_SCORE_PROMPT.format(
            error_message=_truncate(error_message, 2000),
            root_cause=_truncate(root_cause, 1000),
            fix_summary=_truncate(fix_summary, 1000),
            language=language or "unknown",
            framework=framework or "unknown",
        )

        raw_text = await _call_genai_with_retry(
            client=client,
            model=settings.llm_model,
            contents=prompt,
        )
        score = float(raw_text)

        # Clamp to valid range
        return max(0.0, min(1.0, score))

    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse quality score: {e}")
        return 0.0
    except Exception as e:
        logger.error(f"Quality scoring error: {e}")
        return 0.0
