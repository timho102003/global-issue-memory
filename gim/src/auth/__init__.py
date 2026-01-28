"""Authentication module for GIM MCP Server.

This module provides GIM ID-based authentication with JWT token exchange
and OAuth 2.1 with PKCE support.
"""

from src.auth.gim_id_service import GIMIdService
from src.auth.jwt_service import JWTService
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
from src.auth.oauth_models import (
    OAuthAuthorizationCode,
    OAuthAuthorizationRequest,
    OAuthClient,
    OAuthClientRegistrationRequest,
    OAuthClientRegistrationResponse,
    OAuthError,
    OAuthRefreshToken,
    OAuthServerMetadata,
    OAuthTokenRequest,
    OAuthTokenResponse,
)
from src.auth.oauth_provider import GIMOAuthProvider, get_oauth_provider
from src.auth.pkce import (
    compute_code_challenge,
    generate_authorization_code,
    generate_code_verifier,
    validate_code_verifier,
    verify_code_challenge,
)
from src.auth.rate_limiter import RateLimitExceeded, RateLimiter

__all__ = [
    # Core auth
    "ErrorResponse",
    "GIMIdentity",
    "GIMIdentityCreate",
    "GIMIdentityResponse",
    "GIMIdentityStatus",
    "GIMIdService",
    "JWTClaims",
    "JWTService",
    "RateLimitExceeded",
    "RateLimiter",
    "RevokeRequest",
    "TokenRequest",
    "TokenResponse",
    # OAuth 2.1
    "GIMOAuthProvider",
    "get_oauth_provider",
    "OAuthAuthorizationCode",
    "OAuthAuthorizationRequest",
    "OAuthClient",
    "OAuthClientRegistrationRequest",
    "OAuthClientRegistrationResponse",
    "OAuthError",
    "OAuthRefreshToken",
    "OAuthServerMetadata",
    "OAuthTokenRequest",
    "OAuthTokenResponse",
    # PKCE
    "compute_code_challenge",
    "generate_authorization_code",
    "generate_code_verifier",
    "validate_code_verifier",
    "verify_code_challenge",
]
