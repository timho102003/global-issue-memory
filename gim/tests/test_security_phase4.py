"""Tests for Phase 4 Security Hardening - OAuth and Auth Hardening.

Covers:
- 4.1 PKCE plain method removal (only S256 allowed)
- 4.2 Token blocklist and revocation integration
- 4.3 Auth code replay cascade revocation
- 4.4 stat_field whitelist enforcement
- 4.5 Rate limiter race condition fix
"""

import hashlib
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.auth.gim_id_service import GIMIdService
from src.auth.oauth_models import OAuthAuthorizationCode
from src.auth.oauth_provider import GIMOAuthProvider
from src.auth.pkce import compute_code_challenge, generate_code_verifier
from src.auth.rate_limiter import RateLimitExceeded, RateLimiter
from src.auth.token_blocklist import TokenBlocklist, get_token_blocklist
from src.auth.token_verifier import GIMTokenVerifier


# ---------------------------------------------------------------------------
# 4.1 PKCE Plain Method Removal
# ---------------------------------------------------------------------------


class TestPKCEPlainMethodRemoval:
    """Tests verifying that the PKCE plain method is rejected."""

    def test_oauth_authorization_code_rejects_plain_method(self) -> None:
        """Test that OAuthAuthorizationCode model rejects 'plain' method."""
        with pytest.raises(ValidationError):
            OAuthAuthorizationCode(
                id=uuid4(),
                code="test-code",
                client_id="test-client",
                gim_identity_id=uuid4(),
                redirect_uri="http://localhost:3000/callback",
                code_challenge="test-challenge",
                code_challenge_method="plain",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                created_at=datetime.now(timezone.utc),
            )

    def test_oauth_authorization_code_accepts_s256_method(self) -> None:
        """Test that OAuthAuthorizationCode model accepts 'S256' method."""
        auth_code = OAuthAuthorizationCode(
            id=uuid4(),
            code="test-code",
            client_id="test-client",
            gim_identity_id=uuid4(),
            redirect_uri="http://localhost:3000/callback",
            code_challenge="test-challenge",
            code_challenge_method="S256",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            created_at=datetime.now(timezone.utc),
        )
        assert auth_code.code_challenge_method == "S256"

    def test_oauth_authorization_code_defaults_to_s256(self) -> None:
        """Test that code_challenge_method defaults to S256."""
        auth_code = OAuthAuthorizationCode(
            id=uuid4(),
            code="test-code",
            client_id="test-client",
            gim_identity_id=uuid4(),
            redirect_uri="http://localhost:3000/callback",
            code_challenge="test-challenge",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            created_at=datetime.now(timezone.utc),
        )
        assert auth_code.code_challenge_method == "S256"


# ---------------------------------------------------------------------------
# 4.2 Token Blocklist
# ---------------------------------------------------------------------------


class TestTokenBlocklist:
    """Tests for the in-memory token blocklist."""

    def test_add_and_is_blocked(self) -> None:
        """Test adding a token to the blocklist and checking it."""
        blocklist = TokenBlocklist()
        token_hash = hashlib.sha256(b"test-token").hexdigest()
        # Expire in the future
        blocklist.add(token_hash, time.time() + 3600)

        assert blocklist.is_blocked(token_hash)

    def test_is_blocked_returns_false_for_unknown_token(self) -> None:
        """Test that unknown tokens are not blocked."""
        blocklist = TokenBlocklist()
        assert not blocklist.is_blocked("unknown-hash")

    def test_ttl_expiry_removes_entry(self) -> None:
        """Test that expired entries are removed from the blocklist."""
        blocklist = TokenBlocklist()
        token_hash = hashlib.sha256(b"expired-token").hexdigest()
        # Expire in the past
        blocklist.add(token_hash, time.time() - 1)

        assert not blocklist.is_blocked(token_hash)

    def test_cleanup_removes_expired_entries(self) -> None:
        """Test that cleanup removes expired entries during add."""
        blocklist = TokenBlocklist()
        old_hash = hashlib.sha256(b"old-token").hexdigest()
        new_hash = hashlib.sha256(b"new-token").hexdigest()

        # Add an already-expired entry
        blocklist.add(old_hash, time.time() - 1)
        # Add a valid entry (triggers cleanup of old)
        blocklist.add(new_hash, time.time() + 3600)

        assert not blocklist.is_blocked(old_hash)
        assert blocklist.is_blocked(new_hash)

    def test_get_token_blocklist_returns_singleton(self) -> None:
        """Test that get_token_blocklist returns the same instance."""
        # Reset singleton for clean test
        import src.auth.token_blocklist as tb_module
        tb_module._blocklist = None

        b1 = get_token_blocklist()
        b2 = get_token_blocklist()
        assert b1 is b2

        # Clean up
        tb_module._blocklist = None


class TestTokenVerifierBlocklistIntegration:
    """Tests verifying that the token verifier checks the blocklist."""

    def test_verify_rejects_blocklisted_token(self) -> None:
        """Test that verify() returns None for a blocklisted token."""
        verifier = GIMTokenVerifier(
            secret_key="test-secret-key-minimum-32-characters-long!!",
            issuer="test-issuer",
            audience="test-audience",
        )

        token = "some.jwt.token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Add to blocklist
        blocklist = get_token_blocklist()
        blocklist.add(token_hash, time.time() + 3600)

        result = verifier.verify(token)
        assert result is None

        # Clean up singleton
        import src.auth.token_blocklist as tb_module
        tb_module._blocklist = None

    def test_verify_allows_non_blocklisted_valid_token(self) -> None:
        """Test that verify() works for non-blocklisted valid tokens."""
        # Reset blocklist
        import src.auth.token_blocklist as tb_module
        tb_module._blocklist = None

        secret = "test-secret-key-minimum-32-characters-long!!"
        verifier = GIMTokenVerifier(
            secret_key=secret,
            issuer="test-issuer",
            audience="test-audience",
        )

        # Create a real JWT token
        import jwt as pyjwt
        now = int(time.time())
        payload = {
            "sub": str(uuid4()),
            "iss": "test-issuer",
            "aud": "test-audience",
            "exp": now + 3600,
            "iat": now,
            "gim_identity_id": str(uuid4()),
        }
        token = pyjwt.encode(payload, secret, algorithm="HS256")

        result = verifier.verify(token)
        assert result is not None
        assert result.sub == payload["sub"]

        # Clean up
        tb_module._blocklist = None


# ---------------------------------------------------------------------------
# 4.2 continued: revoke_token wires up blocklist
# ---------------------------------------------------------------------------


class TestRevokeTokenBlocklist:
    """Tests verifying that revoke_token adds to the blocklist."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.oauth_issuer_url = "http://localhost:8000"
        settings.oauth_authorization_code_ttl_seconds = 600
        settings.oauth_access_token_ttl_seconds = 3600
        settings.oauth_refresh_token_ttl_days = 30
        mock_secret = MagicMock()
        mock_secret.get_secret_value.return_value = (
            "test-secret-key-minimum-32-characters-long"
        )
        settings.jwt_secret_key = mock_secret
        settings.auth_issuer = "test-issuer"
        settings.auth_audience = "test-audience"
        return settings

    @pytest.fixture
    def oauth_provider(self, mock_settings: MagicMock) -> GIMOAuthProvider:
        """Create OAuth provider with mocked settings."""
        with patch(
            "src.auth.oauth_provider.get_settings", return_value=mock_settings
        ):
            with patch(
                "src.auth.jwt_service.get_settings", return_value=mock_settings
            ):
                return GIMOAuthProvider()

    @pytest.mark.asyncio
    async def test_revoke_access_token_adds_to_blocklist(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test that revoking an access token adds it to the blocklist."""
        import src.auth.token_blocklist as tb_module
        tb_module._blocklist = None

        access_token = "my.access.token"
        token_hash = hashlib.sha256(access_token.encode()).hexdigest()

        # No refresh token found, falls through to access token handling
        with patch(
            "src.auth.oauth_provider.get_record",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await oauth_provider.revoke_token(
                token=access_token,
                token_type_hint="access_token",
            )

        assert result is True
        blocklist = get_token_blocklist()
        assert blocklist.is_blocked(token_hash)

        # Clean up
        tb_module._blocklist = None


# ---------------------------------------------------------------------------
# 4.3 Auth Code Replay Cascade
# ---------------------------------------------------------------------------


class TestAuthCodeReplayCascade:
    """Tests for auth code replay triggering cascade revocation."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.oauth_issuer_url = "http://localhost:8000"
        settings.oauth_authorization_code_ttl_seconds = 600
        settings.oauth_access_token_ttl_seconds = 3600
        settings.oauth_refresh_token_ttl_days = 30
        mock_secret = MagicMock()
        mock_secret.get_secret_value.return_value = (
            "test-secret-key-minimum-32-characters-long"
        )
        settings.jwt_secret_key = mock_secret
        settings.auth_issuer = "test-issuer"
        settings.auth_audience = "test-audience"
        return settings

    @pytest.fixture
    def oauth_provider(self, mock_settings: MagicMock) -> GIMOAuthProvider:
        """Create OAuth provider with mocked settings."""
        with patch(
            "src.auth.oauth_provider.get_settings", return_value=mock_settings
        ):
            with patch(
                "src.auth.jwt_service.get_settings", return_value=mock_settings
            ):
                return GIMOAuthProvider()

    @pytest.mark.asyncio
    async def test_replay_triggers_cascade_revocation(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test that replaying a used auth code revokes all refresh tokens."""
        gim_identity_id = uuid4()
        client_id = "test-client"

        # Auth code that has already been used
        auth_code_record = {
            "id": str(uuid4()),
            "code": "used-code-hash",
            "client_id": client_id,
            "gim_identity_id": str(gim_identity_id),
            "redirect_uri": "http://localhost:3000/callback",
            "code_challenge": "challenge",
            "code_challenge_method": "S256",
            "scope": None,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=10)
            ).isoformat(),
            "used_at": datetime.now(timezone.utc).isoformat(),  # Already used
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Refresh tokens that should be revoked
        refresh_token_records = [
            {
                "id": str(uuid4()),
                "token_hash": "hash1",
                "client_id": client_id,
                "gim_identity_id": str(gim_identity_id),
                "revoked_at": None,
            },
            {
                "id": str(uuid4()),
                "token_hash": "hash2",
                "client_id": client_id,
                "gim_identity_id": str(gim_identity_id),
                "revoked_at": None,
            },
        ]

        with patch(
            "src.auth.oauth_provider.get_record",
            new_callable=AsyncMock,
            return_value=auth_code_record,
        ):
            with patch(
                "src.auth.oauth_provider.query_records",
                new_callable=AsyncMock,
                return_value=refresh_token_records,
            ) as mock_query:
                with patch(
                    "src.auth.oauth_provider.update_record",
                    new_callable=AsyncMock,
                ) as mock_update:
                    response, error = (
                        await oauth_provider.exchange_authorization_code(
                            code="replayed-code",
                            client_id=client_id,
                            code_verifier="verifier",
                            redirect_uri="http://localhost:3000/callback",
                        )
                    )

        # Should return error
        assert response is None
        assert error is not None
        assert error.error == "invalid_grant"
        assert "already been used" in error.error_description.lower()

        # Should have queried for refresh tokens
        mock_query.assert_called_once()
        query_call_args = mock_query.call_args
        assert query_call_args[0][0] == "oauth_refresh_tokens"

        # Should have revoked both refresh tokens
        assert mock_update.call_count == 2
        for call in mock_update.call_args_list:
            assert "revoked_at" in call[0][2]

    @pytest.mark.asyncio
    async def test_replay_skips_already_revoked_tokens(
        self, oauth_provider: GIMOAuthProvider
    ) -> None:
        """Test that replay cascade skips already-revoked tokens."""
        gim_identity_id = uuid4()
        client_id = "test-client"

        auth_code_record = {
            "id": str(uuid4()),
            "code": "used-code-hash",
            "client_id": client_id,
            "gim_identity_id": str(gim_identity_id),
            "redirect_uri": "http://localhost:3000/callback",
            "code_challenge": "challenge",
            "code_challenge_method": "S256",
            "scope": None,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=10)
            ).isoformat(),
            "used_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # One already revoked, one active
        refresh_token_records = [
            {
                "id": str(uuid4()),
                "token_hash": "hash1",
                "client_id": client_id,
                "gim_identity_id": str(gim_identity_id),
                "revoked_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid4()),
                "token_hash": "hash2",
                "client_id": client_id,
                "gim_identity_id": str(gim_identity_id),
                "revoked_at": None,
            },
        ]

        with patch(
            "src.auth.oauth_provider.get_record",
            new_callable=AsyncMock,
            return_value=auth_code_record,
        ):
            with patch(
                "src.auth.oauth_provider.query_records",
                new_callable=AsyncMock,
                return_value=refresh_token_records,
            ):
                with patch(
                    "src.auth.oauth_provider.update_record",
                    new_callable=AsyncMock,
                ) as mock_update:
                    await oauth_provider.exchange_authorization_code(
                        code="replayed-code",
                        client_id=client_id,
                        code_verifier="verifier",
                        redirect_uri="http://localhost:3000/callback",
                    )

        # Only the active token should be revoked
        assert mock_update.call_count == 1


# ---------------------------------------------------------------------------
# 4.4 stat_field Whitelist
# ---------------------------------------------------------------------------


class TestStatFieldWhitelist:
    """Tests for stat field whitelist enforcement in GIMIdService."""

    @pytest.mark.asyncio
    async def test_increment_stat_rejects_unknown_field(self) -> None:
        """Test that unknown stat fields are rejected."""
        service = GIMIdService()
        identity_id = uuid4()

        with pytest.raises(ValueError, match="Invalid stat field"):
            await service.increment_stat(identity_id, "password_hash")

    @pytest.mark.asyncio
    async def test_increment_stat_rejects_arbitrary_column(self) -> None:
        """Test that arbitrary database column names are rejected."""
        service = GIMIdService()
        identity_id = uuid4()

        with pytest.raises(ValueError, match="Invalid stat field"):
            await service.increment_stat(identity_id, "status")

    @pytest.mark.asyncio
    async def test_increment_stat_rejects_sql_injection_attempt(self) -> None:
        """Test that SQL injection attempts in stat field are rejected."""
        service = GIMIdService()
        identity_id = uuid4()

        with pytest.raises(ValueError, match="Invalid stat field"):
            await service.increment_stat(
                identity_id, "total_searches; DROP TABLE"
            )

    @pytest.mark.asyncio
    async def test_increment_stat_allows_total_searches(self) -> None:
        """Test that total_searches is an allowed stat field."""
        service = GIMIdService()
        identity_id = uuid4()

        mock_identity = MagicMock()
        mock_identity.total_searches = 5

        with patch(
            "src.auth.gim_id_service.get_record",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with patch.object(
                service,
                "get_identity_by_id",
                new_callable=AsyncMock,
                return_value=mock_identity,
            ):
                with patch(
                    "src.auth.gim_id_service.update_record",
                    new_callable=AsyncMock,
                ) as mock_update:
                    await service.increment_stat(
                        identity_id, "total_searches"
                    )

        mock_update.assert_called_once_with(
            "gim_identities",
            str(identity_id),
            {"total_searches": 6},
        )

    @pytest.mark.asyncio
    async def test_increment_stat_allows_total_submissions(self) -> None:
        """Test that total_submissions is an allowed stat field."""
        service = GIMIdService()
        identity_id = uuid4()

        mock_identity = MagicMock()
        mock_identity.total_submissions = 3

        with patch.object(
            service,
            "get_identity_by_id",
            new_callable=AsyncMock,
            return_value=mock_identity,
        ):
            with patch(
                "src.auth.gim_id_service.update_record",
                new_callable=AsyncMock,
            ) as mock_update:
                await service.increment_stat(
                    identity_id, "total_submissions"
                )

        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_stat_allows_total_confirmations(self) -> None:
        """Test that total_confirmations is an allowed stat field."""
        service = GIMIdService()
        identity_id = uuid4()

        mock_identity = MagicMock()
        mock_identity.total_confirmations = 10

        with patch.object(
            service,
            "get_identity_by_id",
            new_callable=AsyncMock,
            return_value=mock_identity,
        ):
            with patch(
                "src.auth.gim_id_service.update_record",
                new_callable=AsyncMock,
            ):
                # Should not raise
                await service.increment_stat(
                    identity_id, "total_confirmations"
                )

    @pytest.mark.asyncio
    async def test_increment_stat_allows_total_reports(self) -> None:
        """Test that total_reports is an allowed stat field."""
        service = GIMIdService()
        identity_id = uuid4()

        mock_identity = MagicMock()
        mock_identity.total_reports = 1

        with patch.object(
            service,
            "get_identity_by_id",
            new_callable=AsyncMock,
            return_value=mock_identity,
        ):
            with patch(
                "src.auth.gim_id_service.update_record",
                new_callable=AsyncMock,
            ):
                # Should not raise
                await service.increment_stat(
                    identity_id, "total_reports"
                )


# ---------------------------------------------------------------------------
# 4.5 Rate Limiter Race Condition Fix
# ---------------------------------------------------------------------------


class TestRateLimiterRaceConditionFix:
    """Tests for the rate limiter fallback path race condition fix."""

    @pytest.mark.asyncio
    async def test_fallback_refetches_before_update(self) -> None:
        """Test that the fallback path re-fetches state before updating.

        Simulates the scenario where the optimistic lock fails on all retries
        and the fallback path must re-fetch current state.
        """
        identity_id = uuid4()
        now = datetime.now(timezone.utc)
        reset_at = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Initial record: under limit
        initial_record = {
            "id": str(identity_id),
            "daily_search_limit": 100,
            "daily_search_used": 5,
            "daily_reset_at": reset_at.isoformat(),
            "total_searches": 50,
        }

        # After fallback re-fetch: still under limit but with different used count
        fallback_record = {
            "id": str(identity_id),
            "daily_search_limit": 100,
            "daily_search_used": 10,  # Changed by concurrent requests
            "daily_reset_at": reset_at.isoformat(),
            "total_searches": 55,
        }

        # Mock supabase client that always fails the optimistic lock
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_result = MagicMock()
        mock_result.data = None  # No data = optimistic lock failure

        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.execute.side_effect = Exception("DB error")

        mock_client = MagicMock()
        mock_client.table.return_value = mock_table

        get_record_call_count = 0

        async def mock_get_record(table: str, id_val: str, **kwargs):
            """Return different records for successive calls.

            Call sequence in consume_rate_limit:
            1. Initial fetch (line 221)
            2. Re-fetch after reset check (line 251)
            3. Fallback re-fetch on last retry (line 307) -> return updated
            """
            nonlocal get_record_call_count
            get_record_call_count += 1
            if get_record_call_count <= 2:
                return initial_record
            return fallback_record

        rate_limiter = RateLimiter()

        with patch(
            "src.auth.rate_limiter.get_record",
            side_effect=mock_get_record,
        ):
            with patch(
                "src.auth.rate_limiter.get_supabase_client",
                return_value=mock_client,
            ):
                with patch(
                    "src.auth.rate_limiter.update_record",
                    new_callable=AsyncMock,
                ) as mock_update_record:
                    result = await rate_limiter.consume_rate_limit(
                        identity_id, "gim_search_issues"
                    )

        # Verify the fallback update used the re-fetched value (10 + 1 = 11)
        # Find the call that set daily_search_used
        fallback_calls = [
            c
            for c in mock_update_record.call_args_list
            if "daily_search_used" in c[0][2]
        ]
        assert len(fallback_calls) >= 1
        last_fallback = fallback_calls[-1]
        assert last_fallback[0][2]["daily_search_used"] == 11

    @pytest.mark.asyncio
    async def test_fallback_recheck_raises_when_limit_exceeded(self) -> None:
        """Test that fallback re-check raises RateLimitExceeded if at limit.

        If by the time the fallback re-fetches, the limit is already reached,
        it should raise RateLimitExceeded instead of blindly incrementing.
        """
        identity_id = uuid4()
        now = datetime.now(timezone.utc)
        reset_at = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Initial record: under limit
        initial_record = {
            "id": str(identity_id),
            "daily_search_limit": 100,
            "daily_search_used": 5,
            "daily_reset_at": reset_at.isoformat(),
            "total_searches": 50,
        }

        # After fallback re-fetch: now AT the limit (set by concurrent requests)
        fallback_record = {
            "id": str(identity_id),
            "daily_search_limit": 100,
            "daily_search_used": 100,  # At limit!
            "daily_reset_at": reset_at.isoformat(),
            "total_searches": 150,
        }

        mock_table = MagicMock()
        mock_update_chain = MagicMock()
        mock_eq1 = MagicMock()
        mock_eq2 = MagicMock()
        mock_table.update.return_value = mock_update_chain
        mock_update_chain.eq.return_value = mock_eq1
        mock_eq1.eq.return_value = mock_eq2
        mock_eq2.execute.side_effect = Exception("DB error")

        mock_client = MagicMock()
        mock_client.table.return_value = mock_table

        get_record_call_count = 0

        async def mock_get_record(table: str, id_val: str, **kwargs):
            """Return different records for successive calls.

            Call sequence:
            1. Initial fetch (line 221)
            2. Re-fetch after reset check (line 251)
            3. Fallback re-fetch on last retry (line 307) -> at limit
            """
            nonlocal get_record_call_count
            get_record_call_count += 1
            if get_record_call_count <= 2:
                return initial_record
            return fallback_record

        rate_limiter = RateLimiter()

        with patch(
            "src.auth.rate_limiter.get_record",
            side_effect=mock_get_record,
        ):
            with patch(
                "src.auth.rate_limiter.get_supabase_client",
                return_value=mock_client,
            ):
                with patch(
                    "src.auth.rate_limiter.update_record",
                    new_callable=AsyncMock,
                ):
                    with pytest.raises(RateLimitExceeded):
                        await rate_limiter.consume_rate_limit(
                            identity_id, "gim_search_issues"
                        )
