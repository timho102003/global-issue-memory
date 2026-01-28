"""Tests for environment extractor service."""

import pytest

from src.services.environment_extractor import (
    extract_environment_info,
    _normalize_language,
    _normalize_framework,
    _normalize_os,
    _normalize_version,
)


class TestExtractEnvironmentInfo:
    """Test cases for extract_environment_info function."""

    def test_empty_input(self) -> None:
        """Test with no inputs returns empty dict."""
        result = extract_environment_info()
        assert result == {}

    def test_language_only(self) -> None:
        """Test with language only."""
        result = extract_environment_info(language="python")
        assert result == {"language": "python"}

    def test_language_with_version(self) -> None:
        """Test with language and version."""
        result = extract_environment_info(
            language="python",
            language_version="3.11.5",
        )
        assert result["language"] == "python"
        assert result["language_version"] == "3.11.5"

    def test_framework_with_version(self) -> None:
        """Test with framework and version."""
        result = extract_environment_info(
            framework="fastapi",
            framework_version="0.100.0",
        )
        assert result["framework"] == "fastapi"
        assert result["framework_version"] == "0.100.0"

    def test_os_info(self) -> None:
        """Test with OS info."""
        result = extract_environment_info(os="linux")
        assert result["os"] == "linux"

    def test_full_environment(self) -> None:
        """Test with all environment fields."""
        result = extract_environment_info(
            language="python",
            framework="fastapi",
            language_version="3.11",
            framework_version="0.100.0",
            os="linux",
        )
        assert result["language"] == "python"
        assert result["framework"] == "fastapi"
        assert result["language_version"] == "3.11"
        assert result["framework_version"] == "0.100.0"
        assert result["os"] == "linux"

    def test_extraction_from_context_python(self) -> None:
        """Test extraction of Python version from context."""
        result = extract_environment_info(
            error_context="Running on Python 3.10.5 with pip 22.0",
        )
        assert result["language"] == "python"
        assert result["language_version"] == "3.10.5"

    def test_extraction_from_context_node(self) -> None:
        """Test extraction of Node version from context."""
        result = extract_environment_info(
            error_context="nodejs v18.15.0",
        )
        assert result["language"] == "javascript"
        assert result["language_version"] == "18.15.0"

    def test_extraction_from_context_os(self) -> None:
        """Test extraction of OS from context."""
        result = extract_environment_info(
            error_context="Running on darwin 22.0",
        )
        assert result["os"] == "macos"

    def test_explicit_values_override_extraction(self) -> None:
        """Test explicit values take priority over context extraction."""
        result = extract_environment_info(
            language="typescript",
            error_context="Python 3.10 script",
        )
        assert result["language"] == "typescript"
        # Should not have extracted python version since language was set


class TestNormalizeLanguage:
    """Test cases for _normalize_language helper."""

    def test_python_aliases(self) -> None:
        """Test Python language aliases."""
        assert _normalize_language("py") == "python"
        assert _normalize_language("Python3") == "python"
        assert _normalize_language("PYTHON") == "python"

    def test_javascript_aliases(self) -> None:
        """Test JavaScript language aliases."""
        assert _normalize_language("js") == "javascript"
        assert _normalize_language("node") == "javascript"
        assert _normalize_language("nodejs") == "javascript"

    def test_typescript_unchanged(self) -> None:
        """Test TypeScript is not aliased."""
        assert _normalize_language("typescript") == "typescript"
        assert _normalize_language("ts") == "typescript"

    def test_other_languages(self) -> None:
        """Test other languages pass through."""
        assert _normalize_language("rust") == "rust"
        assert _normalize_language("go") == "go"
        assert _normalize_language("golang") == "go"


class TestNormalizeFramework:
    """Test cases for _normalize_framework helper."""

    def test_nextjs_aliases(self) -> None:
        """Test Next.js framework aliases."""
        assert _normalize_framework("next") == "nextjs"
        assert _normalize_framework("next.js") == "nextjs"
        assert _normalize_framework("NEXT.JS") == "nextjs"

    def test_fastapi_aliases(self) -> None:
        """Test FastAPI framework aliases."""
        assert _normalize_framework("fast-api") == "fastapi"
        assert _normalize_framework("fast_api") == "fastapi"

    def test_other_frameworks(self) -> None:
        """Test other frameworks pass through."""
        assert _normalize_framework("django") == "django"
        assert _normalize_framework("flask") == "flask"


class TestNormalizeOs:
    """Test cases for _normalize_os helper."""

    def test_macos_aliases(self) -> None:
        """Test macOS aliases."""
        assert _normalize_os("mac") == "macos"
        assert _normalize_os("osx") == "macos"
        assert _normalize_os("darwin") == "macos"

    def test_windows_aliases(self) -> None:
        """Test Windows aliases."""
        assert _normalize_os("win") == "windows"
        assert _normalize_os("win32") == "windows"
        assert _normalize_os("win64") == "windows"

    def test_linux_distros(self) -> None:
        """Test Linux distribution names normalize to linux."""
        assert _normalize_os("ubuntu") == "linux"
        assert _normalize_os("debian") == "linux"
        assert _normalize_os("centos") == "linux"
        assert _normalize_os("alpine") == "linux"


class TestNormalizeVersion:
    """Test cases for _normalize_version helper."""

    def test_remove_v_prefix(self) -> None:
        """Test removal of v prefix."""
        assert _normalize_version("v1.0.0") == "1.0.0"
        assert _normalize_version("V2.3.4") == "2.3.4"

    def test_remove_version_prefix(self) -> None:
        """Test removal of 'version' prefix."""
        assert _normalize_version("version 1.0.0") == "1.0.0"
        assert _normalize_version("Version 2.0") == "2.0"

    def test_strip_whitespace(self) -> None:
        """Test stripping of whitespace."""
        assert _normalize_version("  1.0.0  ") == "1.0.0"

    def test_normal_version_unchanged(self) -> None:
        """Test normal version strings pass through."""
        assert _normalize_version("3.11.5") == "3.11.5"
        assert _normalize_version("0.100.0") == "0.100.0"
