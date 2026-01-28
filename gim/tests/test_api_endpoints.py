"""Tests for REST API endpoints in server.py.

These tests verify the API endpoint logic and response formats.
Run with: pytest tests/test_api_endpoints.py -v

Note: These tests require the MCP/FastMCP dependencies to be installed.
Use a virtual environment with `pip install -e ".[dev]"` first.
"""

import json
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
            from src.tools.gim_search_issues import search_issues_tool
            from starlette.testclient import TestClient
        except ImportError:
            pytest.skip("Required dependencies not installed")

        mock_text = MagicMock()
        mock_text.text = json.dumps({
            "success": True,
            "message": "No matching issues found in GIM",
            "results": [],
            "sanitization_warnings": [],
        })

        with patch.object(search_issues_tool, "execute",
                          new_callable=AsyncMock, return_value=[mock_text]):
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
                assert "active_issues" in data
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
                assert data["active_issues"] == 0


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
