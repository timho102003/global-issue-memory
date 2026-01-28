"""Tests for JWT service."""

import time
from uuid import uuid4

import pytest

from src.auth.jwt_service import JWTService
from src.auth.models import JWTClaims


class TestJWTService:
    """Tests for JWTService class."""

    @pytest.fixture
    def jwt_service(self) -> JWTService:
        """Create a JWT service instance for testing."""
        return JWTService(
            secret_key="test-secret-key-minimum-32-characters-long",
            issuer="test-issuer",
            audience="test-audience",
            ttl_hours=1,
        )

    def test_create_token_returns_valid_response(
        self,
        jwt_service: JWTService,
    ) -> None:
        """Test that create_token returns a valid TokenResponse."""
        gim_id = uuid4()
        identity_id = uuid4()

        response = jwt_service.create_token(gim_id, identity_id)

        assert response.access_token is not None
        assert response.token_type == "Bearer"
        assert response.expires_in == 3600  # 1 hour in seconds

    def test_create_token_produces_verifiable_token(
        self,
        jwt_service: JWTService,
    ) -> None:
        """Test that created tokens can be verified."""
        gim_id = uuid4()
        identity_id = uuid4()

        response = jwt_service.create_token(gim_id, identity_id)
        claims = jwt_service.verify_token(response.access_token)

        assert claims is not None
        assert claims.sub == str(gim_id)
        assert claims.gim_identity_id == str(identity_id)
        assert claims.iss == "test-issuer"
        assert claims.aud == "test-audience"

    def test_verify_token_returns_none_for_invalid_token(
        self,
        jwt_service: JWTService,
    ) -> None:
        """Test that verify_token returns None for invalid tokens."""
        claims = jwt_service.verify_token("invalid-token")
        assert claims is None

    def test_verify_token_returns_none_for_wrong_secret(
        self,
        jwt_service: JWTService,
    ) -> None:
        """Test that tokens signed with different secrets fail verification."""
        gim_id = uuid4()
        identity_id = uuid4()

        response = jwt_service.create_token(gim_id, identity_id)

        # Create a service with different secret
        other_service = JWTService(
            secret_key="different-secret-key-32-characters-min",
            issuer="test-issuer",
            audience="test-audience",
            ttl_hours=1,
        )

        claims = other_service.verify_token(response.access_token)
        assert claims is None

    def test_verify_token_returns_none_for_wrong_issuer(
        self,
    ) -> None:
        """Test that tokens with wrong issuer fail verification."""
        gim_id = uuid4()
        identity_id = uuid4()

        # Create token with one issuer
        service1 = JWTService(
            secret_key="test-secret-key-minimum-32-characters-long",
            issuer="issuer-1",
            audience="test-audience",
            ttl_hours=1,
        )
        response = service1.create_token(gim_id, identity_id)

        # Verify with different issuer expectation
        service2 = JWTService(
            secret_key="test-secret-key-minimum-32-characters-long",
            issuer="issuer-2",
            audience="test-audience",
            ttl_hours=1,
        )
        claims = service2.verify_token(response.access_token)
        assert claims is None

    def test_verify_token_returns_none_for_wrong_audience(
        self,
    ) -> None:
        """Test that tokens with wrong audience fail verification."""
        gim_id = uuid4()
        identity_id = uuid4()

        # Create token with one audience
        service1 = JWTService(
            secret_key="test-secret-key-minimum-32-characters-long",
            issuer="test-issuer",
            audience="audience-1",
            ttl_hours=1,
        )
        response = service1.create_token(gim_id, identity_id)

        # Verify with different audience expectation
        service2 = JWTService(
            secret_key="test-secret-key-minimum-32-characters-long",
            issuer="test-issuer",
            audience="audience-2",
            ttl_hours=1,
        )
        claims = service2.verify_token(response.access_token)
        assert claims is None

    def test_get_gim_id_from_token(
        self,
        jwt_service: JWTService,
    ) -> None:
        """Test extracting GIM ID from token."""
        gim_id = uuid4()
        identity_id = uuid4()

        response = jwt_service.create_token(gim_id, identity_id)
        extracted_id = jwt_service.get_gim_id_from_token(response.access_token)

        assert extracted_id == gim_id

    def test_get_identity_id_from_token(
        self,
        jwt_service: JWTService,
    ) -> None:
        """Test extracting identity ID from token."""
        gim_id = uuid4()
        identity_id = uuid4()

        response = jwt_service.create_token(gim_id, identity_id)
        extracted_id = jwt_service.get_identity_id_from_token(response.access_token)

        assert extracted_id == identity_id

    def test_get_gim_id_from_invalid_token_returns_none(
        self,
        jwt_service: JWTService,
    ) -> None:
        """Test that invalid tokens return None for GIM ID extraction."""
        extracted_id = jwt_service.get_gim_id_from_token("invalid-token")
        assert extracted_id is None

    def test_token_contains_expected_claims(
        self,
        jwt_service: JWTService,
    ) -> None:
        """Test that tokens contain all expected claims."""
        gim_id = uuid4()
        identity_id = uuid4()

        response = jwt_service.create_token(gim_id, identity_id)
        claims = jwt_service.verify_token(response.access_token)

        assert claims is not None
        assert claims.sub == str(gim_id)
        assert claims.iss == "test-issuer"
        assert claims.aud == "test-audience"
        assert claims.gim_identity_id == str(identity_id)
        assert claims.exp > claims.iat
        assert claims.exp - claims.iat == 3600  # 1 hour TTL
