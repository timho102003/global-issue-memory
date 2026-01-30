"""Post-processing code synthesis for fix bundles.

This module generates reproduction snippets, BEFORE/AFTER fix code,
enriched fix steps with embedded code, and deterministic patch diffs
using the Gemini LLM and Python's difflib.
"""

import difflib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.config import get_settings
from src.logging_config import get_logger
from src.services.sanitization.llm_sanitizer import _get_genai_client

logger = get_logger("services.code_synthesizer")


@dataclass
class CodeSynthesisResult:
    """Result of code synthesis for fix bundles.

    Attributes:
        reproduction_snippet: Minimal code to reproduce the error.
        fix_snippet: BEFORE/AFTER code showing the fix.
        synthesized_fix_steps: Fix steps enriched with embedded code snippets.
        patch_diff: Unified diff of the fix.
        success: Whether synthesis was successful.
        error: Error message if synthesis failed.
    """

    reproduction_snippet: str = ""
    fix_snippet: str = ""
    synthesized_fix_steps: List[str] = field(default_factory=list)
    patch_diff: str = ""
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYNTHESIZE_REPRODUCTION_PROMPT = """You are a code synthesis expert. Create a minimal, self-contained code snippet that reproduces the following error.

**Requirements:**
1. Maximum 20 lines of code
2. Copy-pasteable and runnable
3. Use generic names (no real project names)
4. Include necessary imports
5. Add a comment "# This triggers the error" at the key line

**Error:** {error_message}
**Context:** {error_context}
**Original Code:** {code_snippet}

**Output ONLY the reproduction code, nothing else:**
"""

SYNTHESIZE_FIX_PROMPT = """You are a code synthesis expert. Create a clear BEFORE/AFTER code comparison showing how to fix the following error.

**Requirements:**
1. Maximum 30 lines total
2. Show "# BEFORE (broken)" section then "# AFTER (fixed)" section
3. Add inline comments explaining WHY each change fixes the issue
4. Use generic names (no real project names)
5. Keep only the relevant code that changes

**Error:** {error_message}
**Root Cause:** {root_cause}
**Fix Steps:** {fix_steps}
**Code Changes:** {code_changes}

**Output ONLY the before/after code, nothing else:**
"""

SYNTHESIZE_FIX_STEPS_PROMPT = """You are a code synthesis expert. Enrich each fix step with an embedded code snippet showing what to do.

**Requirements:**
1. Keep the original step text
2. Add a small code snippet (2-5 lines) after each step showing the actual code change
3. Format each step as: "Step text\\n```\\ncode snippet\\n```"
4. Use generic names (no real project names)

**Fix Steps:**
{fix_steps}

**Code Changes:**
{code_changes}

**Output the enriched steps as a JSON array of strings, nothing else:**
"""


# ---------------------------------------------------------------------------
# Helper: strip markdown code blocks
# ---------------------------------------------------------------------------

def _strip_markdown_code_blocks(text: str) -> str:
    """Strip markdown code block fences from LLM response text.

    Removes leading ```<language> and trailing ``` lines that Gemini
    sometimes wraps around its output.

    Args:
        text: Raw text from LLM response.

    Returns:
        str: Text with markdown code block fences removed.
    """
    if not text:
        return text

    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # Remove first line (```python or ```)
        lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines)

    return stripped


# ---------------------------------------------------------------------------
# LLM synthesis functions
# ---------------------------------------------------------------------------

async def synthesize_reproduction_code(
    error_message: str,
    error_context: str,
    code_snippet: str,
) -> str:
    """Synthesize a minimal reproduction snippet for an error.

    Uses Gemini to generate a concise, copy-pasteable code snippet
    that reproduces the given error.

    Args:
        error_message: The error message to reproduce.
        error_context: Surrounding context describing the error.
        code_snippet: Original code where the error occurred.

    Returns:
        str: Reproduction code snippet, or empty string on failure.
    """
    try:
        settings = get_settings()
        client = _get_genai_client()

        prompt = SYNTHESIZE_REPRODUCTION_PROMPT.format(
            error_message=error_message,
            error_context=error_context,
            code_snippet=code_snippet,
        )

        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )

        return _strip_markdown_code_blocks(response.text.strip())

    except Exception as e:
        logger.warning(
            "Failed to synthesize reproduction code: %s",
            type(e).__name__,
        )
        return ""


async def synthesize_fix_code(
    error_message: str,
    root_cause: str,
    fix_steps: List[str],
    code_changes: List[Dict[str, Any]],
) -> str:
    """Synthesize a BEFORE/AFTER code comparison for a fix.

    Uses Gemini to generate a clear code comparison showing
    the broken code and the fixed version with inline comments.

    Args:
        error_message: The error message being fixed.
        root_cause: Description of the root cause.
        fix_steps: List of human-readable fix steps.
        code_changes: List of code change dicts with before/after keys.

    Returns:
        str: BEFORE/AFTER fix code snippet, or empty string on failure.
    """
    try:
        settings = get_settings()
        client = _get_genai_client()

        prompt = SYNTHESIZE_FIX_PROMPT.format(
            error_message=error_message,
            root_cause=root_cause,
            fix_steps="\n".join(fix_steps) if fix_steps else "Not provided",
            code_changes=json.dumps(code_changes, indent=2) if code_changes else "Not provided",
        )

        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )

        return _strip_markdown_code_blocks(response.text.strip())

    except Exception as e:
        logger.warning(
            "Failed to synthesize fix code: %s",
            type(e).__name__,
        )
        return ""


async def synthesize_fix_steps_with_code(
    fix_steps: List[str],
    code_changes: List[Dict[str, Any]],
) -> List[str]:
    """Enrich fix steps with embedded code snippets.

    Uses Gemini to add small code examples after each fix step,
    making the steps more actionable.

    Args:
        fix_steps: List of human-readable fix steps.
        code_changes: List of code change dicts with before/after keys.

    Returns:
        List[str]: Enriched fix steps with embedded code, or
            the original fix_steps on failure.
    """
    if not fix_steps:
        return []

    try:
        settings = get_settings()
        client = _get_genai_client()

        prompt = SYNTHESIZE_FIX_STEPS_PROMPT.format(
            fix_steps="\n".join(f"- {step}" for step in fix_steps),
            code_changes=json.dumps(code_changes, indent=2) if code_changes else "Not provided",
        )

        response = client.models.generate_content(
            model=settings.llm_model,
            contents=prompt,
        )

        raw = _strip_markdown_code_blocks(response.text.strip())
        enriched = json.loads(raw)

        if isinstance(enriched, list) and all(isinstance(s, str) for s in enriched):
            return enriched

        logger.warning(
            "LLM returned unexpected format for enriched fix steps, "
            "falling back to original steps."
        )
        return fix_steps

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(
            "Failed to parse enriched fix steps JSON: %s",
            type(e).__name__,
        )
        return fix_steps
    except Exception as e:
        logger.warning(
            "Failed to synthesize enriched fix steps: %s",
            type(e).__name__,
        )
        return fix_steps


# ---------------------------------------------------------------------------
# Deterministic synthesis
# ---------------------------------------------------------------------------

def synthesize_patch_diff(code_changes: List[Dict[str, Any]]) -> str:
    """Generate unified diff from code changes.

    This is a deterministic function (no LLM). It uses Python's
    ``difflib.unified_diff`` to produce a standard unified diff
    string from before/after code pairs.

    Args:
        code_changes: List of dicts with optional "before" and "after" keys.
            Each dict may also contain a "file" key used as the file label.

    Returns:
        str: Unified diff string.
    """
    if not code_changes:
        return ""

    diffs: List[str] = []
    for i, change in enumerate(code_changes):
        before = change.get("before", "")
        after = change.get("after", "")
        if not before and not after:
            continue
        file_label = change.get("file", f"change_{i + 1}")
        diff = difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{file_label}",
            tofile=f"b/{file_label}",
        )
        diffs.append("".join(diff))

    return "\n".join(diffs)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_code_synthesis(
    error_message: str = "",
    error_context: str = "",
    code_snippet: str = "",
    root_cause: str = "",
    fix_steps: Optional[List[str]] = None,
    code_changes: Optional[List[Dict[str, Any]]] = None,
) -> CodeSynthesisResult:
    """Run all code synthesis steps for a fix bundle.

    Executes LLM-based synthesis steps (reproduction code, fix code,
    enriched fix steps) and a deterministic patch diff generation.
    LLM failures are non-blocking: they are logged as warnings and
    the corresponding field falls back to its default value.

    Args:
        error_message: The error message.
        error_context: Error context description.
        code_snippet: Original code snippet.
        root_cause: Root cause description.
        fix_steps: List of fix step strings.
        code_changes: List of code change dicts.

    Returns:
        CodeSynthesisResult: Combined synthesis results.
    """
    if fix_steps is None:
        fix_steps = []
    if code_changes is None:
        code_changes = []

    errors: List[str] = []

    # 1. Reproduction code (LLM)
    reproduction_snippet = ""
    try:
        reproduction_snippet = await synthesize_reproduction_code(
            error_message=error_message,
            error_context=error_context,
            code_snippet=code_snippet,
        )
    except Exception as e:
        msg = f"reproduction synthesis failed: {type(e).__name__}"
        logger.warning(msg)
        errors.append(msg)

    # 2. Fix code (LLM)
    fix_snippet = ""
    try:
        fix_snippet = await synthesize_fix_code(
            error_message=error_message,
            root_cause=root_cause,
            fix_steps=fix_steps,
            code_changes=code_changes,
        )
    except Exception as e:
        msg = f"fix code synthesis failed: {type(e).__name__}"
        logger.warning(msg)
        errors.append(msg)

    # 3. Enriched fix steps (LLM)
    synthesized_fix_steps = fix_steps
    try:
        synthesized_fix_steps = await synthesize_fix_steps_with_code(
            fix_steps=fix_steps,
            code_changes=code_changes,
        )
    except Exception as e:
        msg = f"fix steps synthesis failed: {type(e).__name__}"
        logger.warning(msg)
        errors.append(msg)
        synthesized_fix_steps = fix_steps

    # 4. Patch diff (deterministic -- always runs)
    patch_diff = synthesize_patch_diff(code_changes)

    success = len(errors) == 0
    error_summary = "; ".join(errors) if errors else None

    return CodeSynthesisResult(
        reproduction_snippet=reproduction_snippet,
        fix_snippet=fix_snippet,
        synthesized_fix_steps=synthesized_fix_steps,
        patch_diff=patch_diff,
        success=success,
        error=error_summary,
    )
