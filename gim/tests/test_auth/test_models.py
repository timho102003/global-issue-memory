"""Tests for auth models."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.auth.models import (
    ErrorResponse,
    GIMIdentity,
    GIMIdentityCreate,
    GIMIdentityResponse,
    GIMIdentityStatus,
    JWTClaims,
    RevokeRequest,
    TokenRequest,
    TokenResponse,
)


class TestGIMIdentityStatus:
    """Tests for GIMIdentityStatus enum."""

    def test_status_values(self) -> None:
        """Test that status enum has expected values."""
        assert GIMIdentityStatus.ACTIVE.value == "active"
        assert GIMIdentityStatus.SUSPENDED.value == "suspended"
        assert GIMIdentityStatus.REVOKED.value == "revoked"


class TestGIMIdentity:
    """Tests for GIMIdentity model."""

    def test_create_with_required_fields(self) -> None:
        """Test creating identity with required fields."""
        identity = GIMIdentity(
            id=uuid4(),
            gim_id=uuid4(),
            created_at=datetime.now(timezone.utc),
        )

        assert identity.status == GIMIdentityStatus.ACTIVE
        assert identity.daily_search_limit == 100
        assert identity.daily_search_used == 0
        assert identity.total_searches == 0

    def test_create_with_all_fields(self) -> None:
        """Test creating identity with all fields."""
        now = datetime.now(timezone.utc)
        identity = GIMIdentity(
            id=uuid4(),
            gim_id=uuid4(),
            created_at=now,
            last_used_at=now,
            status=GIMIdentityStatus.SUSPENDED,
            daily_search_limit=50,
            daily_search_used=25,
            daily_reset_at=now,
            total_searches=100,
            total_submissions=50,
            total_confirmations=30,
            total_reports=20,
            description="Test identity",
            metadata={"key": "value"},
        )

        assert identity.status == GIMIdentityStatus.SUSPENDED
        assert identity.daily_search_limit == 50
        assert identity.description == "Test identity"
        assert identity.metadata == {"key": "value"}


class TestGIMIdentityCreate:
    """Tests for GIMIdentityCreate model."""

    def test_create_empty(self) -> None:
        """Test creating with no fields."""
        request = GIMIdentityCreate()
        assert request.description is None
        assert request.metadata == {}

    def test_create_with_fields(self) -> None:
        """Test creating with optional fields."""
        request = GIMIdentityCreate(
            description="My GIM ID",
            metadata={"purpose": "testing"},
        )
        assert request.description == "My GIM ID"
        assert request.metadata == {"purpose": "testing"}


class TestTokenRequest:
    """Tests for TokenRequest model."""

    def test_create_with_uuid(self) -> None:
        """Test creating request with valid UUID."""
        gim_id = uuid4()
        request = TokenRequest(gim_id=gim_id)
        assert request.gim_id == gim_id

    def test_create_with_string_uuid(self) -> None:
        """Test creating request with string UUID."""
        gim_id = uuid4()
        request = TokenRequest(gim_id=str(gim_id))
        assert request.gim_id == gim_id


class TestTokenResponse:
    """Tests for TokenResponse model."""

    def test_create_response(self) -> None:
        """Test creating token response."""
        response = TokenResponse(
            access_token="test-token",
            expires_in=3600,
        )

        assert response.access_token == "test-token"
        assert response.token_type == "Bearer"
        assert response.expires_in == 3600


class TestJWTClaims:
    """Tests for JWTClaims model."""

    def test_create_claims(self) -> None:
        """Test creating JWT claims."""
        claims = JWTClaims(
            sub="gim-id-string",
            iss="issuer",
            aud="audience",
            exp=1234567890,
            iat=1234564290,
            gim_identity_id="identity-id-string",
        )

        assert claims.sub == "gim-id-string"
        assert claims.iss == "issuer"
        assert claims.aud == "audience"
        assert claims.exp == 1234567890
        assert claims.iat == 1234564290
        assert claims.gim_identity_id == "identity-id-string"


class TestRevokeRequest:
    """Tests for RevokeRequest model."""

    def test_create_request(self) -> None:
        """Test creating revoke request."""
        gim_id = uuid4()
        request = RevokeRequest(gim_id=gim_id)
        assert request.gim_id == gim_id


class TestGIMIdentityResponse:
    """Tests for GIMIdentityResponse model."""

    def test_create_response(self) -> None:
        """Test creating identity response."""
        gim_id = uuid4()
        now = datetime.now(timezone.utc)

        response = GIMIdentityResponse(
            gim_id=gim_id,
            created_at=now,
            description="Test",
        )

        assert response.gim_id == gim_id
        assert response.created_at == now
        assert response.description == "Test"


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_create_error(self) -> None:
        """Test creating error response."""
        error = ErrorResponse(
            error="invalid_grant",
            error_description="GIM ID not found",
        )

        assert error.error == "invalid_grant"
        assert error.error_description == "GIM ID not found"
