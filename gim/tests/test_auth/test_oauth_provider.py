"""Tests for OAuth 2.1 provider and PKCE utilities."""

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.auth.oauth_models import (
    OAuthAuthorizationCode,
    OAuthClient,
    OAuthClientRegistrationRequest,
    OAuthError,
    OAuthRefreshToken,
    OAuthServerMetadata,
    OAuthTokenResponse,
)
from src.auth.oauth_provider import GIMOAuthProvider
from src.auth.pkce import (
    compute_code_challenge,
    generate_authorization_code,
    generate_code_verifier,
    validate_code_verifier,
    verify_code_challenge,
)


class TestPKCE:
    """Tests for PKCE utilities."""

    def test_generate_code_verifier_default_length(self) -> None:
        """Test code verifier generation with default length."""
        verifier = generate_code_verifier()
        assert len(verifier) == 64
        assert validate_code_verifier(verifier)

    def test_generate_code_verifier_custom_length(self) -> None:
        """Test code verifier generation with custom length."""
        verifier = generate_code_verifier(length=43)
        assert len(verifier) == 43
        assert validate_code_verifier(verifier)

        verifier = generate_code_verifier(length=128)
        assert len(verifier) == 128
        assert validate_code_verifier(verifier)

    def test_generate_code_verifier_invalid_length_raises(self) -> None:
        """Test code verifier generation with invalid length raises error."""
        with pytest.raises(ValueError, match="between 43 and 128"):
            generate_code_verifier(length=42)

        with pytest.raises(ValueError, match="between 43 and 128"):
            generate_code_verifier(length=129)

    def test_generate_code_verifier_is_random(self) -> None:
        """Test that generated verifiers are unique."""
        verifiers = [generate_code_verifier() for _ in range(100)]
        assert len(set(verifiers)) == 100

    def test_compute_code_challenge_s256(self) -> None:
        """Test S256 code challenge computation."""
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        expected = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

        challenge = compute_code_challenge(verifier, method="S256")
        assert challenge == expected

    def test_compute_code_challenge_invalid_method_raises(self) -> None:
        """Test invalid challenge method raises error."""
        with pytest.raises(ValueError, match="Only S256 is supported"):
            compute_code_challenge("verifier", method="plain")  # type: ignore

    def test_verify_code_challenge_s256_valid(self) -> None:
        """Test S256 code challenge verification with valid pair."""
        verifier = generate_code_verifier()
        challenge = compute_code_challenge(verifier, method="S256")

        assert verify_code_challenge(verifier, challenge, method="S256")

    def test_verify_code_challenge_s256_invalid(self) -> None:
        """Test S256 code challenge verification with invalid verifier."""
        verifier = generate_code_verifier()
        challenge = compute_code_challenge(verifier, method="S256")

        # Different verifier should fail
        assert not verify_code_challenge("different-verifier-that-is-long-enough-for-pkce", challenge, method="S256")

    def test_verify_code_challenge_plain_not_supported(self) -> None:
        """Test plain PKCE method is not supported (OAuth 2.1 compliance)."""
        verifier = "my-plain-verifier"
        challenge = "my-plain-verifier"

        # Plain method should fail - only S256 is supported
        assert not verify_code_challenge(verifier, challenge, method="plain")

    def test_verify_code_challenge_empty_inputs(self) -> None:
        """Test verification with empty inputs returns False."""
        assert not verify_code_challenge("", "challenge")
        assert not verify_code_challenge("verifier", "")
        assert not verify_code_challenge("", "")

    def test_validate_code_verifier_valid(self) -> None:
        """Test validation of valid code verifiers."""
        assert validate_code_verifier("a" * 43)  # Minimum length
        assert validate_code_verifier("a" * 128)  # Maximum length
        assert validate_code_verifier("abcdefghijklmnopqrstuvwxyz1234567890-._~" + "a" * 10)

    def test_validate_code_verifier_invalid(self) -> None:
        """Test validation of invalid code verifiers."""
        assert not validate_code_verifier("")  # Empty
        assert not validate_code_verifier("a" * 42)  # Too short
        assert not validate_code_verifier("a" * 129)  # Too long
        assert not validate_code_verifier("a" * 43 + "!")  # Invalid character

    def test_generate_authorization_code(self) -> None:
        """Test authorization code generation."""
        code = generate_authorization_code()
        assert len(code) > 0
        # URL-safe base64 characters only
        assert all(c.isalnum() or c in "-_" for c in code)

    def test_generate_authorization_code_is_random(self) -> None:
        """Test that generated codes are unique."""
        codes = [generate_authorization_code() for _ in range(100)]
        assert len(set(codes)) == 100


class TestOAuthServerMetadata:
    """Tests for OAuth server metadata."""

    def test_server_metadata_structure(self) -> None:
        """Test server metadata has required fields."""
        metadata = OAuthServerMetadata(
            issuer="https://gim.example.com",
            authorization_endpoint="https://gim.example.com/authorize",
            token_endpoint="https://gim.example.com/token",
        )

        assert metadata.issuer == "https://gim.example.com"
        assert metadata.authorization_endpoint == "https://gim.example.com/authorize"
        assert metadata.token_endpoint == "https://gim.example.com/token"
        assert "code" in metadata.response_types_supported
        assert "authorization_code" in metadata.grant_types_supported
        assert "refresh_token" in metadata.grant_types_supported
        assert "S256" in metadata.code_challenge_methods_supported


class TestOAuthClientRegistration:
    """Tests for OAuth client registration models."""

    def test_valid_registration_request(self) -> None:
        """Test valid client registration request."""
        request = OAuthClientRegistrationRequest(
            redirect_uris=["http://localhost:3000/callback"],
            client_name="Test Client",
        )
        assert request.redirect_uris == ["http://localhost:3000/callback"]
        assert request.client_name == "Test Client"
        assert "authorization_code" in request.grant_types

    def test_invalid_redirect_uri_raises(self) -> None:
        """Test that invalid redirect URIs raise error."""
        with pytest.raises(ValueError, match="Invalid redirect URI"):
            OAuthClientRegistrationRequest(
                redirect_uris=["not-a-valid-uri"],
            )


class TestGIMOAuthProvider:
    """Tests for GIMOAuthProvider class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.oauth_issuer_url = "http://localhost:8000"
        settings.oauth_authorization_code_ttl_seconds = 600
        settings.oauth_access_token_ttl_seconds = 3600
        settings.oauth_refresh_token_ttl_days = 30
        settings.jwt_secret_key = "test-secret-key-minimum-32-characters-long"
        settings.auth_issuer = "test-issuer"
        settings.auth_audience = "test-audience"
        return settings

    @pytest.fixture
    def oauth_provider(self, mock_settings):
        """Create OAuth provider with mocked settings."""
        with patch("src.auth.oauth_provider.get_settings", return_value=mock_settings):
            with patch("src.auth.jwt_service.get_settings", return_value=mock_settings):
                return GIMOAuthProvider()

    def test_get_server_metadata(self, oauth_provider: GIMOAuthProvider) -> None:
        """Test getting OAuth server metadata."""
        metadata = oauth_provider.get_server_metadata()

        assert metadata.issuer == "http://localhost:8000"
        assert metadata.authorization_endpoint == "http://localhost:8000/authorize"
        assert metadata.token_endpoint == "http://localhost:8000/token"
        assert metadata.registration_endpoint == "http://localhost:8000/register"
        assert metadata.revocation_endpoint == "http://localhost:8000/revoke"
        assert "code" in metadata.response_types_supported
        assert "S256" in metadata.code_challenge_methods_supported

    @pytest.mark.asyncio
    async def test_register_client(self, oauth_provider: GIMOAuthProvider) -> None:
        """Test client registration."""
        request = OAuthClientRegistrationRequest(
            redirect_uris=["http://localhost:3000/callback"],
            client_name="Test Client",
        )

        mock_record = {
            "id": str(uuid4()),
            "client_id": "test-client-id",
            "client_name": "Test Client",
            "redirect_uris": ["http://localhost:3000/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch("src.auth.oauth_provider.insert_record", new_callable=AsyncMock) as mock_insert:
            mock_insert.return_value = mock_record
            response = await oauth_provider.register_client(request)

        assert response.client_id == "test-client-id"
        assert response.client_name == "Test Client"
        assert response.redirect_uris == ["http://localhost:3000/callback"]

    @pytest.mark.asyncio
    async def test_get_client_found(self, oauth_provider: GIMOAuthProvider) -> None:
        """Test getting an existing client."""
        client_id = str(uuid4())
        mock_record = {
            "id": str(uuid4()),
            "client_id": client_id,
            "client_name": "Test Client",
            "redirect_uris": ["http://localhost:3000/callback"],
            "grant_types": ["authorization_code", "refresh_token"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {},
        }

        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_record
            client = await oauth_provider.get_client(client_id)

        assert client is not None
        assert client.client_id == client_id
        assert client.client_name == "Test Client"

    @pytest.mark.asyncio
    async def test_get_client_not_found(self, oauth_provider: GIMOAuthProvider) -> None:
        """Test getting a non-existent client."""
        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            client = await oauth_provider.get_client("non-existent")

        assert client is None

    def test_validate_redirect_uri_valid(self, oauth_provider: GIMOAuthProvider) -> None:
        """Test redirect URI validation with valid URI."""
        client = OAuthClient(
            id=uuid4(),
            client_id="test-client",
            redirect_uris=["http://localhost:3000/callback", "https://example.com/oauth"],
            created_at=datetime.now(timezone.utc),
        )

        assert oauth_provider.validate_redirect_uri(client, "http://localhost:3000/callback")
        assert oauth_provider.validate_redirect_uri(client, "https://example.com/oauth")

    def test_validate_redirect_uri_invalid(self, oauth_provider: GIMOAuthProvider) -> None:
        """Test redirect URI validation with invalid URI."""
        client = OAuthClient(
            id=uuid4(),
            client_id="test-client",
            redirect_uris=["http://localhost:3000/callback"],
            created_at=datetime.now(timezone.utc),
        )

        assert not oauth_provider.validate_redirect_uri(client, "http://attacker.com/callback")

    @pytest.mark.asyncio
    async def test_create_authorization_code(self, oauth_provider: GIMOAuthProvider) -> None:
        """Test authorization code creation."""
        client_id = "test-client"
        gim_identity_id = uuid4()
        redirect_uri = "http://localhost:3000/callback"
        code_challenge = "test-challenge"

        with patch("src.auth.oauth_provider.insert_record", new_callable=AsyncMock) as mock_insert:
            mock_insert.return_value = {}
            code = await oauth_provider.create_authorization_code(
                client_id=client_id,
                gim_identity_id=gim_identity_id,
                redirect_uri=redirect_uri,
                code_challenge=code_challenge,
            )

        assert code is not None
        assert len(code) > 0
        mock_insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_exchange_authorization_code_success(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test successful authorization code exchange."""
        code = "valid-code"
        client_id = "test-client"
        gim_identity_id = uuid4()
        gim_id = uuid4()
        code_verifier = generate_code_verifier()
        code_challenge = compute_code_challenge(code_verifier)
        redirect_uri = "http://localhost:3000/callback"

        auth_code_record = {
            "id": str(uuid4()),
            "code": code,
            "client_id": client_id,
            "gim_identity_id": str(gim_identity_id),
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "used_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_identity = MagicMock()
        mock_identity.gim_id = gim_id
        mock_identity.id = gim_identity_id

        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            with patch("src.auth.oauth_provider.update_record", new_callable=AsyncMock):
                with patch("src.auth.oauth_provider.insert_record", new_callable=AsyncMock):
                    with patch("src.auth.oauth_provider.get_gim_id_service") as mock_gim_service:
                        mock_get.return_value = auth_code_record
                        mock_gim_service.return_value.get_identity_by_id = AsyncMock(
                            return_value=mock_identity
                        )

                        response, error = await oauth_provider.exchange_authorization_code(
                            code=code,
                            client_id=client_id,
                            code_verifier=code_verifier,
                            redirect_uri=redirect_uri,
                        )

        assert error is None
        assert response is not None
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.token_type == "Bearer"

    @pytest.mark.asyncio
    async def test_exchange_authorization_code_invalid_code(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test authorization code exchange with invalid code."""
        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response, error = await oauth_provider.exchange_authorization_code(
                code="invalid-code",
                client_id="test-client",
                code_verifier="verifier",
                redirect_uri="http://localhost:3000/callback",
            )

        assert response is None
        assert error is not None
        assert error.error == "invalid_grant"
        assert "not found" in error.error_description.lower()

    @pytest.mark.asyncio
    async def test_exchange_authorization_code_already_used(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test authorization code exchange with already used code."""
        auth_code_record = {
            "id": str(uuid4()),
            "code": "used-code",
            "client_id": "test-client",
            "gim_identity_id": str(uuid4()),
            "redirect_uri": "http://localhost:3000/callback",
            "code_challenge": "challenge",
            "code_challenge_method": "S256",
            "scope": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "used_at": datetime.now(timezone.utc).isoformat(),  # Already used
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = auth_code_record

            response, error = await oauth_provider.exchange_authorization_code(
                code="used-code",
                client_id="test-client",
                code_verifier="verifier",
                redirect_uri="http://localhost:3000/callback",
            )

        assert response is None
        assert error is not None
        assert error.error == "invalid_grant"
        assert "already been used" in error.error_description.lower()

    @pytest.mark.asyncio
    async def test_exchange_authorization_code_expired(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test authorization code exchange with expired code."""
        auth_code_record = {
            "id": str(uuid4()),
            "code": "expired-code",
            "client_id": "test-client",
            "gim_identity_id": str(uuid4()),
            "redirect_uri": "http://localhost:3000/callback",
            "code_challenge": "challenge",
            "code_challenge_method": "S256",
            "scope": None,
            "expires_at": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),  # Expired
            "used_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = auth_code_record

            response, error = await oauth_provider.exchange_authorization_code(
                code="expired-code",
                client_id="test-client",
                code_verifier="verifier",
                redirect_uri="http://localhost:3000/callback",
            )

        assert response is None
        assert error is not None
        assert error.error == "invalid_grant"
        assert "expired" in error.error_description.lower()

    @pytest.mark.asyncio
    async def test_exchange_authorization_code_pkce_failure(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test authorization code exchange with invalid PKCE verifier."""
        code_verifier = generate_code_verifier()
        code_challenge = compute_code_challenge(code_verifier)

        auth_code_record = {
            "id": str(uuid4()),
            "code": "valid-code",
            "client_id": "test-client",
            "gim_identity_id": str(uuid4()),
            "redirect_uri": "http://localhost:3000/callback",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "used_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = auth_code_record

            # Use wrong verifier
            response, error = await oauth_provider.exchange_authorization_code(
                code="valid-code",
                client_id="test-client",
                code_verifier="wrong-verifier-that-is-long-enough-for-pkce-validation",
                redirect_uri="http://localhost:3000/callback",
            )

        assert response is None
        assert error is not None
        assert error.error == "invalid_grant"
        assert "pkce" in error.error_description.lower()

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test successful token refresh."""
        refresh_token = "valid-refresh-token"
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        client_id = "test-client"
        gim_identity_id = uuid4()
        gim_id = uuid4()

        refresh_token_record = {
            "id": str(uuid4()),
            "token_hash": token_hash,
            "client_id": client_id,
            "gim_identity_id": str(gim_identity_id),
            "scope": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "revoked_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        mock_identity = MagicMock()
        mock_identity.gim_id = gim_id
        mock_identity.id = gim_identity_id

        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            with patch("src.auth.oauth_provider.update_record", new_callable=AsyncMock):
                with patch("src.auth.oauth_provider.insert_record", new_callable=AsyncMock):
                    with patch("src.auth.oauth_provider.get_gim_id_service") as mock_gim_service:
                        mock_get.return_value = refresh_token_record
                        mock_gim_service.return_value.get_identity_by_id = AsyncMock(
                            return_value=mock_identity
                        )

                        response, error = await oauth_provider.refresh_access_token(
                            refresh_token=refresh_token,
                            client_id=client_id,
                        )

        assert error is None
        assert response is not None
        assert response.access_token is not None
        assert response.refresh_token is not None  # New refresh token (rotation)

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test token refresh with invalid token."""
        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response, error = await oauth_provider.refresh_access_token(
                refresh_token="invalid-token",
                client_id="test-client",
            )

        assert response is None
        assert error is not None
        assert error.error == "invalid_grant"

    @pytest.mark.asyncio
    async def test_refresh_access_token_revoked(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test token refresh with revoked token."""
        refresh_token = "revoked-refresh-token"
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        refresh_token_record = {
            "id": str(uuid4()),
            "token_hash": token_hash,
            "client_id": "test-client",
            "gim_identity_id": str(uuid4()),
            "scope": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "revoked_at": datetime.now(timezone.utc).isoformat(),  # Revoked
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = refresh_token_record

            response, error = await oauth_provider.refresh_access_token(
                refresh_token=refresh_token,
                client_id="test-client",
            )

        assert response is None
        assert error is not None
        assert error.error == "invalid_grant"
        assert "revoked" in error.error_description.lower()

    @pytest.mark.asyncio
    async def test_revoke_token_success(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test successful token revocation."""
        refresh_token = "token-to-revoke"
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        refresh_token_record = {
            "id": str(uuid4()),
            "token_hash": token_hash,
            "client_id": "test-client",
            "gim_identity_id": str(uuid4()),
            "scope": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "revoked_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            with patch("src.auth.oauth_provider.update_record", new_callable=AsyncMock) as mock_update:
                mock_get.return_value = refresh_token_record

                result = await oauth_provider.revoke_token(
                    token=refresh_token,
                    token_type_hint="refresh_token",
                )

        assert result is True
        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_token_not_found(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test token revocation with non-existent token."""
        with patch("src.auth.oauth_provider.get_record", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await oauth_provider.revoke_token(
                token="non-existent-token",
                token_type_hint="refresh_token",
            )

        assert result is False
