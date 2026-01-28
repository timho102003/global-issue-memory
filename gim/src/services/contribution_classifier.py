"""Service for classifying the type of contribution a child issue makes.

This module analyzes submission content to determine the primary contribution type,
helping organize and categorize child issues within the GIM system.
"""

from typing import List, Optional

from src.models.issue import ContributionType
from src.logging_config import get_logger


logger = get_logger("services.contribution_classifier")


# Keywords for classification
_ENVIRONMENT_KEYWORDS = [
    "install", "package", "dependency", "version", "pip", "npm", "yarn",
    "environment", "config", "configuration", "setup", "path", "env",
    "docker", "container", "kubernetes", "os", "operating system",
    "library", "module", "runtime", "sdk", "framework version",
]

_MODEL_QUIRK_KEYWORDS = [
    "model", "ai", "llm", "gpt", "claude", "anthropic", "openai",
    "prompt", "response", "hallucin", "behavior", "quirk", "pattern",
    "token", "context", "temperature", "generation", "tool call",
    "function call", "reasoning", "chain of thought",
]


def classify_contribution_type(
    error_message: str,
    root_cause: str,
    fix_steps: List[str],
    environment_actions: Optional[List[dict]] = None,
    model_behavior_notes: Optional[List[str]] = None,
    validation_success: Optional[bool] = None,
) -> ContributionType:
    """Classify contribution type based on submission content.

    Analyzes the provided content to determine what type of contribution
    this child issue represents to the parent master issue.

    Classification priority:
    1. VALIDATION: If validation_success is explicitly provided
    2. ENVIRONMENT: If environment_actions are provided or env-related keywords
    3. MODEL_QUIRK: If model_behavior_notes are provided or model-related keywords
    4. SYMPTOM: Default for new error variations

    Args:
        error_message: The error message encountered.
        root_cause: Explanation of what caused the error.
        fix_steps: Step-by-step instructions to fix the issue.
        environment_actions: Environment changes (package installs, etc.).
        model_behavior_notes: Notes about model-specific behavior.
        validation_success: Whether the fix was validated successfully.

    Returns:
        ContributionType: The classified contribution type.
    """
    environment_actions = environment_actions or []
    model_behavior_notes = model_behavior_notes or []

    # Priority 1: Explicit validation
    if validation_success is not None:
        logger.debug("Classified as VALIDATION (explicit validation_success provided)")
        return ContributionType.VALIDATION

    # Priority 2: Environment-related contribution
    if environment_actions:
        logger.debug("Classified as ENVIRONMENT (environment_actions provided)")
        return ContributionType.ENVIRONMENT

    # Check for environment keywords in content
    combined_text = _combine_text(error_message, root_cause, fix_steps)
    if _has_keywords(combined_text, _ENVIRONMENT_KEYWORDS):
        logger.debug("Classified as ENVIRONMENT (environment keywords detected)")
        return ContributionType.ENVIRONMENT

    # Priority 3: Model-specific behavior
    if model_behavior_notes:
        logger.debug("Classified as MODEL_QUIRK (model_behavior_notes provided)")
        return ContributionType.MODEL_QUIRK

    # Check for model keywords in content
    if _has_keywords(combined_text, _MODEL_QUIRK_KEYWORDS):
        logger.debug("Classified as MODEL_QUIRK (model keywords detected)")
        return ContributionType.MODEL_QUIRK

    # Default: New symptom/error variation
    logger.debug("Classified as SYMPTOM (default)")
    return ContributionType.SYMPTOM


def _combine_text(
    error_message: str,
    root_cause: str,
    fix_steps: List[str],
) -> str:
    """Combine all text content for keyword analysis.

    Args:
        error_message: The error message.
        root_cause: Root cause description.
        fix_steps: List of fix steps.

    Returns:
        str: Combined lowercase text.
    """
    all_text = [error_message, root_cause] + fix_steps
    return " ".join(all_text).lower()


def _has_keywords(text: str, keywords: List[str]) -> bool:
    """Check if text contains any of the given keywords.

    Args:
        text: Text to search in.
        keywords: Keywords to look for.

    Returns:
        bool: True if any keyword is found.
    """
    return any(keyword in text for keyword in keywords)
