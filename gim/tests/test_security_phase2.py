"""Tests for Phase 2 security hardening - Auth middleware and rate limiting."""

import pytest
from unittest.mock import MagicMock

import src.config as _config_module
from src.auth.ip_rate_limiter import IPRateLimiter, get_gim_id_rate_limiter


@pytest.fixture(autouse=True)
def _mock_settings():
    """Provide mock settings to avoid requiring environment variables."""
    mock = MagicMock()
    mock.transport_mode = "stdio"
    mock.frontend_url = None
    mock.jwt_secret_key = "test-secret-key-minimum-32-characters-long"
    mock.auth_issuer = "gim-mcp"
    mock.auth_audience = "gim-clients"
    mock.access_token_ttl_hours = 24
    mock.default_daily_search_limit = 100
    mock.log_level = "INFO"
    mock.require_auth_for_reads = False
    original = _config_module._settings
    _config_module._settings = mock
    yield mock
    _config_module._settings = original


class TestIPRateLimiter:
    """Test IP-based rate limiter."""

    def test_allows_requests_under_limit(self) -> None:
        """Test that requests under the limit are allowed."""
        limiter = IPRateLimiter(max_requests=3, window_seconds=3600)
        assert limiter.is_allowed("1.2.3.4") is True
        assert limiter.is_allowed("1.2.3.4") is True
        assert limiter.is_allowed("1.2.3.4") is True

    def test_blocks_requests_over_limit(self) -> None:
        """Test that requests over the limit are blocked."""
        limiter = IPRateLimiter(max_requests=2, window_seconds=3600)
        assert limiter.is_allowed("1.2.3.4") is True
        assert limiter.is_allowed("1.2.3.4") is True
        assert limiter.is_allowed("1.2.3.4") is False

    def test_different_ips_tracked_separately(self) -> None:
        """Test that different IPs have independent limits."""
        limiter = IPRateLimiter(max_requests=1, window_seconds=3600)
        assert limiter.is_allowed("1.2.3.4") is True
        assert limiter.is_allowed("5.6.7.8") is True
        assert limiter.is_allowed("1.2.3.4") is False

    def test_get_remaining_requests(self) -> None:
        """Test that remaining count decreases with usage."""
        limiter = IPRateLimiter(max_requests=3, window_seconds=3600)
        assert limiter.get_remaining("1.2.3.4") == 3
        limiter.is_allowed("1.2.3.4")
        assert limiter.get_remaining("1.2.3.4") == 2

    def test_get_remaining_at_zero(self) -> None:
        """Test that remaining is zero when limit is exhausted."""
        limiter = IPRateLimiter(max_requests=1, window_seconds=3600)
        limiter.is_allowed("1.2.3.4")
        assert limiter.get_remaining("1.2.3.4") == 0

    def test_singleton_returns_same_instance(self) -> None:
        """Test that get_gim_id_rate_limiter returns a singleton."""
        # Reset the singleton for this test
        import src.auth.ip_rate_limiter as limiter_mod
        original = limiter_mod._gim_id_limiter
        limiter_mod._gim_id_limiter = None
        try:
            limiter1 = get_gim_id_rate_limiter()
            limiter2 = get_gim_id_rate_limiter()
            assert limiter1 is limiter2
        finally:
            limiter_mod._gim_id_limiter = original


class TestRequestSizeLimitMiddleware:
    """Test request body size limit middleware."""

    def test_middleware_class_exists(self) -> None:
        """Test that RequestSizeLimitMiddleware is importable."""
        from src.server import RequestSizeLimitMiddleware
        assert RequestSizeLimitMiddleware is not None

    def test_middleware_has_dispatch_method(self) -> None:
        """Test that the middleware has the expected dispatch method."""
        from src.server import RequestSizeLimitMiddleware
        assert hasattr(RequestSizeLimitMiddleware, "dispatch")


class TestRequireAuthHelper:
    """Test the _require_auth helper."""

    def test_require_auth_for_reads_config_exists(self) -> None:
        """Test that require_auth_for_reads config field exists with correct default."""
        from src.config import Settings
        settings = Settings(
            supabase_url="https://dummy.supabase.co",
            supabase_key="dummy-supabase-key",
            qdrant_url="https://dummy.qdrant.io",
            qdrant_api_key="dummy-qdrant-api-key",
            google_api_key="dummy-google-api-key",
            jwt_secret_key="a" * 32,
        )
        assert hasattr(settings, "require_auth_for_reads")
        assert settings.require_auth_for_reads is False  # default

    def test_require_auth_for_reads_can_be_enabled(self) -> None:
        """Test that require_auth_for_reads can be set to True."""
        from src.config import Settings
        settings = Settings(
            supabase_url="https://dummy.supabase.co",
            supabase_key="dummy-supabase-key",
            qdrant_url="https://dummy.qdrant.io",
            qdrant_api_key="dummy-qdrant-api-key",
            google_api_key="dummy-google-api-key",
            jwt_secret_key="a" * 32,
            require_auth_for_reads=True,
        )
        assert settings.require_auth_for_reads is True

    def test_require_auth_helper_exists(self) -> None:
        """Test that _require_auth is importable from server module."""
        from src.server import _require_auth
        assert _require_auth is not None
        assert callable(_require_auth)


class TestRequireAuthHelperBehavior:
    """Test _require_auth with actual request mocks."""

    @pytest.mark.asyncio
    async def test_missing_auth_header_returns_401(self) -> None:
        """Test that missing Authorization header returns 401."""
        from src.server import _require_auth

        mock_request = MagicMock()
        mock_request.headers = {}

        claims, error = await _require_auth(mock_request)
        assert claims is None
        assert error is not None
        assert error.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_auth_format_returns_401(self) -> None:
        """Test that non-Bearer auth format returns 401."""
        from src.server import _require_auth

        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Basic abc123"}

        claims, error = await _require_auth(mock_request)
        assert claims is None
        assert error is not None
        assert error.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self) -> None:
        """Test that an invalid/expired token returns 401."""
        from unittest.mock import patch
        from src.server import _require_auth

        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer invalid-token"}

        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = None

        with patch("src.server.GIMTokenVerifier", return_value=mock_verifier):
            claims, error = await _require_auth(mock_request)
            assert claims is None
            assert error is not None
            assert error.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_returns_claims(self) -> None:
        """Test that a valid token returns claims with no error."""
        from unittest.mock import patch
        from src.server import _require_auth

        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid-token"}

        mock_claims = MagicMock()
        mock_claims.sub = "test-gim-id"
        mock_verifier = MagicMock()
        mock_verifier.verify.return_value = mock_claims

        with patch("src.server.GIMTokenVerifier", return_value=mock_verifier):
            claims, error = await _require_auth(mock_request)
            assert claims is mock_claims
            assert error is None
