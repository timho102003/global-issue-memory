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
    """Test that submit response does not echo back request arguments."""

    def test_submit_response_contains_only_safe_fields(self) -> None:
        """Test that async submit response has only success, message, submission_id."""
        from src.models.responses import SubmitIssueAcceptedResponse
        response = SubmitIssueAcceptedResponse(
            success=True,
            message="Accepted",
            submission_id="test-id",
        )
        fields = set(response.model_dump().keys())
        assert fields == {"success", "message", "submission_id"}

    def test_submit_response_excludes_request_arguments(self) -> None:
        """Test that no request arguments are echoed in the response model."""
        from src.models.responses import SubmitIssueAcceptedResponse
        response = SubmitIssueAcceptedResponse(
            success=True,
            message="Accepted",
            submission_id="test-id",
        )
        data = response.model_dump()
        # None of these request-argument keys should appear in the response
        for dangerous_key in ["error_message", "root_cause", "fix_summary",
                              "id", "master_issue_id", "created_at", "access_token"]:
            assert dangerous_key not in data
