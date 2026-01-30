"""LLM-based sanitization using Gemini for intelligent code rewriting."""

from dataclasses import dataclass, field
from typing import List, Optional

from google import genai

from src.config import get_settings


@dataclass
class LLMSanitizationResult:
    """Result of LLM-based sanitization.

    Attributes:
        original_text: The original text before sanitization.
        sanitized_text: The sanitized/rewritten text.
        changes_made: List of changes that were made.
        success: Whether sanitization was successful.
        error: Error message if sanitization failed.
    """

    original_text: str = ""
    sanitized_text: str = ""
    changes_made: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


# Prompt templates for different sanitization tasks
SANITIZE_CODE_PROMPT = """You are a code sanitization expert. Your task is to rewrite the following code snippet to create a minimal, privacy-safe, reproducible example.

**Requirements:**
1. Remove ALL secrets, API keys, tokens, passwords, and credentials
2. Replace ALL personal information (emails, names, file paths with usernames)
3. Replace domain-specific class/function/variable names with generic ones:
   - UserService → ServiceA
   - CustomerOrder → ItemA
   - process_payment → process_item
   - john_doe → user_a
4. Keep the code structure that demonstrates the error
5. Preserve import statements but remove internal/private package imports
6. Add a comment "# ERROR OCCURS HERE" at the error location if identifiable
7. Keep the code minimal (10-50 lines ideally)

**Original Code:**
<user_code>
{code}
</user_code>

**Error Context (if provided):**
<error_context>
{error_context}
</error_context>

**Output ONLY the sanitized code, nothing else. No explanations, no markdown code blocks, just the raw code:**
"""

SANITIZE_ERROR_MESSAGE_PROMPT = """Sanitize the following error message by:
1. Removing any file paths that contain usernames (e.g., /Users/john/ → /path/to/)
2. Removing any email addresses (replace with user@example.com)
3. Removing any IP addresses (replace with 0.0.0.0)
4. Removing any API keys, tokens, or secrets
5. Keeping the technical error information intact

**Original Error:**
<user_error>
{error_message}
</user_error>

**Output ONLY the sanitized error message, nothing else:**
"""

SANITIZE_CONTEXT_PROMPT = """Sanitize the following context/description by:
1. Removing any personal information (names, emails, usernames)
2. Removing any internal company/project names
3. Removing any secrets or credentials
4. Keeping the technical description intact

**Original Context:**
<user_context>
{context}
</user_context>

**Output ONLY the sanitized context, nothing else:**
"""


def _get_genai_client() -> genai.Client:
    """Get configured Gemini client.

    Returns:
        genai.Client: Configured Gemini client.
    """
    settings = get_settings()
    return genai.Client(api_key=settings.google_api_key.get_secret_value())


async def sanitize_code_with_llm(
    code: str,
    error_context: Optional[str] = None,
) -> LLMSanitizationResult:
    """Sanitize code snippet using Gemini LLM.

    This function uses Gemini to intelligently rewrite code,
    removing sensitive information while preserving the error-triggering
    structure.

    Args:
        code: The code snippet to sanitize.
        error_context: Optional error context for better understanding.

    Returns:
        LLMSanitizationResult: The sanitization result.
    """
    if not code or not code.strip():
        return LLMSanitizationResult(
            original_text=code,
            sanitized_text="",
            success=True,
        )

    try:
        settings = get_settings()
        client = _get_genai_client()

        prompt = SANITIZE_CODE_PROMPT.format(
            code=code,
            error_context=error_context or "Not provided",
        )

        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )

        sanitized = response.text.strip()

        # Remove markdown code blocks if present
        if sanitized.startswith("```"):
            lines = sanitized.split("\n")
            # Remove first line (```python or ```)
            lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sanitized = "\n".join(lines)

        changes = []
        if code != sanitized:
            changes.append("Code rewritten by LLM for privacy")

        return LLMSanitizationResult(
            original_text=code,
            sanitized_text=sanitized,
            changes_made=changes,
            success=True,
        )

    except Exception as e:
        return LLMSanitizationResult(
            original_text=code,
            sanitized_text="",  # Return empty on failure to avoid leaking unsanitized data
            success=False,
            error=str(e),
        )


async def sanitize_error_message_with_llm(
    error_message: str,
) -> LLMSanitizationResult:
    """Sanitize error message using Gemini LLM.

    Args:
        error_message: The error message to sanitize.

    Returns:
        LLMSanitizationResult: The sanitization result.
    """
    if not error_message or not error_message.strip():
        return LLMSanitizationResult(
            original_text=error_message,
            sanitized_text="",
            success=True,
        )

    try:
        settings = get_settings()
        client = _get_genai_client()

        prompt = SANITIZE_ERROR_MESSAGE_PROMPT.format(
            error_message=error_message,
        )

        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )

        sanitized = response.text.strip()

        changes = []
        if error_message != sanitized:
            changes.append("Error message sanitized by LLM")

        return LLMSanitizationResult(
            original_text=error_message,
            sanitized_text=sanitized,
            changes_made=changes,
            success=True,
        )

    except Exception as e:
        return LLMSanitizationResult(
            original_text=error_message,
            sanitized_text="",  # Return empty on failure to avoid leaking unsanitized data
            success=False,
            error=str(e),
        )


async def sanitize_context_with_llm(
    context: str,
) -> LLMSanitizationResult:
    """Sanitize context/description using Gemini LLM.

    Args:
        context: The context to sanitize.

    Returns:
        LLMSanitizationResult: The sanitization result.
    """
    if not context or not context.strip():
        return LLMSanitizationResult(
            original_text=context,
            sanitized_text="",
            success=True,
        )

    try:
        settings = get_settings()
        client = _get_genai_client()

        prompt = SANITIZE_CONTEXT_PROMPT.format(
            context=context,
        )

        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )

        sanitized = response.text.strip()

        changes = []
        if context != sanitized:
            changes.append("Context sanitized by LLM")

        return LLMSanitizationResult(
            original_text=context,
            sanitized_text=sanitized,
            changes_made=changes,
            success=True,
        )

    except Exception as e:
        return LLMSanitizationResult(
            original_text=context,
            sanitized_text="",  # Return empty on failure to avoid leaking unsanitized data
            success=False,
            error=str(e),
        )
