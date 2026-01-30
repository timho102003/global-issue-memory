"""Tests for Phase 1 security hardening."""

import pytest
from pydantic import SecretStr

from src.config import Settings


class TestSecretStrConfig:
    """Test that sensitive config fields use SecretStr."""

    def test_supabase_key_is_secret_str(self) -> None:
        """Test supabase_key field is SecretStr type."""
        settings = Settings(
            supabase_url="https://dummy.supabase.co",
            supabase_key="dummy-supabase-key",
            qdrant_url="https://dummy.qdrant.io",
            qdrant_api_key="dummy-qdrant-api-key",
            google_api_key="dummy-google-api-key",
            jwt_secret_key="a" * 32,
        )
        assert isinstance(settings.supabase_key, SecretStr)
        assert settings.supabase_key.get_secret_value() == "dummy-supabase-key"

    def test_qdrant_api_key_is_secret_str(self) -> None:
        """Test qdrant_api_key field is SecretStr type."""
        settings = Settings(
            supabase_url="https://dummy.supabase.co",
            supabase_key="dummy-supabase-key",
            qdrant_url="https://dummy.qdrant.io",
            qdrant_api_key="dummy-qdrant-api-key",
            google_api_key="dummy-google-api-key",
            jwt_secret_key="a" * 32,
        )
        assert isinstance(settings.qdrant_api_key, SecretStr)
        assert settings.qdrant_api_key.get_secret_value() == "dummy-qdrant-api-key"

    def test_google_api_key_is_secret_str(self) -> None:
        """Test google_api_key field is SecretStr type."""
        settings = Settings(
            supabase_url="https://dummy.supabase.co",
            supabase_key="dummy-supabase-key",
            qdrant_url="https://dummy.qdrant.io",
            qdrant_api_key="dummy-qdrant-api-key",
            google_api_key="dummy-google-api-key",
            jwt_secret_key="a" * 32,
        )
        assert isinstance(settings.google_api_key, SecretStr)

    def test_jwt_secret_key_is_secret_str(self) -> None:
        """Test jwt_secret_key field is SecretStr type."""
        settings = Settings(
            supabase_url="https://dummy.supabase.co",
            supabase_key="dummy-supabase-key",
            qdrant_url="https://dummy.qdrant.io",
            qdrant_api_key="dummy-qdrant-api-key",
            google_api_key="dummy-google-api-key",
            jwt_secret_key="a" * 32,
        )
        assert isinstance(settings.jwt_secret_key, SecretStr)

    def test_secret_str_not_exposed_in_repr(self) -> None:
        """Test that SecretStr values are not exposed in string representation."""
        settings = Settings(
            supabase_url="https://dummy.supabase.co",
            supabase_key="super-secret-key",
            qdrant_url="https://dummy.qdrant.io",
            qdrant_api_key="qdrant-secret",
            google_api_key="google-secret",
            jwt_secret_key="a" * 32,
        )
        repr_str = repr(settings)
        assert "super-secret-key" not in repr_str
        assert "qdrant-secret" not in repr_str
        assert "google-secret" not in repr_str


class TestResponseInjectionPrevention:
    """Test that response injection via **arguments is prevented."""

    def test_allowed_fields_frozenset_exists(self) -> None:
        """Test that _ALLOWED_SUBMIT_RESPONSE_FIELDS is defined."""
        from src.server import _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert isinstance(_ALLOWED_SUBMIT_RESPONSE_FIELDS, frozenset)
        assert "error_message" in _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert "root_cause" in _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert "fix_summary" in _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert "language" in _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert "framework" in _ALLOWED_SUBMIT_RESPONSE_FIELDS

    def test_disallowed_fields_not_in_set(self) -> None:
        """Test that dangerous fields are not in allowed set."""
        from src.server import _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert "id" not in _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert "master_issue_id" not in _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert "created_at" not in _ALLOWED_SUBMIT_RESPONSE_FIELDS
        assert "access_token" not in _ALLOWED_SUBMIT_RESPONSE_FIELDS
