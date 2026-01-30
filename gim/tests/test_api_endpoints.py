"""Tests for REST API endpoints in server.py.

These tests verify the API endpoint logic and response formats.
Run with: pytest tests/test_api_endpoints.py -v

Note: These tests require the MCP/FastMCP dependencies to be installed.
Use a virtual environment with `pip install -e ".[dev]"` first.
"""

import json
from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

# Mark all tests as requiring the full test environment
pytestmark = pytest.mark.integration


@pytest.fixture
def sample_uuid() -> str:
    """Generate a sample UUID string for testing.

    Returns:
        str: A UUID string.
    """
    return str(uuid4())


@pytest.fixture
def mock_search_result():
    """Mock search tool result."""
    return [{
        "issue_id": str(uuid4()),
        "similarity_score": 0.85,
        "canonical_error": "ModuleNotFoundError: No module named 'fastapi'",
        "root_cause": "Package not installed",
        "root_cause_category": "missing_dependency",
        "verification_count": 5,
        "has_fix_bundle": True,
        "fix_summary": "Install fastapi using pip",
    }]


@pytest.fixture
def mock_issue(sample_uuid):
    """Mock master issue record."""
    return {
        "id": sample_uuid,
        "canonical_error": "Test error message",
        "root_cause": "Test root cause",
        "root_cause_category": "missing_dependency",
        "verification_count": 3,
        "created_at": "2024-01-01T00:00:00Z",
        "last_verified_at": "2024-01-02T00:00:00Z",
    }


@pytest.fixture
def mock_fix_bundle(sample_uuid):
    """Mock fix bundle data."""
    return {
        "id": str(uuid4()),
        "summary": "Install the missing package",
        "fix_steps": ["Run pip install fastapi"],
        "code_changes": [],
        "environment_actions": [{"action": "install", "package": "fastapi"}],
        "constraints": {},
        "verification_steps": [{"step": "Import fastapi", "expected_output": "No error"}],
        "confidence_score": 0.9,
        "verification_count": 5,
    }


class TestSearchIssuesEndpoint:
    """Tests for POST /mcp/tools/gim_search_issues endpoint."""

    @pytest.mark.asyncio
    async def test_search_issues_returns_results(self, mock_search_result):
        """Test that search returns results in expected format."""
        try:
            from src.server import create_mcp_server
            from src.db.qdrant_client import ensure_collection_exists
            from src.tools.gim_search_issues import search_issues_tool
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_text = MagicMock()
        mock_text.text = json.dumps({
            "success": True,
            "message": "Found 1 matching issue(s)",
            "results": mock_search_result,
            "sanitization_warnings": [],
        })

        with patch.object(search_issues_tool, "execute",
                          new_callable=AsyncMock, return_value=[mock_text]):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.post(
                    "/mcp/tools/gim_search_issues",
                    json={"arguments": {"query": "ModuleNotFoundError"}},
                )

                assert response.status_code == 200
                data = response.json()
                assert "issues" in data
                assert "total" in data
                assert data["total"] >= 0

    @pytest.mark.asyncio
    async def test_search_issues_empty_query(self):
        """Test search with empty query returns empty results."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=0):
            with patch.object(server_module, "query_records", new_callable=AsyncMock, return_value=[]):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {}},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["issues"] == []
                    assert data["total"] == 0


class TestGetIssueEndpoint:
    """Tests for GET /issues/{issue_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_issue_valid_id(self, sample_uuid, mock_issue):
        """Test getting a valid issue by ID."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch.object(server_module, "get_record", new_callable=AsyncMock, return_value=mock_issue):
            with patch.object(server_module, "query_records", new_callable=AsyncMock, return_value=[]):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.get(f"/issues/{sample_uuid}")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["id"] == sample_uuid

    @pytest.mark.asyncio
    async def test_get_issue_not_found(self, sample_uuid):
        """Test getting a non-existent issue returns 404."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch.object(server_module, "get_record", new_callable=AsyncMock, return_value=None):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.get(f"/issues/{sample_uuid}")

                assert response.status_code == 404
                data = response.json()
                assert data["error"] == "not_found"

    @pytest.mark.asyncio
    async def test_get_issue_invalid_uuid(self):
        """Test getting an issue with invalid UUID returns 400."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
            mcp = create_mcp_server(use_auth=False)
            client = TestClient(mcp.app)

            response = client.get("/issues/invalid-uuid")

            assert response.status_code == 400
            data = response.json()
            assert data["error"] == "invalid_request"


class TestGetFixBundleEndpoint:
    """Tests for POST /mcp/tools/gim_get_fix_bundle endpoint."""

    @pytest.mark.asyncio
    async def test_get_fix_bundle_success(self, sample_uuid, mock_fix_bundle):
        """Test getting fix bundle returns expected format."""
        try:
            from src.server import create_mcp_server
            from src.tools.gim_get_fix_bundle import get_fix_bundle_tool
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_text = MagicMock()
        mock_text.text = json.dumps({
            "success": True,
            "issue_id": sample_uuid,
            "fix_bundle": mock_fix_bundle,
        })

        with patch.object(get_fix_bundle_tool, "execute",
                          new_callable=AsyncMock, return_value=[mock_text]):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.post(
                    "/mcp/tools/gim_get_fix_bundle",
                    json={"arguments": {"issue_id": sample_uuid}},
                )

                assert response.status_code == 200
                data = response.json()
                assert "content" in data
                assert len(data["content"]) > 0

    @pytest.mark.asyncio
    async def test_get_fix_bundle_no_bundle(self, sample_uuid):
        """Test getting fix bundle when none exists."""
        try:
            from src.server import create_mcp_server
            from src.tools.gim_get_fix_bundle import get_fix_bundle_tool
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_text = MagicMock()
        mock_text.text = json.dumps({
            "success": True,
            "issue_id": sample_uuid,
            "message": "No fix bundle available for this issue",
            "fix_bundle": None,
        })

        with patch.object(get_fix_bundle_tool, "execute",
                          new_callable=AsyncMock, return_value=[mock_text]):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.post(
                    "/mcp/tools/gim_get_fix_bundle",
                    json={"arguments": {"issue_id": sample_uuid}},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["content"] == []

    @pytest.mark.asyncio
    async def test_get_fix_bundle_missing_issue_id(self):
        """Test getting fix bundle without issue_id returns error."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
            mcp = create_mcp_server(use_auth=False)
            client = TestClient(mcp.app)

            response = client.post(
                "/mcp/tools/gim_get_fix_bundle",
                json={"arguments": {}},
            )

            assert response.status_code == 400
            data = response.json()
            assert data["error"] == "invalid_request"


class TestSubmitIssueEndpoint:
    """Tests for POST /mcp/tools/gim_submit_issue endpoint."""

    @pytest.mark.asyncio
    async def test_submit_issue_requires_auth(self):
        """Test that submit issue requires authentication."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
            mcp = create_mcp_server(use_auth=False)
            client = TestClient(mcp.app)

            response = client.post(
                "/mcp/tools/gim_submit_issue",
                json={"arguments": {"error_message": "Test error"}},
            )

            assert response.status_code == 401
            data = response.json()
            assert data["error"] == "unauthorized"

    @pytest.mark.asyncio
    async def test_submit_issue_with_auth(self, sample_uuid):
        """Test submitting issue with valid auth token."""
        try:
            from src.server import create_mcp_server
            from src.tools.gim_submit_issue import submit_issue_tool
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_text = MagicMock()
        mock_text.text = json.dumps({
            "success": True,
            "message": "Issue submitted successfully",
            "issue_id": sample_uuid,
            "fix_bundle_id": str(uuid4()),
            "type": "master_issue",
            "linked_to": None,
        })

        with patch.object(submit_issue_tool, "execute",
                          new_callable=AsyncMock, return_value=[mock_text]):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.post(
                    "/mcp/tools/gim_submit_issue",
                    json={
                        "arguments": {
                            "error_message": "Test error",
                            "root_cause": "Test cause",
                            "fix_summary": "Test fix",
                            "fix_steps": ["Step 1"],
                        }
                    },
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 201
                data = response.json()
                assert "id" in data


class TestConfirmFixEndpoint:
    """Tests for POST /mcp/tools/gim_confirm_fix endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_fix_requires_auth(self, sample_uuid):
        """Test that confirm fix requires authentication."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
            mcp = create_mcp_server(use_auth=False)
            client = TestClient(mcp.app)

            response = client.post(
                "/mcp/tools/gim_confirm_fix",
                json={
                    "arguments": {
                        "issue_id": sample_uuid,
                        "success": True,
                    }
                },
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_confirm_fix_success(self, sample_uuid):
        """Test confirming a fix with valid auth."""
        try:
            from src.server import create_mcp_server
            from src.tools.gim_confirm_fix import confirm_fix_tool
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_text = MagicMock()
        mock_text.text = json.dumps({
            "success": True,
            "message": "Fix confirmation recorded",
            "issue_id": sample_uuid,
            "fix_bundle_id": str(uuid4()),
            "fix_worked": True,
        })

        with patch.object(confirm_fix_tool, "execute",
                          new_callable=AsyncMock, return_value=[mock_text]):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.post(
                    "/mcp/tools/gim_confirm_fix",
                    json={
                        "arguments": {
                            "issue_id": sample_uuid,
                            "fix_bundle_id": str(uuid4()),
                            "success": True,
                            "notes": "Fix worked perfectly",
                        }
                    },
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["confirmed"] is True


class TestDashboardStatsEndpoint:
    """Tests for GET /dashboard/stats endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_stats_returns_data(self):
        """Test that dashboard stats returns expected format."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_issues = [
            {
                "id": str(uuid4()),
                "root_cause_category": "missing_dependency",
                "model_provider": "anthropic",
                "verification_count": 5,
            },
            {
                "id": str(uuid4()),
                "root_cause_category": "configuration_error",
                "model_provider": "openai",
                "verification_count": 2,
            },
        ]

        mock_events = [
            {
                "id": str(uuid4()),
                "event_type": "issue_submitted",
                "issue_id": str(uuid4()),
                "provider": "anthropic",
                "created_at": "2024-01-01T00:00:00Z",
            },
        ]

        async def mock_query_records(table, **kwargs):
            if table == "master_issues":
                return mock_issues
            elif table == "usage_events":
                return mock_events
            elif table == "child_issues":
                return []
            return []

        with patch.object(server_module, "query_records", side_effect=mock_query_records):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.get("/dashboard/stats")

                assert response.status_code == 200
                data = response.json()
                assert "total_issues" in data
                assert "resolved_issues" in data
                assert "unverified_issues" in data
                assert "total_contributors" in data
                assert "issues_by_category" in data
                assert "issues_by_provider" in data
                assert "recent_activity" in data

    @pytest.mark.asyncio
    async def test_dashboard_stats_empty_db(self):
        """Test dashboard stats with empty database."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch.object(server_module, "query_records", new_callable=AsyncMock, return_value=[]):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.get("/dashboard/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["total_issues"] == 0
                assert data["resolved_issues"] == 0
                assert data["unverified_issues"] == 0

    @pytest.mark.asyncio
    async def test_dashboard_stats_resolved_threshold_boundary(self):
        """Test that verification_count >= 1 counts as resolved."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_issues = [
            {
                "id": str(uuid4()),
                "root_cause_category": "missing_dependency",
                "model_provider": "anthropic",
                "verification_count": 0,
            },
            {
                "id": str(uuid4()),
                "root_cause_category": "configuration_error",
                "model_provider": "openai",
                "verification_count": 1,
            },
            {
                "id": str(uuid4()),
                "root_cause_category": "runtime_error",
                "model_provider": "anthropic",
                "verification_count": 5,
            },
        ]

        async def mock_query_records(table, **kwargs):
            if table == "master_issues":
                return mock_issues
            elif table == "usage_events":
                return []
            elif table == "child_issues":
                return []
            return []

        with patch.object(server_module, "query_records", side_effect=mock_query_records):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.get("/dashboard/stats")

                assert response.status_code == 200
                data = response.json()
                assert data["total_issues"] == 3
                assert data["resolved_issues"] == 2
                assert data["unverified_issues"] == 1


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    @pytest.mark.asyncio
    async def test_cors_allows_localhost_3000(self):
        """Test that CORS allows requests from localhost:3000."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
            mcp = create_mcp_server(use_auth=False)
            client = TestClient(mcp.app)

            response = client.options(
                "/dashboard/stats",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

            # CORS preflight should return 200
            assert response.status_code == 200
            assert "access-control-allow-origin" in response.headers

    @pytest.mark.asyncio
    async def test_cors_headers_in_response(self):
        """Test that CORS headers are present in responses."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch.object(server_module, "query_records", new_callable=AsyncMock, return_value=[]):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.get(
                    "/dashboard/stats",
                    headers={"Origin": "http://localhost:3000"},
                )

                assert response.status_code == 200
                # CORS middleware should add the header
                assert "access-control-allow-origin" in response.headers


class TestTimeRangeToIso:
    """Tests for _time_range_to_iso helper function."""

    @staticmethod
    def _import_helper():
        """Import _time_range_to_iso from server module.

        Returns:
            The _time_range_to_iso function.

        Raises:
            pytest.skip: If required dependencies are not installed.
        """
        try:
            from src.server import _time_range_to_iso
            return _time_range_to_iso
        except ImportError:
            pytest.skip("Required dependencies not installed")

    def test_valid_1d_range(self) -> None:
        """Test that '1d' returns a cutoff ~1 day ago."""
        _time_range_to_iso = self._import_helper()

        result = _time_range_to_iso("1d")
        assert result is not None
        cutoff = datetime.fromisoformat(result)
        expected = datetime.now(timezone.utc) - timedelta(days=1)
        # Allow 5 seconds of tolerance for test execution time
        assert abs((cutoff - expected).total_seconds()) < 5

    def test_valid_7d_range(self) -> None:
        """Test that '7d' returns a cutoff ~7 days ago."""
        _time_range_to_iso = self._import_helper()

        result = _time_range_to_iso("7d")
        assert result is not None
        cutoff = datetime.fromisoformat(result)
        expected = datetime.now(timezone.utc) - timedelta(days=7)
        assert abs((cutoff - expected).total_seconds()) < 5

    def test_valid_30d_range(self) -> None:
        """Test that '30d' returns a cutoff ~30 days ago."""
        _time_range_to_iso = self._import_helper()

        result = _time_range_to_iso("30d")
        assert result is not None
        cutoff = datetime.fromisoformat(result)
        expected = datetime.now(timezone.utc) - timedelta(days=30)
        assert abs((cutoff - expected).total_seconds()) < 5

    def test_valid_90d_range(self) -> None:
        """Test that '90d' returns a cutoff ~90 days ago."""
        _time_range_to_iso = self._import_helper()

        result = _time_range_to_iso("90d")
        assert result is not None
        cutoff = datetime.fromisoformat(result)
        expected = datetime.now(timezone.utc) - timedelta(days=90)
        assert abs((cutoff - expected).total_seconds()) < 5

    def test_invalid_range_returns_none(self) -> None:
        """Test that an unrecognized range string returns None."""
        _time_range_to_iso = self._import_helper()

        assert _time_range_to_iso("2d") is None
        assert _time_range_to_iso("") is None
        assert _time_range_to_iso("all") is None
        assert _time_range_to_iso("1w") is None

    def test_returns_iso_format_string(self) -> None:
        """Test that the result is a valid ISO format string."""
        _time_range_to_iso = self._import_helper()

        result = _time_range_to_iso("7d")
        assert result is not None
        # Should be parseable as ISO datetime
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo is not None  # Should be timezone-aware


class TestSearchIssuesProviderFilter:
    """Tests for provider filter in the no-query search path."""

    @pytest.mark.asyncio
    async def test_provider_filter_passed_to_query(self) -> None:
        """Test that provider argument is mapped to model_provider filter."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        captured_kwargs = {}

        async def mock_query_records(table, **kwargs):
            if table == "master_issues":
                captured_kwargs.update(kwargs)
                return []
            return []

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=0):
            with patch.object(server_module, "query_records", side_effect=mock_query_records):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {"provider": "anthropic"}},
                    )

                    assert response.status_code == 200
                    # Verify that model_provider was passed in filters
                    filters = captured_kwargs.get("filters")
                    assert filters is not None
                    assert filters.get("model_provider") == "anthropic"

    @pytest.mark.asyncio
    async def test_no_provider_filter_when_not_specified(self) -> None:
        """Test that no model_provider filter is applied when provider is absent."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        captured_kwargs = {}

        async def mock_query_records(table, **kwargs):
            if table == "master_issues":
                captured_kwargs.update(kwargs)
                return []
            return []

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=0):
            with patch.object(server_module, "query_records", side_effect=mock_query_records):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {}},
                    )

                    assert response.status_code == 200
                    filters = captured_kwargs.get("filters")
                    # When no filters, filters should be None
                    assert filters is None or "model_provider" not in filters


class TestSearchIssuesTimeRangeFilter:
    """Tests for time_range filter in the no-query search path."""

    @pytest.mark.asyncio
    async def test_time_range_passed_as_gte_filter(self) -> None:
        """Test that time_range argument is converted to gte_filters."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        captured_kwargs = {}

        async def mock_query_records(table, **kwargs):
            if table == "master_issues":
                captured_kwargs.update(kwargs)
                return []
            return []

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=0):
            with patch.object(server_module, "query_records", side_effect=mock_query_records):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {"time_range": "7d"}},
                    )

                    assert response.status_code == 200
                    gte_filters = captured_kwargs.get("gte_filters")
                    assert gte_filters is not None
                    assert "created_at" in gte_filters
                    # Verify the cutoff is approximately 7 days ago
                    cutoff = datetime.fromisoformat(gte_filters["created_at"])
                    expected = datetime.now(timezone.utc) - timedelta(days=7)
                    assert abs((cutoff - expected).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_invalid_time_range_no_gte_filter(self) -> None:
        """Test that an invalid time_range does not create gte_filters."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        captured_kwargs = {}

        async def mock_query_records(table, **kwargs):
            if table == "master_issues":
                captured_kwargs.update(kwargs)
                return []
            return []

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=0):
            with patch.object(server_module, "query_records", side_effect=mock_query_records):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {"time_range": "invalid"}},
                    )

                    assert response.status_code == 200
                    gte_filters = captured_kwargs.get("gte_filters")
                    assert gte_filters is None

    @pytest.mark.asyncio
    async def test_no_time_range_no_gte_filter(self) -> None:
        """Test that missing time_range does not create gte_filters."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        captured_kwargs = {}

        async def mock_query_records(table, **kwargs):
            if table == "master_issues":
                captured_kwargs.update(kwargs)
                return []
            return []

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=0):
            with patch.object(server_module, "query_records", side_effect=mock_query_records):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {}},
                    )

                    assert response.status_code == 200
                    gte_filters = captured_kwargs.get("gte_filters")
                    assert gte_filters is None

    @pytest.mark.asyncio
    async def test_combined_provider_and_time_range(self) -> None:
        """Test that provider and time_range filters work together."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        captured_kwargs = {}

        async def mock_query_records(table, **kwargs):
            if table == "master_issues":
                captured_kwargs.update(kwargs)
                return []
            return []

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=0):
            with patch.object(server_module, "query_records", side_effect=mock_query_records):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {
                            "provider": "openai",
                            "time_range": "30d",
                            "status": "active",
                        }},
                    )

                    assert response.status_code == 200
                    filters = captured_kwargs.get("filters")
                    assert filters is not None
                    assert filters.get("model_provider") == "openai"
                    assert filters.get("status") == "active"

                    gte_filters = captured_kwargs.get("gte_filters")
                    assert gte_filters is not None
                    assert "created_at" in gte_filters


class TestGetIssueChildResolution:
    """Tests for child ID resolution in GET /issues/{issue_id}."""

    @pytest.mark.asyncio
    async def test_get_issue_child_id_returns_child_format(self):
        """Test that passing a child UUID returns child-specific response format.

        When resolve_issue_id identifies the ID as a child issue and finds
        both the child and its master, the response should include
        is_child_issue=True plus parent context fields.
        """
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        child_id = str(uuid4())
        master_id = str(uuid4())

        mock_master = {
            "id": master_id,
            "canonical_error": "ImportError: cannot import name 'foo'",
            "root_cause": "Module renamed in v2",
            "root_cause_category": "breaking_change",
            "verification_count": 4,
            "created_at": "2024-03-01T00:00:00Z",
        }
        mock_child = {
            "id": child_id,
            "master_issue_id": master_id,
            "original_error": "ImportError: cannot import name 'foo' from 'bar'",
            "original_context": "Upgrading bar from v1 to v2",
            "code_snippet": "from bar import foo",
            "model": "claude-3-opus",
            "provider": "anthropic",
            "language": "python",
            "framework": "fastapi",
            "created_at": "2024-03-02T00:00:00Z",
            "contribution_type": "new_occurrence",
            "validation_success": True,
            "metadata": {"env": "production"},
        }

        with patch(
            "src.server.resolve_issue_id",
            new_callable=AsyncMock,
            return_value=(mock_master, mock_child, True),
        ):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.get(f"/issues/{child_id}")

                assert response.status_code == 200
                data = response.json()
                assert data["is_child_issue"] is True
                assert data["id"] == child_id
                assert data["master_issue_id"] == master_id
                assert data["original_error"] == mock_child["original_error"]
                assert data["original_context"] == mock_child["original_context"]
                assert data["code_snippet"] == mock_child["code_snippet"]
                assert data["provider"] == "anthropic"
                assert data["language"] == "python"
                assert data["framework"] == "fastapi"
                # Parent context fields
                assert "parent_canonical_title" in data
                assert data["parent_canonical_title"] == mock_master["canonical_error"][:100]
                assert data["parent_root_cause_category"] == "breaking_change"

    @pytest.mark.asyncio
    async def test_get_issue_child_id_orphaned(self):
        """Test that an orphaned child (no master) returns 200 with child data but no parent fields.

        When a child issue exists but its master_issue_id references a
        non-existent master, resolve_issue_id returns (None, child, True).
        The endpoint should still return the child data without parent context.
        """
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        child_id = str(uuid4())
        master_id = str(uuid4())

        mock_child = {
            "id": child_id,
            "master_issue_id": master_id,
            "original_error": "RuntimeError: event loop closed",
            "original_context": "Running async tests",
            "code_snippet": "asyncio.run(main())",
            "model": "gpt-4",
            "provider": "openai",
            "language": "python",
            "framework": "pytest",
            "created_at": "2024-04-01T00:00:00Z",
            "contribution_type": "new_occurrence",
            "validation_success": False,
            "metadata": {},
        }

        with patch(
            "src.server.resolve_issue_id",
            new_callable=AsyncMock,
            return_value=(None, mock_child, True),
        ):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.get(f"/issues/{child_id}")

                assert response.status_code == 200
                data = response.json()
                assert data["is_child_issue"] is True
                assert data["id"] == child_id
                assert data["master_issue_id"] == master_id
                assert data["original_error"] == mock_child["original_error"]
                assert data["provider"] == "openai"
                # Parent context fields should NOT be present for orphans
                assert "parent_canonical_title" not in data
                assert "parent_root_cause_category" not in data


class TestListChildIssuesEndpoint:
    """Tests for GET /issues/{issue_id}/children endpoint."""

    @pytest.mark.asyncio
    async def test_list_children_success(self):
        """Test listing children for a master issue returns expected format.

        Given a valid master issue with 2 child issues, the endpoint should
        return a 200 with a children list, total count, and pagination info.
        """
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        master_id = str(uuid4())
        mock_master = {
            "id": master_id,
            "canonical_error": "ValueError: invalid literal",
            "root_cause": "Type mismatch",
            "root_cause_category": "type_error",
        }

        child1_id = str(uuid4())
        child2_id = str(uuid4())
        mock_children = [
            {
                "id": child1_id,
                "master_issue_id": master_id,
                "original_error": "ValueError: invalid literal for int()",
                "provider": "anthropic",
                "language": "python",
                "framework": "django",
                "created_at": "2024-05-02T00:00:00Z",
                "contribution_type": "new_occurrence",
                "model": "claude-3-sonnet",
                "validation_success": True,
            },
            {
                "id": child2_id,
                "master_issue_id": master_id,
                "original_error": "ValueError: could not convert string to float",
                "provider": "openai",
                "language": "python",
                "framework": "flask",
                "created_at": "2024-05-01T00:00:00Z",
                "contribution_type": "new_occurrence",
                "model": "gpt-4",
                "validation_success": False,
            },
        ]

        with patch.object(
            server_module, "get_record", new_callable=AsyncMock, return_value=mock_master
        ):
            with patch.object(
                server_module, "query_records", new_callable=AsyncMock, return_value=mock_children
            ):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.get(f"/issues/{master_id}/children")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["master_issue_id"] == master_id
                    assert data["total"] == 2
                    assert data["limit"] == 50
                    assert data["offset"] == 0
                    assert len(data["children"]) == 2
                    # Verify child structure
                    first_child = data["children"][0]
                    assert first_child["id"] == child1_id
                    assert first_child["master_issue_id"] == master_id
                    assert first_child["original_error"] == mock_children[0]["original_error"]
                    assert first_child["provider"] == "anthropic"
                    assert first_child["model_name"] == "claude-3-sonnet"
                    assert first_child["validation_success"] is True

    @pytest.mark.asyncio
    async def test_list_children_empty(self):
        """Test listing children for a master issue with no children returns empty list."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        master_id = str(uuid4())
        mock_master = {
            "id": master_id,
            "canonical_error": "KeyError: 'missing_key'",
            "root_cause": "Dictionary key not found",
            "root_cause_category": "key_error",
        }

        with patch.object(
            server_module, "get_record", new_callable=AsyncMock, return_value=mock_master
        ):
            with patch.object(
                server_module, "query_records", new_callable=AsyncMock, return_value=[]
            ):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.get(f"/issues/{master_id}/children")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["children"] == []
                    assert data["total"] == 0
                    assert data["master_issue_id"] == master_id

    @pytest.mark.asyncio
    async def test_list_children_invalid_uuid(self):
        """Test that an invalid UUID returns 400 with invalid_request error."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
            mcp = create_mcp_server(use_auth=False)
            client = TestClient(mcp.app)

            response = client.get("/issues/invalid-uuid/children")

            assert response.status_code == 400
            data = response.json()
            assert data["error"] == "invalid_request"

    @pytest.mark.asyncio
    async def test_list_children_master_not_found(self):
        """Test that a valid UUID for a non-existent master returns 404."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        missing_id = str(uuid4())

        with patch.object(
            server_module, "get_record", new_callable=AsyncMock, return_value=None
        ):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.get(f"/issues/{missing_id}/children")

                assert response.status_code == 404
                data = response.json()
                assert data["error"] == "not_found"


class TestGetFixBundleChildResolution:
    """Tests for fix bundle endpoint when called with a child issue ID."""

    @pytest.mark.asyncio
    async def test_get_fix_bundle_child_id_resolves_to_master(self):
        """Test that the fix bundle tool handles child ID resolution internally.

        When a child issue ID is passed to gim_get_fix_bundle, the tool
        resolves it to the master and returns the fix bundle with
        master_issue_id and is_child_issue fields.
        """
        try:
            from src.server import create_mcp_server
            from src.tools.gim_get_fix_bundle import get_fix_bundle_tool
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        child_id = str(uuid4())
        master_id = str(uuid4())

        mock_text = MagicMock()
        mock_text.text = json.dumps({
            "success": True,
            "issue_id": master_id,
            "master_issue_id": master_id,
            "is_child_issue": True,
            "child_issue_id": child_id,
            "fix_bundle": {
                "id": str(uuid4()),
                "summary": "Upgrade dependency to v2",
                "fix_steps": ["pip install bar>=2.0"],
                "code_changes": [{"file": "main.py", "diff": "- from bar import foo\n+ from bar.v2 import foo"}],
                "environment_actions": [{"action": "upgrade", "package": "bar"}],
                "constraints": {},
                "verification_steps": [{"step": "Run import", "expected_output": "No error"}],
                "confidence_score": 0.85,
                "verification_count": 3,
            },
        })

        with patch.object(
            get_fix_bundle_tool, "execute",
            new_callable=AsyncMock, return_value=[mock_text],
        ):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.post(
                    "/mcp/tools/gim_get_fix_bundle",
                    json={"arguments": {"issue_id": child_id}},
                )

                assert response.status_code == 200
                data = response.json()
                assert "content" in data
                assert len(data["content"]) > 0
                # Parse the text content to verify child resolution fields
                content_text = data["content"][0]["text"]
                parsed = json.loads(content_text)
                assert parsed["master_issue_id"] == master_id
                assert parsed["is_child_issue"] is True
                assert parsed["child_issue_id"] == child_id


class TestSearchIssuesPagination:
    """Tests for pagination in the no-query search path."""

    @pytest.mark.asyncio
    async def test_search_returns_total_from_count_records(self) -> None:
        """Test that total comes from count_records, not len(issues)."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_issues = [
            {
                "id": str(uuid4()),
                "canonical_error": "Error A",
                "root_cause": "Cause A",
                "root_cause_category": "environment",
                "status": "active",
                "model_provider": "anthropic",
                "verification_count": 1,
                "environment_coverage": [],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            },
        ]

        async def mock_query(table, **kwargs):
            if table == "master_issues":
                return mock_issues
            if table == "child_issues":
                return []
            if table == "fix_bundles":
                return []
            return []

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=50):
            with patch.object(server_module, "query_records", side_effect=mock_query):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {"limit": 20}},
                    )

                    assert response.status_code == 200
                    data = response.json()
                    # total should be 50 (from count_records), not 1 (len of returned issues)
                    assert data["total"] == 50
                    assert len(data["issues"]) == 1

    @pytest.mark.asyncio
    async def test_search_passes_offset_to_query_records(self) -> None:
        """Test that offset is forwarded to query_records."""
        try:
            from src.server import create_mcp_server
            from starlette.testclient import TestClient
            import src.server as server_module
        except ImportError:
            pytest.skip("Required dependencies not installed")

        captured_kwargs = {}

        async def mock_query(table, **kwargs):
            if table == "master_issues":
                captured_kwargs.update(kwargs)
                return []
            return []

        with patch.object(server_module, "count_records", new_callable=AsyncMock, return_value=0):
            with patch.object(server_module, "query_records", side_effect=mock_query):
                with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                    mcp = create_mcp_server(use_auth=False)
                    client = TestClient(mcp.app)

                    response = client.post(
                        "/mcp/tools/gim_search_issues",
                        json={"arguments": {"limit": 20, "offset": 40}},
                    )

                    assert response.status_code == 200
                    assert captured_kwargs.get("offset") == 40
                    assert captured_kwargs.get("limit") == 20
                    data = response.json()
                    assert data["offset"] == 40
                    assert data["limit"] == 20

    @pytest.mark.asyncio
    async def test_semantic_search_total_is_len_issues(self) -> None:
        """Test that semantic search path returns len(issues) as total."""
        try:
            from src.server import create_mcp_server
            from src.tools.gim_search_issues import search_issues_tool
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_text = MagicMock()
        mock_text.text = json.dumps({
            "success": True,
            "message": "Found 2 matching issue(s)",
            "results": [
                {
                    "issue_id": str(uuid4()),
                    "similarity_score": 0.9,
                    "canonical_error": "Error 1",
                    "root_cause": "Cause 1",
                    "root_cause_category": "environment",
                    "verification_count": 3,
                    "has_fix_bundle": True,
                    "fix_summary": "Fix 1",
                },
                {
                    "issue_id": str(uuid4()),
                    "similarity_score": 0.8,
                    "canonical_error": "Error 2",
                    "root_cause": "Cause 2",
                    "root_cause_category": "api_integration",
                    "verification_count": 1,
                    "has_fix_bundle": False,
                    "fix_summary": "",
                },
            ],
            "sanitization_warnings": [],
        })

        with patch.object(search_issues_tool, "execute",
                          new_callable=AsyncMock, return_value=[mock_text]):
            with patch("src.db.qdrant_client.ensure_collection_exists", new_callable=AsyncMock):
                mcp = create_mcp_server(use_auth=False)
                client = TestClient(mcp.app)

                response = client.post(
                    "/mcp/tools/gim_search_issues",
                    json={"arguments": {"query": "some error"}},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["total"] == 2
                assert len(data["issues"]) == 2
