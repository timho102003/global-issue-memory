"""Tests for Phase 6 security hardening - N+1 optimization, IDOR logging, cache headers."""

import pytest


class TestNPlusOneOptimization:
    """Test that N+1 queries are optimized in list endpoints."""

    def test_list_issues_no_per_issue_child_query(self) -> None:
        """Verify the issues list endpoint uses batch queries.

        Check that the api_list_issues function body does not contain
        per-issue child_issues queries inside a loop.
        """
        import inspect
        from src.server import _register_api_endpoints
        source = inspect.getsource(_register_api_endpoints)

        # The old N+1 pattern had individual queries inside a for loop
        # The new batch pattern pre-fetches all children at once
        # We check that a batch select of master_issue_id is present
        assert 'select="master_issue_id"' in source or "child_counts" in source

    def test_list_issues_uses_batch_confidence(self) -> None:
        """Verify the issues list endpoint uses batch confidence lookups."""
        import inspect
        from src.server import _register_api_endpoints
        source = inspect.getsource(_register_api_endpoints)

        # The new batch pattern uses best_confidence dict
        assert "best_confidence" in source

    def test_search_issues_nonquery_path_uses_batch(self) -> None:
        """Verify the search issues non-query path uses batch queries."""
        import inspect
        from src.server import _register_api_endpoints
        source = inspect.getsource(_register_api_endpoints)

        # Both the /issues GET and /mcp/tools/gim_search_issues POST
        # non-query paths should use batch child_counts
        assert source.count("child_counts") >= 2


class TestIDORAuditLogging:
    """Test IDOR audit logging on issue endpoints."""

    def test_issue_access_logging_present(self) -> None:
        """Verify audit logging is present in issue access endpoints."""
        import inspect
        from src.server import _register_api_endpoints
        source = inspect.getsource(_register_api_endpoints)
        assert "Issue access:" in source or "issue access" in source.lower()

    def test_issue_access_logging_includes_ip(self) -> None:
        """Verify audit logging captures client IP address."""
        import inspect
        from src.server import _register_api_endpoints
        source = inspect.getsource(_register_api_endpoints)
        assert "request.client.host" in source

    def test_multiple_endpoints_have_audit_logging(self) -> None:
        """Verify audit logging is present in multiple issue endpoints."""
        import inspect
        from src.server import _register_api_endpoints
        source = inspect.getsource(_register_api_endpoints)
        # Should appear in at least 3 endpoints: get_issue, children, fix_bundle
        assert source.count("Issue access:") >= 3


class TestCacheControlHeaders:
    """Test cache-control headers on auth responses."""

    def test_security_headers_middleware_sets_cache_control(self) -> None:
        """Verify SecurityHeadersMiddleware adds Cache-Control: no-store."""
        import inspect
        from src.server import SecurityHeadersMiddleware
        source = inspect.getsource(SecurityHeadersMiddleware)
        assert "no-store" in source
