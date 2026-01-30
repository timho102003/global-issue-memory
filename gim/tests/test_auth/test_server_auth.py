"""Integration tests for server authentication endpoints."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from src.auth.models import GIMIdentity, GIMIdentityStatus


class TestAuthEndpoints:
    """Tests for authentication HTTP endpoints."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.jwt_secret_key = "test-secret-key-minimum-32-characters-long"
        settings.auth_issuer = "gim-mcp"
        settings.auth_audience = "gim-clients"
        settings.access_token_ttl_hours = 1
        settings.transport_mode = "http"
        settings.http_host = "127.0.0.1"
        settings.http_port = 8000
        settings.default_daily_search_limit = 100
        settings.log_level = "INFO"
        return settings

    @pytest.fixture
    def mock_identity(self):
        """Create a mock GIM identity."""
        return GIMIdentity(
            id=uuid4(),
            gim_id=uuid4(),
            created_at=datetime.now(timezone.utc),
            status=GIMIdentityStatus.ACTIVE,
            daily_search_limit=100,
            daily_search_used=0,
        )

    def test_create_gim_id_endpoint_success(
        self,
        mock_settings,
        mock_identity,
    ):
        """Test successful GIM ID creation."""
        with (
            patch("src.server.get_settings", return_value=mock_settings),
            patch("src.auth.jwt_service.get_settings", return_value=mock_settings),
            patch("src.auth.gim_id_service.get_settings", return_value=mock_settings),
            patch("src.auth.token_verifier.get_settings", return_value=mock_settings),
            patch(
                "src.server.create_fastmcp_jwt_verifier",
                return_value=None,
            ),
            patch(
                "src.auth.gim_id_service.insert_record",
                new_callable=AsyncMock,
            ) as mock_insert,
        ):
            mock_insert.return_value = {
                "id": str(mock_identity.id),
                "gim_id": str(mock_identity.gim_id),
                "created_at": mock_identity.created_at.isoformat(),
                "description": None,
            }

            from src.server import create_mcp_server

            mcp = create_mcp_server(use_auth=False)

            # Get the ASGI app for testing
            app = mcp.http_app()

            with TestClient(app) as client:
                response = client.post(
                    "/auth/gim-id",
                    json={"description": "Test GIM ID"},
                )

                assert response.status_code == 201
                data = response.json()
                assert "gim_id" in data
                assert "created_at" in data

    def test_token_exchange_success(
        self,
        mock_settings,
        mock_identity,
    ):
        """Test successful token exchange."""
        with (
            patch("src.server.get_settings", return_value=mock_settings),
            patch("src.auth.jwt_service.get_settings", return_value=mock_settings),
            patch("src.auth.gim_id_service.get_settings", return_value=mock_settings),
            patch("src.auth.token_verifier.get_settings", return_value=mock_settings),
            patch(
                "src.server.create_fastmcp_jwt_verifier",
                return_value=None,
            ),
            patch(
                "src.auth.gim_id_service.get_record",
                new_callable=AsyncMock,
            ) as mock_get,
            patch(
                "src.auth.gim_id_service.update_record",
                new_callable=AsyncMock,
            ),
        ):
            mock_get.return_value = {
                "id": str(mock_identity.id),
                "gim_id": str(mock_identity.gim_id),
                "created_at": mock_identity.created_at.isoformat(),
                "status": "active",
                "daily_search_limit": 100,
                "daily_search_used": 0,
            }

            from src.server import create_mcp_server

            mcp = create_mcp_server(use_auth=False)
            app = mcp.http_app()

            with TestClient(app) as client:
                response = client.post(
                    "/auth/token",
                    json={"gim_id": str(mock_identity.gim_id)},
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert data["token_type"] == "Bearer"
                assert "expires_in" in data

    def test_token_exchange_invalid_gim_id(
        self,
        mock_settings,
    ):
        """Test token exchange with invalid GIM ID."""
        with (
            patch("src.server.get_settings", return_value=mock_settings),
            patch("src.auth.jwt_service.get_settings", return_value=mock_settings),
            patch("src.auth.gim_id_service.get_settings", return_value=mock_settings),
            patch("src.auth.token_verifier.get_settings", return_value=mock_settings),
            patch(
                "src.server.create_fastmcp_jwt_verifier",
                return_value=None,
            ),
            patch(
                "src.auth.gim_id_service.get_record",
                new_callable=AsyncMock,
            ) as mock_get,
        ):
            mock_get.return_value = None  # GIM ID not found

            from src.server import create_mcp_server

            mcp = create_mcp_server(use_auth=False)
            app = mcp.http_app()

            with TestClient(app) as client:
                response = client.post(
                    "/auth/token",
                    json={"gim_id": str(uuid4())},
                )

                assert response.status_code == 401
                data = response.json()
                assert data["error"] == "invalid_grant"

    def test_revoke_gim_id_success(
        self,
        mock_settings,
        mock_identity,
    ):
        """Test successful GIM ID revocation."""
        mock_claims = MagicMock()
        mock_claims.sub = str(mock_identity.gim_id)
        mock_claims.gim_identity_id = str(mock_identity.id)

        with (
            patch("src.server.get_settings", return_value=mock_settings),
            patch("src.auth.jwt_service.get_settings", return_value=mock_settings),
            patch("src.auth.gim_id_service.get_settings", return_value=mock_settings),
            patch("src.auth.token_verifier.get_settings", return_value=mock_settings),
            patch(
                "src.server.create_fastmcp_jwt_verifier",
                return_value=None,
            ),
            patch("src.server.GIMTokenVerifier") as MockVerifier,
            patch(
                "src.auth.gim_id_service.get_record",
                new_callable=AsyncMock,
            ) as mock_get,
            patch(
                "src.auth.gim_id_service.update_record",
                new_callable=AsyncMock,
            ),
        ):
            MockVerifier.return_value.verify.return_value = mock_claims
            mock_get.return_value = {
                "id": str(mock_identity.id),
                "gim_id": str(mock_identity.gim_id),
                "created_at": mock_identity.created_at.isoformat(),
                "status": "active",
            }

            from src.server import create_mcp_server

            mcp = create_mcp_server(use_auth=False)
            app = mcp.http_app()

            with TestClient(app) as client:
                response = client.post(
                    "/auth/revoke",
                    json={"gim_id": str(mock_identity.gim_id)},
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_health_check(
        self,
        mock_settings,
    ):
        """Test health check endpoint."""
        with (
            patch("src.server.get_settings", return_value=mock_settings),
            patch("src.auth.jwt_service.get_settings", return_value=mock_settings),
            patch("src.auth.token_verifier.get_settings", return_value=mock_settings),
            patch(
                "src.server.create_fastmcp_jwt_verifier",
                return_value=None,
            ),
        ):
            from src.server import create_mcp_server

            mcp = create_mcp_server(use_auth=False)
            app = mcp.http_app()

            with TestClient(app) as client:
                response = client.get("/health")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["service"] == "gim-mcp"
