"""Configuration settings for GIM MCP Server."""

from typing import Literal, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        supabase_url: Supabase project URL.
        supabase_key: Supabase anon/service key.
        qdrant_url: Qdrant Cloud cluster URL.
        qdrant_api_key: Qdrant API key for authentication.
        google_api_key: Google AI API key for embeddings and LLM.
        embedding_model: Google embedding model name.
        llm_model: Google LLM model name for processing.
        log_level: Logging level.
        jwt_secret_key: Secret key for signing JWT tokens (min 32 chars).
        auth_issuer: JWT token issuer identifier.
        auth_audience: JWT token audience identifier.
        access_token_ttl_hours: JWT access token TTL in hours.
        transport_mode: Server transport mode (stdio, http, or dual).
        http_host: Host to bind HTTP server to.
        http_port: Port for HTTP server.
        frontend_url: Production frontend URL for CORS.
        default_daily_search_limit: Default daily limit for search operations.
    """

    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: SecretStr = Field(..., description="Supabase anon/service key")

    # Qdrant
    qdrant_url: str = Field(..., description="Qdrant Cloud cluster URL")
    qdrant_api_key: SecretStr = Field(..., description="Qdrant API key")

    # Google AI
    google_api_key: SecretStr = Field(..., description="Google AI API key")
    embedding_model: str = Field(
        default="gemini-embedding-001",
        description="Google embedding model name"
    )
    embedding_dimensions: int = Field(
        default=3072,
        description="Embedding vector dimensions (3072 for gemini-embedding-001)"
    )
    llm_model: str = Field(
        default="gemini-3-flash-preview",
        description="Google LLM model for processing"
    )

    # Server
    log_level: str = Field(default="INFO", description="Logging level")

    # Authentication
    jwt_secret_key: SecretStr = Field(
        ...,
        min_length=32,
        description="Secret key for signing JWT tokens (min 32 characters)"
    )
    auth_issuer: str = Field(
        default="gim-mcp",
        description="JWT token issuer identifier"
    )
    auth_audience: str = Field(
        default="gim-clients",
        description="JWT token audience identifier"
    )
    access_token_ttl_hours: int = Field(
        default=24,
        ge=1,
        le=24,
        description="JWT access token TTL in hours"
    )

    # Transport
    transport_mode: Literal["stdio", "http", "dual"] = Field(
        default="stdio",
        description="Server transport mode"
    )
    http_host: str = Field(
        default="0.0.0.0",
        description="Host to bind HTTP server to"
    )
    http_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port for HTTP server"
    )

    # CORS
    frontend_url: Optional[str] = Field(
        default=None,
        description="Production frontend URL for CORS (e.g., https://your-app.vercel.app)"
    )

    # Rate limiting
    default_daily_search_limit: int = Field(
        default=100,
        ge=1,
        description="Default daily limit for search and get_fix_bundle operations"
    )

    # Auth enforcement
    require_auth_for_reads: bool = Field(
        default=False,
        description="Require authentication for read-only endpoints (gradual rollout)"
    )

    # OAuth 2.1 settings
    oauth_issuer_url: str = Field(
        default="http://localhost:8000",
        description="OAuth authorization server issuer URL"
    )
    oauth_authorization_code_ttl_seconds: int = Field(
        default=600,
        ge=60,
        le=3600,
        description="Authorization code TTL in seconds (10 minutes default)"
    )
    oauth_access_token_ttl_seconds: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="OAuth access token TTL in seconds (1 hour default)"
    )
    oauth_refresh_token_ttl_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Refresh token TTL in days (30 days default)"
    )

    # GitHub Crawler
    github_token: Optional[SecretStr] = Field(
        default=None,
        description="GitHub PAT for crawler (optional, increases rate limits)"
    )

    # Sanitization
    sanitization_confidence_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for sanitization approval"
    )

    # Similarity
    similarity_merge_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for suggesting issue merge"
    )

    # Async submission
    max_submission_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max retry attempts for background submission"
    )
    submission_retry_base_delay: float = Field(
        default=2.0,
        ge=0.5,
        le=30.0,
        description="Base delay in seconds for exponential backoff"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings instance (cached).

    Returns:
        Settings: Application settings loaded from environment.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
