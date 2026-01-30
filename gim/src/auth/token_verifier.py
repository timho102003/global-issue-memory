"""Token verifier for FastMCP integration.

This module provides a custom token verifier that integrates with FastMCP's
authentication system using HS256 symmetric JWT tokens.
"""

import logging
from typing import Optional
from uuid import UUID

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from src.auth.models import JWTClaims
from src.config import get_settings

logger = logging.getLogger(__name__)


class GIMTokenVerifier:
    """Custom token verifier for GIM MCP server.

    Verifies JWT tokens and extracts GIM identity information.
    Compatible with FastMCP's authentication middleware.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
    ) -> None:
        """Initialize token verifier.

        Args:
            secret_key: Secret key for verification (defaults to settings).
            issuer: Expected token issuer (defaults to settings).
            audience: Expected token audience (defaults to settings).
        """
        if any(v is None for v in (secret_key, issuer, audience)):
            settings = get_settings()
        else:
            settings = None
        self._secret_key = secret_key if secret_key is not None else settings.jwt_secret_key
        self._issuer = issuer if issuer is not None else settings.auth_issuer
        self._audience = audience if audience is not None else settings.auth_audience
        self._algorithm = "HS256"

    def verify(self, token: str) -> Optional[JWTClaims]:
        """Verify a JWT token and return claims.

        Args:
            token: The JWT token to verify.

        Returns:
            JWTClaims: The decoded claims if valid, None if invalid.
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
            logger.warning("Token has expired")
            return None
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def get_gim_id(self, token: str) -> Optional[UUID]:
        """Extract GIM ID from a verified token.

        Args:
            token: The JWT token.

        Returns:
            UUID: The GIM ID if valid, None otherwise.
        """
        claims = self.verify(token)
        if claims:
            try:
                return UUID(claims.sub)
            except ValueError:
                return None
        return None

    def get_identity_id(self, token: str) -> Optional[UUID]:
        """Extract identity ID from a verified token.

        Args:
            token: The JWT token.

        Returns:
            UUID: The identity ID if valid, None otherwise.
        """
        claims = self.verify(token)
        if claims:
            try:
                return UUID(claims.gim_identity_id)
            except ValueError:
                return None
        return None


def create_fastmcp_jwt_verifier():
    """Create a JWTVerifier for FastMCP.

    This creates a FastMCP-compatible JWTVerifier using HS256 symmetric key.

    Returns:
        JWTVerifier: A FastMCP JWTVerifier instance.
    """
    from fastmcp.server.auth.providers.jwt import JWTVerifier

    settings = get_settings()

    # FastMCP JWTVerifier with symmetric key (HS256)
    # Note: For HS256, public_key is actually the shared secret
    return JWTVerifier(
        public_key=settings.jwt_secret_key,
        issuer=settings.auth_issuer,
        audience=settings.auth_audience,
        algorithm="HS256",
    )


# Module-level singleton
_token_verifier: Optional[GIMTokenVerifier] = None


def get_token_verifier() -> GIMTokenVerifier:
    """Get token verifier singleton.

    Returns:
        GIMTokenVerifier: The token verifier instance.
    """
    global _token_verifier
    if _token_verifier is None:
        _token_verifier = GIMTokenVerifier()
    return _token_verifier
