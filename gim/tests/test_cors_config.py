"""Tests for CORS origin configuration in server module."""

from unittest.mock import MagicMock

import pytest

from src.config import Settings
from src.server import _build_cors_origins


class TestBuildCorsOrigins:
    """Test cases for the _build_cors_origins helper function."""

    def test_default_origins_without_frontend_url(self) -> None:
        """Test that only localhost origins are returned when frontend_url is None.

        When no production frontend URL is configured, the function should
        return only the two default localhost development origins.
        """
        mock_settings = MagicMock()
        mock_settings.frontend_url = None

        origins = _build_cors_origins(mock_settings)

        assert origins == [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    def test_origins_includes_frontend_url_when_set(self) -> None:
        """Test that frontend_url is appended when it is configured.

        When a production frontend URL is provided, the returned list
        should contain both localhost origins plus the frontend URL.
        """
        mock_settings = MagicMock()
        mock_settings.frontend_url = "https://my-app.vercel.app"

        origins = _build_cors_origins(mock_settings)

        assert origins == [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://my-app.vercel.app",
        ]

    def test_settings_frontend_url_defaults_to_none(self) -> None:
        """Test that Settings.frontend_url defaults to None.

        Constructs a real Settings instance with all required fields
        using dummy values and verifies that frontend_url is None by default.
        """
        settings = Settings(
            supabase_url="https://dummy.supabase.co",
            supabase_key="dummy-supabase-key",
            qdrant_url="https://dummy.qdrant.io",
            qdrant_api_key="dummy-qdrant-api-key",
            google_api_key="dummy-google-api-key",
            jwt_secret_key="a" * 32,
        )

        assert settings.frontend_url is None
