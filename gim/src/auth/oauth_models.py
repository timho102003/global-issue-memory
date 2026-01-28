"""Pydantic models for OAuth 2.1 authentication.

This module defines data models for OAuth 2.1 with PKCE,
including clients, authorization codes, refresh tokens, and server metadata.
"""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OAuthClient(BaseModel):
    """OAuth client stored in database.

    Attributes:
        id: Internal database ID.
        client_id: Public client identifier.
        client_name: Optional human-readable client name.
        redirect_uris: List of allowed redirect URIs.
        grant_types: Allowed grant types for this client.
        created_at: When the client was registered.
        metadata: Additional client metadata.
    """

    id: UUID
    client_id: str
    client_name: Optional[str] = None
    redirect_uris: list[str]
    grant_types: list[str] = Field(
        default_factory=lambda: ["authorization_code", "refresh_token"]
    )
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class OAuthClientRegistrationRequest(BaseModel):
    """Request to register a new OAuth client (RFC 7591).

    Attributes:
        redirect_uris: List of redirect URIs the client will use.
        client_name: Optional human-readable client name.
        grant_types: Requested grant types.
    """

    redirect_uris: list[str] = Field(..., min_length=1)
    client_name: Optional[str] = None
    grant_types: list[str] = Field(
        default_factory=lambda: ["authorization_code", "refresh_token"]
    )

    @field_validator("redirect_uris")
    @classmethod
    def validate_redirect_uris(cls, v: list[str]) -> list[str]:
        """Validate redirect URIs are valid."""
        for uri in v:
            if not uri.startswith(("http://", "https://")):
                raise ValueError(f"Invalid redirect URI scheme: {uri}")
        return v


class OAuthClientRegistrationResponse(BaseModel):
    """Response after registering an OAuth client.

    Attributes:
        client_id: The assigned client identifier.
        client_name: The client name if provided.
        redirect_uris: Registered redirect URIs.
        grant_types: Allowed grant types.
    """

    client_id: str
    client_name: Optional[str] = None
    redirect_uris: list[str]
    grant_types: list[str]


class OAuthAuthorizationCode(BaseModel):
    """OAuth authorization code stored in database.

    Attributes:
        id: Internal database ID.
        code: The authorization code string.
        client_id: Client that requested authorization.
        gim_identity_id: GIM identity that authorized.
        redirect_uri: URI to redirect after authorization.
        code_challenge: PKCE code challenge.
        code_challenge_method: PKCE challenge method (S256 or plain).
        scope: Requested scope (optional).
        expires_at: When the code expires.
        used_at: When the code was exchanged (null if unused).
        created_at: When the code was created.
    """

    id: UUID
    code: str
    client_id: str
    gim_identity_id: UUID
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str = "S256"
    scope: Optional[str] = None
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OAuthRefreshToken(BaseModel):
    """OAuth refresh token stored in database.

    Attributes:
        id: Internal database ID.
        token_hash: Hash of the refresh token.
        client_id: Client the token belongs to.
        gim_identity_id: GIM identity the token belongs to.
        scope: Token scope.
        expires_at: When the token expires.
        revoked_at: When the token was revoked (null if active).
        created_at: When the token was created.
    """

    id: UUID
    token_hash: str
    client_id: str
    gim_identity_id: UUID
    scope: Optional[str] = None
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OAuthAuthorizationRequest(BaseModel):
    """OAuth authorization request parameters.

    Attributes:
        response_type: Must be "code" for authorization code flow.
        client_id: The client identifier.
        redirect_uri: URI to redirect after authorization.
        code_challenge: PKCE code challenge.
        code_challenge_method: PKCE method (S256 recommended).
        state: Optional state parameter for CSRF protection.
        scope: Optional requested scope.
    """

    response_type: Literal["code"]
    client_id: str
    redirect_uri: str
    code_challenge: str
    code_challenge_method: Literal["S256"] = "S256"
    state: Optional[str] = None
    scope: Optional[str] = None


class OAuthTokenRequest(BaseModel):
    """OAuth token request (authorization code or refresh token grant).

    Attributes:
        grant_type: Type of grant being requested.
        client_id: The client identifier.
        code: Authorization code (for authorization_code grant).
        code_verifier: PKCE code verifier (for authorization_code grant).
        redirect_uri: Redirect URI (for authorization_code grant).
        refresh_token: Refresh token (for refresh_token grant).
    """

    grant_type: Literal["authorization_code", "refresh_token"]
    client_id: str
    code: Optional[str] = None
    code_verifier: Optional[str] = None
    redirect_uri: Optional[str] = None
    refresh_token: Optional[str] = None

    @field_validator("code")
    @classmethod
    def validate_code_for_auth_code_grant(
        cls, v: Optional[str], info
    ) -> Optional[str]:
        """Validate code is present for authorization_code grant."""
        return v

    def validate_for_grant_type(self) -> None:
        """Validate request has required fields for grant type.

        Raises:
            ValueError: If required fields are missing.
        """
        if self.grant_type == "authorization_code":
            if not self.code:
                raise ValueError("code is required for authorization_code grant")
            if not self.code_verifier:
                raise ValueError("code_verifier is required for authorization_code grant")
            if not self.redirect_uri:
                raise ValueError("redirect_uri is required for authorization_code grant")
        elif self.grant_type == "refresh_token":
            if not self.refresh_token:
                raise ValueError("refresh_token is required for refresh_token grant")


class OAuthTokenResponse(BaseModel):
    """OAuth token response.

    Attributes:
        access_token: The JWT access token.
        token_type: Token type (always "Bearer").
        expires_in: Access token expiration in seconds.
        refresh_token: Refresh token for obtaining new access tokens.
        scope: Granted scope.
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class OAuthError(BaseModel):
    """OAuth error response (RFC 6749).

    Attributes:
        error: Error code.
        error_description: Human-readable error description.
        error_uri: Optional URI with more information.
    """

    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None


class OAuthServerMetadata(BaseModel):
    """OAuth Authorization Server Metadata (RFC 8414).

    Attributes:
        issuer: Authorization server issuer identifier.
        authorization_endpoint: URL of authorization endpoint.
        token_endpoint: URL of token endpoint.
        registration_endpoint: URL of dynamic client registration endpoint.
        revocation_endpoint: URL of token revocation endpoint.
        response_types_supported: Supported response types.
        grant_types_supported: Supported grant types.
        code_challenge_methods_supported: Supported PKCE methods.
        token_endpoint_auth_methods_supported: Supported auth methods.
    """

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: Optional[str] = None
    revocation_endpoint: Optional[str] = None
    response_types_supported: list[str] = Field(default_factory=lambda: ["code"])
    grant_types_supported: list[str] = Field(
        default_factory=lambda: ["authorization_code", "refresh_token"]
    )
    code_challenge_methods_supported: list[str] = Field(
        default_factory=lambda: ["S256"]
    )
    token_endpoint_auth_methods_supported: list[str] = Field(
        default_factory=lambda: ["none"]
    )
