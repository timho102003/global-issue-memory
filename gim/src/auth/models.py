"""Pydantic models for GIM authentication.

This module defines data models for GIM ID authentication, JWT tokens,
and rate limiting.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GIMIdentityStatus(str, Enum):
    """Status of a GIM identity."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class GIMIdentity(BaseModel):
    """GIM identity stored in database.

    Attributes:
        id: Internal database ID.
        gim_id: Public GIM ID used for authentication.
        created_at: When the identity was created.
        last_used_at: When the identity was last used.
        status: Current status of the identity.
        daily_search_limit: Maximum daily search operations.
        daily_search_used: Number of searches used today.
        daily_reset_at: When daily limits reset.
        total_searches: Lifetime search count.
        total_submissions: Lifetime submission count.
        total_confirmations: Lifetime confirmation count.
        total_reports: Lifetime report count.
        description: Optional description of the identity.
        metadata: Additional metadata.
    """

    id: UUID
    gim_id: UUID
    created_at: datetime
    last_used_at: Optional[datetime] = None
    status: GIMIdentityStatus = GIMIdentityStatus.ACTIVE
    daily_search_limit: int = 100
    daily_search_used: int = 0
    daily_reset_at: Optional[datetime] = None
    total_searches: int = 0
    total_submissions: int = 0
    total_confirmations: int = 0
    total_reports: int = 0
    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class GIMIdentityCreate(BaseModel):
    """Request to create a new GIM identity.

    Attributes:
        description: Optional description of what this GIM ID is for.
        metadata: Optional additional metadata.
    """

    description: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TokenRequest(BaseModel):
    """Request to exchange GIM ID for JWT token.

    Attributes:
        gim_id: The GIM ID to authenticate with.
    """

    gim_id: UUID


class TokenResponse(BaseModel):
    """Response containing JWT access token.

    Attributes:
        access_token: The JWT access token.
        token_type: Token type (always "Bearer").
        expires_in: Token expiration time in seconds.
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class JWTClaims(BaseModel):
    """JWT token claims.

    Attributes:
        sub: Subject (GIM ID).
        iss: Issuer.
        aud: Audience.
        exp: Expiration timestamp.
        iat: Issued at timestamp.
        gim_identity_id: Internal identity ID for database lookups.
    """

    sub: str  # GIM ID as string
    iss: str  # Issuer
    aud: str  # Audience
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp
    gim_identity_id: str  # Internal ID for lookups


class RevokeRequest(BaseModel):
    """Request to revoke a GIM ID.

    Attributes:
        gim_id: The GIM ID to revoke.
    """

    gim_id: UUID


class GIMIdentityResponse(BaseModel):
    """Response after creating a GIM identity.

    Attributes:
        gim_id: The generated GIM ID.
        created_at: When the identity was created.
        description: Optional description.
    """

    gim_id: UUID
    created_at: datetime
    description: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response for auth endpoints.

    Attributes:
        error: Error code.
        error_description: Human-readable error description.
    """

    error: str
    error_description: str
