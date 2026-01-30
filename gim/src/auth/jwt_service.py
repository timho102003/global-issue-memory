"""JWT token service for GIM authentication.

This module handles JWT token creation and validation using HS256 symmetric signing.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from src.auth.models import JWTClaims, TokenResponse
from src.config import get_settings

logger = logging.getLogger(__name__)


class JWTService:
    """Service for creating and validating JWT tokens.

    Uses HS256 symmetric signing with a shared secret key.
    Tokens include GIM ID as subject and internal identity ID for lookups.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        ttl_hours: Optional[int] = None,
    ) -> None:
        """Initialize JWT service.

        Args:
            secret_key: Secret key for signing (defaults to settings).
            issuer: Token issuer (defaults to settings).
            audience: Token audience (defaults to settings).
            ttl_hours: Token TTL in hours (defaults to settings).
        """
        if any(v is None for v in (secret_key, issuer, audience, ttl_hours)):
            settings = get_settings()
        else:
            settings = None
        self._secret_key = secret_key if secret_key is not None else settings.jwt_secret_key
        self._issuer = issuer if issuer is not None else settings.auth_issuer
        self._audience = audience if audience is not None else settings.auth_audience
        self._ttl_hours = ttl_hours if ttl_hours is not None else settings.access_token_ttl_hours
        self._algorithm = "HS256"

    def create_token(
        self,
        gim_id: UUID,
        identity_id: UUID,
    ) -> TokenResponse:
        """Create a JWT access token.

        Args:
            gim_id: The GIM ID (becomes token subject).
            identity_id: Internal identity ID for database lookups.

        Returns:
            TokenResponse: Token response with access token and expiration.
        """
        now = datetime.now(timezone.utc)
        expires_in_seconds = self._ttl_hours * 3600
        exp = int(now.timestamp()) + expires_in_seconds

        claims = {
            "sub": str(gim_id),
            "iss": self._issuer,
            "aud": self._audience,
            "exp": exp,
            "iat": int(now.timestamp()),
            "gim_identity_id": str(identity_id),
        }

        token = jwt.encode(claims, self._secret_key, algorithm=self._algorithm)

        logger.info("Created JWT token for GIM ID")

        return TokenResponse(
            access_token=token,
            token_type="Bearer",
            expires_in=expires_in_seconds,
        )

    def verify_token(self, token: str) -> Optional[JWTClaims]:
        """Verify and decode a JWT token.

        Args:
            token: The JWT token to verify.

        Returns:
            JWTClaims: Decoded claims if valid, None if invalid.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
            )
            return JWTClaims(
                sub=payload["sub"],
                iss=payload["iss"],
                aud=payload["aud"],
                exp=payload["exp"],
                iat=payload["iat"],
                gim_identity_id=payload["gim_identity_id"],
            )
        except ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

    def get_gim_id_from_token(self, token: str) -> Optional[UUID]:
        """Extract GIM ID from a token without full validation.

        Args:
            token: The JWT token.

        Returns:
            UUID: The GIM ID if present, None otherwise.
        """
        claims = self.verify_token(token)
        if claims:
            try:
                return UUID(claims.sub)
            except ValueError:
                return None
        return None

    def get_identity_id_from_token(self, token: str) -> Optional[UUID]:
        """Extract internal identity ID from a token.

        Args:
            token: The JWT token.

        Returns:
            UUID: The identity ID if present, None otherwise.
        """
        claims = self.verify_token(token)
        if claims:
            try:
                return UUID(claims.gim_identity_id)
            except ValueError:
                return None
        return None


# Module-level singleton
_jwt_service: Optional[JWTService] = None


def get_jwt_service() -> JWTService:
    """Get JWT service singleton.

    Returns:
        JWTService: The JWT service instance.
    """
    global _jwt_service
    if _jwt_service is None:
        _jwt_service = JWTService()
    return _jwt_service
