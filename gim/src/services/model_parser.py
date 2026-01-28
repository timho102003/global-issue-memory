"""Service for parsing model information from model strings.

This module extracts provider, model name, and version information
from various model identifier formats used across different AI providers.
"""

import re
from typing import Optional, Tuple

from src.logging_config import get_logger


logger = get_logger("services.model_parser")


# Known provider prefixes and patterns
_PROVIDER_PATTERNS = {
    "anthropic": [
        r"claude",
        r"anthropic",
    ],
    "openai": [
        r"gpt-",
        r"gpt4",
        r"o1-",
        r"o3-",
        r"davinci",
        r"curie",
        r"babbage",
        r"ada",
        r"text-embedding",
        r"openai",
    ],
    "google": [
        r"gemini",
        r"bard",
        r"palm",
        r"google",
    ],
    "meta": [
        r"llama",
        r"meta",
    ],
    "mistral": [
        r"mistral",
        r"mixtral",
    ],
    "cohere": [
        r"cohere",
        r"command",
    ],
    "deepseek": [
        r"deepseek",
    ],
}


def parse_model_info(
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse model string into provider, name, and version.

    Extracts structured information from model identifier strings
    used by various AI providers.

    Examples:
        - "claude-3-opus-20240229" -> ("anthropic", "claude-3-opus", "20240229")
        - "gpt-4-turbo-2024-04-09" -> ("openai", "gpt-4-turbo", "2024-04-09")
        - "gemini-1.5-pro" -> ("google", "gemini-1.5-pro", None)

    Args:
        model: Model identifier string (e.g., "claude-3-opus-20240229").
        provider: Explicit provider override (e.g., "anthropic", "openai").

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]:
            (provider, model_name, model_version)
    """
    if not model:
        return (provider, None, None)

    model = model.strip().lower()

    # Extract version (date pattern at end)
    model_name, model_version = _extract_version(model)

    # Determine provider (use explicit if provided, otherwise detect)
    if provider:
        detected_provider = provider.lower().strip()
    else:
        detected_provider = _detect_provider(model)

    logger.debug(
        f"Parsed model '{model}' -> provider={detected_provider}, "
        f"name={model_name}, version={model_version}"
    )

    return (detected_provider, model_name, model_version)


def _extract_version(model: str) -> Tuple[str, Optional[str]]:
    """Extract version from model string.

    Looks for common version patterns at the end of model identifiers:
    - Date format: 20240229, 2024-04-09
    - Semantic version: v1.0, 1.5.0
    - Revision suffix: -rev1, -r2

    Args:
        model: Model string to parse.

    Returns:
        Tuple[str, Optional[str]]: (model_name_without_version, version)
    """
    # Date version pattern (e.g., -20240229, -2024-04-09)
    date_match = re.search(r"-(\d{4}-?\d{2}-?\d{2})$", model)
    if date_match:
        version = date_match.group(1)
        name = model[: date_match.start()]
        return (name, version)

    # Semantic version pattern at end (e.g., -v1.0, -1.5.0)
    semver_match = re.search(r"-v?(\d+\.\d+(?:\.\d+)?)$", model)
    if semver_match:
        version = semver_match.group(1)
        name = model[: semver_match.start()]
        return (name, version)

    # Revision pattern (e.g., -rev1, -r2)
    rev_match = re.search(r"-(rev?\d+)$", model)
    if rev_match:
        version = rev_match.group(1)
        name = model[: rev_match.start()]
        return (name, version)

    return (model, None)


def _detect_provider(model: str) -> Optional[str]:
    """Detect provider from model name patterns.

    Uses known prefixes and patterns to identify the AI provider
    for a given model identifier.

    Args:
        model: Model string to analyze.

    Returns:
        Optional[str]: Detected provider or None.
    """
    for provider, patterns in _PROVIDER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, model):
                return provider

    return None


def get_model_family(model_name: Optional[str]) -> Optional[str]:
    """Get the model family from a model name.

    Extracts the base model family (e.g., "claude-3" from "claude-3-opus").

    Args:
        model_name: Parsed model name.

    Returns:
        Optional[str]: Model family or None.
    """
    if not model_name:
        return None

    # Claude family patterns
    claude_match = re.match(r"(claude-\d+(?:\.\d+)?)", model_name)
    if claude_match:
        return claude_match.group(1)

    # GPT family patterns
    gpt_match = re.match(r"(gpt-\d+)", model_name)
    if gpt_match:
        return gpt_match.group(1)

    # Gemini family patterns
    gemini_match = re.match(r"(gemini-\d+(?:\.\d+)?)", model_name)
    if gemini_match:
        return gemini_match.group(1)

    # Llama family patterns
    llama_match = re.match(r"(llama-?\d+)", model_name)
    if llama_match:
        return llama_match.group(1)

    return None
