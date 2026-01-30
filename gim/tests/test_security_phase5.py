"""Tests for Phase 5 security hardening - CORS, headers, dashboard bounds."""

import pytest
from pydantic import ValidationError

from src.auth.oauth_models import OAuthClientRegistrationRequest


class TestCORSRestrictions:
    """Test that CORS is properly restricted."""

    def test_cors_methods_not_wildcard(self) -> None:
        """Verify CORS methods are explicitly listed, not wildcard."""
        # This is a code-level check - we verify the middleware config
        # by checking server.py doesn't use allow_methods=["*"]
        import inspect

        from src.server import run_server

        source = inspect.getsource(run_server)
        assert 'allow_methods=["*"]' not in source
        assert 'allow_headers=["*"]' not in source

    def test_security_headers_middleware_exists(self) -> None:
        """Verify SecurityHeadersMiddleware is defined."""
        from src.server import SecurityHeadersMiddleware

        assert SecurityHeadersMiddleware is not None


class TestRedirectURIValidation:
    """Test redirect URI validation in OAuth models."""

    def test_rejects_fragment_in_redirect_uri(self) -> None:
        """Redirect URIs with fragments should be rejected."""
        with pytest.raises(ValidationError):
            OAuthClientRegistrationRequest(
                redirect_uris=["https://example.com/callback#fragment"],
            )

    def test_rejects_wildcard_in_redirect_uri(self) -> None:
        """Redirect URIs with wildcards should be rejected."""
        with pytest.raises(ValidationError):
            OAuthClientRegistrationRequest(
                redirect_uris=["https://*.example.com/callback"],
            )

    def test_accepts_valid_redirect_uri(self) -> None:
        """Valid redirect URIs should be accepted."""
        req = OAuthClientRegistrationRequest(
            redirect_uris=["https://example.com/callback"],
        )
        assert req.redirect_uris == ["https://example.com/callback"]

    def test_rejects_non_http_scheme(self) -> None:
        """Non-HTTP(S) schemes should be rejected."""
        with pytest.raises(ValidationError):
            OAuthClientRegistrationRequest(
                redirect_uris=["ftp://example.com/callback"],
            )


class TestDashboardStatsBounds:
    """Test dashboard stats query limits."""

    def test_dashboard_cache_variables_exist(self) -> None:
        """Verify dashboard cache infrastructure exists."""
        from src import server

        assert hasattr(server, "_dashboard_stats_cache")
        assert hasattr(server, "_DASHBOARD_CACHE_TTL_SECONDS")
        assert server._DASHBOARD_CACHE_TTL_SECONDS == 60
