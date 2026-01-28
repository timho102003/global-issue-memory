"""Service for extracting and structuring environment information.

This module processes raw environment data into a structured format
for storage and analysis in the GIM system.
"""

import re
from typing import Any, Dict, Optional

from src.logging_config import get_logger


logger = get_logger("services.environment_extractor")


def extract_environment_info(
    language: Optional[str] = None,
    framework: Optional[str] = None,
    error_context: Optional[str] = None,
    language_version: Optional[str] = None,
    framework_version: Optional[str] = None,
    os: Optional[str] = None,
) -> Dict[str, Any]:
    """Extract and structure environment information.

    Processes raw environment data into a normalized, structured format
    suitable for storage and cross-issue analysis.

    Args:
        language: Programming language (e.g., "python", "javascript").
        framework: Framework being used (e.g., "fastapi", "react").
        error_context: Additional context that may contain env info.
        language_version: Language version (e.g., "3.11", "18.2").
        framework_version: Framework version (e.g., "0.100.0", "18.2.0").
        os: Operating system (e.g., "linux", "macos", "windows").

    Returns:
        Dict[str, Any]: Structured environment information.
    """
    env_info: Dict[str, Any] = {}

    # Normalize and add language info
    if language:
        normalized_lang = _normalize_language(language)
        env_info["language"] = normalized_lang
        if language_version:
            env_info["language_version"] = _normalize_version(language_version)

    # Normalize and add framework info
    if framework:
        normalized_framework = _normalize_framework(framework)
        env_info["framework"] = normalized_framework
        if framework_version:
            env_info["framework_version"] = _normalize_version(framework_version)

    # Normalize and add OS info
    if os:
        env_info["os"] = _normalize_os(os)

    # Try to extract additional info from error context
    if error_context:
        extracted = _extract_from_context(error_context)
        # Only add extracted values if not already set
        for key, value in extracted.items():
            if key not in env_info:
                env_info[key] = value

    logger.debug(f"Extracted environment info: {env_info}")
    return env_info


def _normalize_language(language: str) -> str:
    """Normalize language name to lowercase standard form.

    Args:
        language: Raw language name.

    Returns:
        str: Normalized language name.
    """
    language = language.lower().strip()

    # Common aliases
    aliases = {
        "py": "python",
        "python3": "python",
        "js": "javascript",
        "ts": "typescript",
        "node": "javascript",
        "nodejs": "javascript",
        "rb": "ruby",
        "rs": "rust",
        "go": "go",
        "golang": "go",
        "cs": "csharp",
        "c#": "csharp",
    }

    return aliases.get(language, language)


def _normalize_framework(framework: str) -> str:
    """Normalize framework name to lowercase standard form.

    Args:
        framework: Raw framework name.

    Returns:
        str: Normalized framework name.
    """
    framework = framework.lower().strip()

    # Common aliases
    aliases = {
        "next": "nextjs",
        "next.js": "nextjs",
        "react.js": "react",
        "vue.js": "vue",
        "fast-api": "fastapi",
        "fast_api": "fastapi",
        "express.js": "express",
        "rails": "ruby-on-rails",
        "ror": "ruby-on-rails",
    }

    return aliases.get(framework, framework)


def _normalize_os(os: str) -> str:
    """Normalize OS name to lowercase standard form.

    Args:
        os: Raw OS name.

    Returns:
        str: Normalized OS name.
    """
    os = os.lower().strip()

    # Common aliases
    aliases = {
        "mac": "macos",
        "osx": "macos",
        "darwin": "macos",
        "win": "windows",
        "win32": "windows",
        "win64": "windows",
        "ubuntu": "linux",
        "debian": "linux",
        "centos": "linux",
        "fedora": "linux",
        "rhel": "linux",
        "alpine": "linux",
    }

    return aliases.get(os, os)


def _normalize_version(version: str) -> str:
    """Normalize version string.

    Args:
        version: Raw version string.

    Returns:
        str: Normalized version string.
    """
    # Remove common prefixes
    version = version.lower().strip()
    # First remove 'version ' prefix (must be before v removal)
    version = re.sub(r"^version\s*", "", version)
    # Then remove 'v' or 'v.' prefix (only match standalone v, not word starting with v)
    version = re.sub(r"^v\.?(?=\d)", "", version)

    return version


def _extract_from_context(context: str) -> Dict[str, str]:
    """Extract environment info from error context string.

    Parses error context for embedded version and platform information.

    Args:
        context: Error context string.

    Returns:
        Dict[str, str]: Extracted environment info.
    """
    extracted: Dict[str, str] = {}
    context_lower = context.lower()

    # Python version patterns
    python_match = re.search(r"python\s*(\d+\.\d+(?:\.\d+)?)", context_lower)
    if python_match:
        extracted["language"] = "python"
        extracted["language_version"] = python_match.group(1)

    # Node version patterns
    node_match = re.search(r"node(?:js)?\s*v?(\d+\.\d+(?:\.\d+)?)", context_lower)
    if node_match and "language" not in extracted:
        extracted["language"] = "javascript"
        extracted["language_version"] = node_match.group(1)

    # OS patterns
    if "darwin" in context_lower or "macos" in context_lower:
        extracted["os"] = "macos"
    elif "linux" in context_lower:
        extracted["os"] = "linux"
    elif "windows" in context_lower or "win32" in context_lower:
        extracted["os"] = "windows"

    return extracted
