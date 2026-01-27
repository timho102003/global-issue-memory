"""Pytest configuration and shared fixtures for GIM tests."""

import pytest
from uuid import uuid4


@pytest.fixture
def sample_uuid() -> str:
    """Generate a sample UUID string for testing.

    Returns:
        str: A UUID string.
    """
    return str(uuid4())


@pytest.fixture
def sample_error_message() -> str:
    """Sample error message for testing.

    Returns:
        str: A sample error message.
    """
    return "AttributeError: module 'langchain.tools' has no attribute 'tool'"


@pytest.fixture
def sample_environment() -> dict:
    """Sample environment info for testing.

    Returns:
        dict: Sample environment configuration.
    """
    return {
        "language": "python",
        "language_version": "3.11",
        "framework": "langchain",
        "framework_version": "0.2.0",
        "os": "macOS",
    }
