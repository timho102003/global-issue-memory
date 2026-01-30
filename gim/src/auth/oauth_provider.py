"""OAuth 2.1 provider for GIM MCP Server.

This module implements an OAuth 2.1 authorization server with PKCE support,
using GIM ID as the user identity.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple
from uuid import UUID

from src.auth.gim_id_service import get_gim_id_service
from src.auth.jwt_service import JWTService
from src.auth.oauth_models import (
    OAuthAuthorizationCode,
    OAuthClient,
    OAuthClientRegistrationRequest,
    OAuthClientRegistrationResponse,
    OAuthError,
    OAuthRefreshToken,
    OAuthServerMetadata,
    OAuthTokenResponse,
)
from src.auth.pkce import generate_authorization_code, verify_code_challenge
from src.auth.token_blocklist import get_token_blocklist
from src.config import get_settings
from src.db.supabase_client import (
    get_record,
    insert_record,
    query_records,
    update_record,
)

logger = logging.getLogger(__name__)

# Table names
OAUTH_CLIENTS_TABLE = "oauth_clients"
OAUTH_AUTH_CODES_TABLE = "oauth_authorization_codes"
OAUTH_REFRESH_TOKENS_TABLE = "oauth_refresh_tokens"


class GIMOAuthProvider:
    """OAuth 2.1 provider using GIM ID as user identity.

    Implements RFC 6749 (OAuth 2.0), RFC 7636 (PKCE), RFC 7591 (Dynamic Client
    Registration), and RFC 8414 (Authorization Server Metadata).
    """

    def __init__(self) -> None:
        """Initialize OAuth provider."""
        self._settings = get_settings()
        self._jwt_service = JWTService(
            ttl_hours=self._settings.oauth_access_token_ttl_seconds // 3600 or 1
        )

    def get_server_metadata(self) -> OAuthServerMetadata:
        """Get OAuth authorization server metadata (RFC 8414).

        Returns:
            OAuthServerMetadata: Server metadata for discovery.
        """
        base_url = self._settings.oauth_issuer_url.rstrip("/")
        return OAuthServerMetadata(
            issuer=base_url,
            authorization_endpoint=f"{base_url}/authorize",
            token_endpoint=f"{base_url}/token",
            registration_endpoint=f"{base_url}/register",
            revocation_endpoint=f"{base_url}/revoke",
            response_types_supported=["code"],
            grant_types_supported=["authorization_code", "refresh_token"],
            code_challenge_methods_supported=["S256"],
            token_endpoint_auth_methods_supported=["none"],
        )

    async def register_client(
        self,
        request: OAuthClientRegistrationRequest,
    ) -> OAuthClientRegistrationResponse:
        """Register a new OAuth client (RFC 7591).

        Args:
            request: Client registration request.

        Returns:
            OAuthClientRegistrationResponse: Registered client details.

        Raises:
            ValueError: If registration fails.
        """
        # Generate a unique client_id
        client_id = secrets.token_urlsafe(24)

        data = {
            "client_id": client_id,
            "client_name": request.client_name,
            "redirect_uris": request.redirect_uris,
            "grant_types": request.grant_types,
            "metadata": {},
        }

        record = await insert_record(OAUTH_CLIENTS_TABLE, data)

        logger.info(f"Registered new OAuth client: {client_id}")

        return OAuthClientRegistrationResponse(
            client_id=record["client_id"],
            client_name=record.get("client_name"),
            redirect_uris=record["redirect_uris"],
            grant_types=record["grant_types"],
        )

    async def get_client(self, client_id: str) -> Optional[OAuthClient]:
        """Get an OAuth client by client_id.

        Args:
            client_id: The client identifier.

        Returns:
            OAuthClient: The client if found, None otherwise.
        """
        record = await get_record(
            OAUTH_CLIENTS_TABLE,
            client_id,
            id_column="client_id",
        )
        if record:
            return self._record_to_client(record)
        return None

    def validate_redirect_uri(
        self,
        client: OAuthClient,
        redirect_uri: str,
    ) -> bool:
        """Validate that a redirect URI is registered for a client.

        Args:
            client: The OAuth client.
            redirect_uri: The redirect URI to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        return redirect_uri in client.redirect_uris

    async def create_authorization_code(
        self,
        client_id: str,
        gim_identity_id: UUID,
        redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str = "S256",
        scope: Optional[str] = None,
    ) -> str:
        """Create an authorization code after user approves.

        Args:
            client_id: The client requesting authorization.
            gim_identity_id: The GIM identity authorizing access.
            redirect_uri: The redirect URI for the callback.
            code_challenge: PKCE code challenge.
            code_challenge_method: PKCE challenge method.
            scope: Requested scope.

        Returns:
            str: The authorization code.
        """
        code = generate_authorization_code()
        code_hash = self._hash_token(code)  # Store hash to prevent timing attacks
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=self._settings.oauth_authorization_code_ttl_seconds
        )

        data = {
            "code": code_hash,  # Store hash, not plaintext
            "client_id": client_id,
            "gim_identity_id": str(gim_identity_id),
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "scope": scope,
            "expires_at": expires_at.isoformat(),
        }

        await insert_record(OAUTH_AUTH_CODES_TABLE, data)

        logger.info("Created authorization code for client")  # Don't log client_id

        return code

    async def exchange_authorization_code(
        self,
        code: str,
        client_id: str,
        code_verifier: str,
        redirect_uri: str,
    ) -> Tuple[Optional[OAuthTokenResponse], Optional[OAuthError]]:
        """Exchange authorization code for tokens.

        Args:
            code: The authorization code.
            client_id: The client identifier.
            code_verifier: PKCE code verifier.
            redirect_uri: The redirect URI used in authorization.

        Returns:
            Tuple of (OAuthTokenResponse, None) on success or
            (None, OAuthError) on failure.
        """
        # Hash the code for lookup (codes are stored as hashes)
        code_hash = self._hash_token(code)

        # Get the authorization code
        auth_code_record = await get_record(
            OAUTH_AUTH_CODES_TABLE,
            code_hash,
            id_column="code",
        )

        if not auth_code_record:
            return None, OAuthError(
                error="invalid_grant",
                error_description="Authorization code not found",
            )

        auth_code = self._record_to_auth_code(auth_code_record)

        # Verify code hasn't been used (replay detection with cascade revocation)
        if auth_code.used_at is not None:
            # Auth code replay detected - revoke all refresh tokens for this
            # identity+client combination as a security precaution (RFC 6819)
            logger.warning(
                "Auth code replay detected, revoking all refresh tokens "
                "for identity+client combination"
            )
            await self._revoke_all_refresh_tokens(
                gim_identity_id=auth_code.gim_identity_id,
                client_id=auth_code.client_id,
            )
            return None, OAuthError(
                error="invalid_grant",
                error_description="Authorization code has already been used",
            )

        # Verify code hasn't expired
        if datetime.now(timezone.utc) > auth_code.expires_at:
            return None, OAuthError(
                error="invalid_grant",
                error_description="Authorization code has expired",
            )

        # Verify client_id matches
        if auth_code.client_id != client_id:
            return None, OAuthError(
                error="invalid_grant",
                error_description="Client ID mismatch",
            )

        # Verify redirect_uri matches
        if auth_code.redirect_uri != redirect_uri:
            return None, OAuthError(
                error="invalid_grant",
                error_description="Redirect URI mismatch",
            )

        # Verify PKCE code challenge (only S256 is allowed per OAuth 2.1)
        method = auth_code.code_challenge_method
        if method != "S256":
            method = "S256"
        if not verify_code_challenge(
            code_verifier,
            auth_code.code_challenge,
            method,
        ):
            return None, OAuthError(
                error="invalid_grant",
                error_description="PKCE verification failed",
            )

        # Mark code as used
        await update_record(
            OAUTH_AUTH_CODES_TABLE,
            str(auth_code.id),
            {"used_at": datetime.now(timezone.utc).isoformat()},
        )

        # Get the GIM identity
        gim_id_service = get_gim_id_service()
        identity = await gim_id_service.get_identity_by_id(auth_code.gim_identity_id)
        if not identity:
            return None, OAuthError(
                error="invalid_grant",
                error_description="GIM identity not found",
            )

        # Generate tokens
        return await self._generate_tokens(
            client_id=client_id,
            gim_identity_id=auth_code.gim_identity_id,
            gim_id=identity.gim_id,
            scope=auth_code.scope,
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
        client_id: str,
    ) -> Tuple[Optional[OAuthTokenResponse], Optional[OAuthError]]:
        """Refresh an access token using a refresh token.

        Implements refresh token rotation - old token is revoked, new one issued.

        Args:
            refresh_token: The refresh token.
            client_id: The client identifier.

        Returns:
            Tuple of (OAuthTokenResponse, None) on success or
            (None, OAuthError) on failure.
        """
        # Hash the refresh token for lookup
        token_hash = self._hash_token(refresh_token)

        # Get the refresh token record
        refresh_token_record = await get_record(
            OAUTH_REFRESH_TOKENS_TABLE,
            token_hash,
            id_column="token_hash",
        )

        if not refresh_token_record:
            return None, OAuthError(
                error="invalid_grant",
                error_description="Refresh token not found",
            )

        stored_token = self._record_to_refresh_token(refresh_token_record)

        # Verify token hasn't been revoked
        if stored_token.revoked_at is not None:
            return None, OAuthError(
                error="invalid_grant",
                error_description="Refresh token has been revoked",
            )

        # Verify token hasn't expired
        if datetime.now(timezone.utc) > stored_token.expires_at:
            return None, OAuthError(
                error="invalid_grant",
                error_description="Refresh token has expired",
            )

        # Verify client_id matches
        if stored_token.client_id != client_id:
            return None, OAuthError(
                error="invalid_grant",
                error_description="Client ID mismatch",
            )

        # Revoke the old refresh token (rotation)
        await update_record(
            OAUTH_REFRESH_TOKENS_TABLE,
            str(stored_token.id),
            {"revoked_at": datetime.now(timezone.utc).isoformat()},
        )

        # Get the GIM identity
        gim_id_service = get_gim_id_service()
        identity = await gim_id_service.get_identity_by_id(
            stored_token.gim_identity_id
        )
        if not identity:
            return None, OAuthError(
                error="invalid_grant",
                error_description="GIM identity not found",
            )

        # Generate new tokens
        return await self._generate_tokens(
            client_id=client_id,
            gim_identity_id=stored_token.gim_identity_id,
            gim_id=identity.gim_id,
            scope=stored_token.scope,
        )

    async def revoke_token(
        self,
        token: str,
        token_type_hint: Optional[str] = None,
    ) -> bool:
        """Revoke a token (RFC 7009).

        Args:
            token: The token to revoke.
            token_type_hint: Hint about token type (refresh_token or access_token).

        Returns:
            bool: True if revoked, False if not found.
        """
        # Try refresh token first if hinted or no hint
        if token_type_hint in (None, "refresh_token"):
            token_hash = self._hash_token(token)
            refresh_token_record = await get_record(
                OAUTH_REFRESH_TOKENS_TABLE,
                token_hash,
                id_column="token_hash",
            )
            if refresh_token_record and not refresh_token_record.get("revoked_at"):
                await update_record(
                    OAUTH_REFRESH_TOKENS_TABLE,
                    str(refresh_token_record["id"]),
                    {"revoked_at": datetime.now(timezone.utc).isoformat()},
                )
                logger.info("Revoked refresh token")
                return True

        # For access tokens (JWTs), add to in-memory blocklist
        if token_type_hint in (None, "access_token"):
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            blocklist = get_token_blocklist()
            # Use a generous TTL (24 hours) since we may not know exact expiry
            blocklist.add(token_hash, time.time() + 86400)
            logger.info("Added access token to blocklist")
            return True

        return False

    async def _generate_tokens(
        self,
        client_id: str,
        gim_identity_id: UUID,
        gim_id: UUID,
        scope: Optional[str] = None,
    ) -> Tuple[OAuthTokenResponse, None]:
        """Generate access and refresh tokens.

        Args:
            client_id: The client identifier.
            gim_identity_id: The GIM identity ID.
            gim_id: The GIM ID (used as token subject).
            scope: Token scope.

        Returns:
            Tuple of (OAuthTokenResponse, None).
        """
        # Generate access token (JWT)
        jwt_response = self._jwt_service.create_token(
            gim_id=gim_id,
            identity_id=gim_identity_id,
        )

        # Generate refresh token
        refresh_token = secrets.token_urlsafe(48)
        refresh_token_hash = self._hash_token(refresh_token)
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(
            days=self._settings.oauth_refresh_token_ttl_days
        )

        await insert_record(
            OAUTH_REFRESH_TOKENS_TABLE,
            {
                "token_hash": refresh_token_hash,
                "client_id": client_id,
                "gim_identity_id": str(gim_identity_id),
                "scope": scope,
                "expires_at": refresh_expires_at.isoformat(),
            },
        )

        return OAuthTokenResponse(
            access_token=jwt_response.access_token,
            token_type="Bearer",
            expires_in=self._settings.oauth_access_token_ttl_seconds,
            refresh_token=refresh_token,
            scope=scope,
        ), None

    async def _revoke_all_refresh_tokens(
        self,
        gim_identity_id: UUID,
        client_id: str,
    ) -> int:
        """Revoke all active refresh tokens for an identity+client pair.

        Used as a cascade action when an authorization code replay is detected.

        Args:
            gim_identity_id: The GIM identity ID.
            client_id: The OAuth client ID.

        Returns:
            int: Number of tokens revoked.
        """
        # Query all active refresh tokens for this identity+client
        records = await query_records(
            OAUTH_REFRESH_TOKENS_TABLE,
            filters={
                "gim_identity_id": str(gim_identity_id),
                "client_id": client_id,
            },
        )

        revoked_count = 0
        now_iso = datetime.now(timezone.utc).isoformat()
        for record in records:
            if record.get("revoked_at") is None:
                await update_record(
                    OAUTH_REFRESH_TOKENS_TABLE,
                    str(record["id"]),
                    {"revoked_at": now_iso},
                )
                revoked_count += 1

        if revoked_count > 0:
            logger.info(
                f"Cascade revoked {revoked_count} refresh token(s) "
                "due to auth code replay"
            )

        return revoked_count

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage.

        Args:
            token: The token to hash.

        Returns:
            str: The SHA-256 hash of the token.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def _record_to_client(self, record: dict[str, Any]) -> OAuthClient:
        """Convert database record to OAuthClient model.

        Args:
            record: Database record.

        Returns:
            OAuthClient: The client model.
        """
        return OAuthClient(
            id=UUID(record["id"]),
            client_id=record["client_id"],
            client_name=record.get("client_name"),
            redirect_uris=record["redirect_uris"],
            grant_types=record.get("grant_types", ["authorization_code", "refresh_token"]),
            created_at=datetime.fromisoformat(record["created_at"]),
            metadata=record.get("metadata", {}),
        )

    def _record_to_auth_code(self, record: dict[str, Any]) -> OAuthAuthorizationCode:
        """Convert database record to OAuthAuthorizationCode model.

        Args:
            record: Database record.

        Returns:
            OAuthAuthorizationCode: The authorization code model.
        """
        return OAuthAuthorizationCode(
            id=UUID(record["id"]),
            code=record["code"],
            client_id=record["client_id"],
            gim_identity_id=UUID(record["gim_identity_id"]),
            redirect_uri=record["redirect_uri"],
            code_challenge=record["code_challenge"],
            code_challenge_method=record.get("code_challenge_method", "S256"),
            scope=record.get("scope"),
            expires_at=datetime.fromisoformat(record["expires_at"]),
            used_at=(
                datetime.fromisoformat(record["used_at"])
                if record.get("used_at")
                else None
            ),
            created_at=datetime.fromisoformat(record["created_at"]),
        )

    def _record_to_refresh_token(self, record: dict[str, Any]) -> OAuthRefreshToken:
        """Convert database record to OAuthRefreshToken model.

        Args:
            record: Database record.

        Returns:
            OAuthRefreshToken: The refresh token model.
        """
        return OAuthRefreshToken(
            id=UUID(record["id"]),
            token_hash=record["token_hash"],
            client_id=record["client_id"],
            gim_identity_id=UUID(record["gim_identity_id"]),
            scope=record.get("scope"),
            expires_at=datetime.fromisoformat(record["expires_at"]),
            revoked_at=(
                datetime.fromisoformat(record["revoked_at"])
                if record.get("revoked_at")
                else None
            ),
            created_at=datetime.fromisoformat(record["created_at"]),
        )


# Module-level singleton
_oauth_provider: Optional[GIMOAuthProvider] = None


def get_oauth_provider() -> GIMOAuthProvider:
    """Get OAuth provider singleton.

    Returns:
        GIMOAuthProvider: The OAuth provider instance.
    """
    global _oauth_provider
    if _oauth_provider is None:
        _oauth_provider = GIMOAuthProvider()
    return _oauth_provider
