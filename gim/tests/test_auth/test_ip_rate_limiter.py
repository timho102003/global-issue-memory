"""Tests for IP rate limiter functionality."""

from unittest.mock import MagicMock, patch

import pytest

from src.auth.ip_rate_limiter import (
    IPRateLimiter,
    get_client_ip,
    get_submit_issue_rate_limiter,
)


class TestGetClientIP:
    """Tests for get_client_ip() header extraction."""

    def _make_request(self, headers=None, client_host=None):
        """Create a mock Starlette request."""
        request = MagicMock()
        request.headers = headers or {}
        if client_host:
            request.client = MagicMock()
            request.client.host = client_host
        else:
            request.client = None
        return request

    def test_cloudflare_header_priority(self):
        """CF-Connecting-IP takes priority over all other headers when trusted."""
        request = self._make_request(
            headers={
                "CF-Connecting-IP": "1.2.3.4",
                "X-Forwarded-For": "5.6.7.8, 9.10.11.12",
            },
            client_host="127.0.0.1",
        )
        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(trust_proxy_headers=True)
            assert get_client_ip(request) == "1.2.3.4"

    def test_forwarded_for_fallback(self):
        """X-Forwarded-For first entry used when no CF header and trusted."""
        request = self._make_request(
            headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2, 10.0.0.3"},
            client_host="127.0.0.1",
        )
        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(trust_proxy_headers=True)
            assert get_client_ip(request) == "10.0.0.1"

    def test_direct_connection_fallback(self):
        """request.client.host used when no proxy headers."""
        request = self._make_request(client_host="192.168.1.100")
        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(trust_proxy_headers=False)
            assert get_client_ip(request) == "192.168.1.100"

    def test_unknown_when_no_client_info(self):
        """Returns 'unknown' when no headers or client info available."""
        request = self._make_request()
        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(trust_proxy_headers=False)
            assert get_client_ip(request) == "unknown"

    def test_strips_whitespace(self):
        """Strips whitespace from header values."""
        request = self._make_request(
            headers={"CF-Connecting-IP": "  1.2.3.4  "}
        )
        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(trust_proxy_headers=True)
            assert get_client_ip(request) == "1.2.3.4"

    def test_proxy_headers_ignored_when_not_trusted(self):
        """Proxy headers are ignored when trust_proxy_headers is False."""
        request = self._make_request(
            headers={
                "CF-Connecting-IP": "1.2.3.4",
                "X-Forwarded-For": "5.6.7.8",
            },
            client_host="192.168.1.1",
        )
        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(trust_proxy_headers=False)
            assert get_client_ip(request) == "192.168.1.1"


class TestSubmitIssueRateLimiter:
    """Tests for submit issue rate limiter singleton."""

    def test_singleton_reads_config(self):
        """Singleton reads limits from config settings."""
        import src.auth.ip_rate_limiter as module
        # Reset singleton
        module._submit_issue_limiter = None

        with patch("src.config.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                ip_submit_max_requests=10,
                ip_submit_window_seconds=1800,
            )
            limiter = get_submit_issue_rate_limiter()
            assert limiter._max_requests == 10
            assert limiter._window_seconds == 1800

        # Reset singleton after test
        module._submit_issue_limiter = None

    def test_enforces_limit(self):
        """Blocks requests after max_requests exceeded."""
        limiter = IPRateLimiter(max_requests=3, window_seconds=3600)
        ip = "10.0.0.1"

        assert limiter.is_allowed(ip) is True
        assert limiter.is_allowed(ip) is True
        assert limiter.is_allowed(ip) is True
        assert limiter.is_allowed(ip) is False  # 4th request blocked

    def test_independent_per_ip(self):
        """Different IPs are tracked independently."""
        limiter = IPRateLimiter(max_requests=2, window_seconds=3600)

        assert limiter.is_allowed("10.0.0.1") is True
        assert limiter.is_allowed("10.0.0.1") is True
        assert limiter.is_allowed("10.0.0.1") is False  # IP1 blocked

        # IP2 should still be allowed
        assert limiter.is_allowed("10.0.0.2") is True
        assert limiter.is_allowed("10.0.0.2") is True

    def test_window_expiration_allows_new_requests(self):
        """Requests are allowed again after the window expires."""
        limiter = IPRateLimiter(max_requests=2, window_seconds=60)
        ip = "10.0.0.1"

        with patch("src.auth.ip_rate_limiter.time") as mock_time:
            mock_time.time.return_value = 1000.0
            assert limiter.is_allowed(ip) is True
            assert limiter.is_allowed(ip) is True
            assert limiter.is_allowed(ip) is False

            # Advance time past the window
            mock_time.time.return_value = 1061.0
            assert limiter.is_allowed(ip) is True  # Should be allowed again

    def test_periodic_cleanup_removes_stale_ips(self):
        """Stale IP entries are cleaned up after 100 calls."""
        limiter = IPRateLimiter(max_requests=1000, window_seconds=60)

        with patch("src.auth.ip_rate_limiter.time") as mock_time:
            # Add entries at time 1000
            mock_time.time.return_value = 1000.0
            for i in range(99):
                limiter.is_allowed(f"10.0.0.{i}")

            # All 99 IPs should be tracked
            assert len(limiter._requests) == 99

            # Advance time past the window so all entries are stale
            mock_time.time.return_value = 1061.0

            # 100th call triggers cleanup
            limiter.is_allowed("10.0.0.200")

            # Only the new IP should remain (stale ones cleaned up)
            assert "10.0.0.200" in limiter._requests
            # Stale IPs should have been removed
            assert "10.0.0.0" not in limiter._requests

    def test_get_remaining_cleans_stale_entries(self):
        """get_remaining removes stale IP entries."""
        limiter = IPRateLimiter(max_requests=5, window_seconds=60)

        with patch("src.auth.ip_rate_limiter.time") as mock_time:
            mock_time.time.return_value = 1000.0
            limiter.is_allowed("10.0.0.1")
            assert "10.0.0.1" in limiter._requests

            # Advance past window
            mock_time.time.return_value = 1061.0
            remaining = limiter.get_remaining("10.0.0.1")
            assert remaining == 5
            # Stale entry should be cleaned up
            assert "10.0.0.1" not in limiter._requests
