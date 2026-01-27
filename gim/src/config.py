"""Configuration settings for GIM MCP Server."""

from pydantic_settings import BaseSettings
from pydantic import Field


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
    """

    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon/service key")

    # Qdrant
    qdrant_url: str = Field(..., description="Qdrant Cloud cluster URL")
    qdrant_api_key: str = Field(..., description="Qdrant API key")

    # Google AI
    google_api_key: str = Field(..., description="Google AI API key")
    embedding_model: str = Field(
        default="text-embedding-004",
        description="Google embedding model name"
    )
    llm_model: str = Field(
        default="gemini-2.5-flash-preview-05-20",
        description="Google LLM model for processing"
    )

    # Server
    log_level: str = Field(default="INFO", description="Logging level")

    # Sanitization
    sanitization_confidence_threshold: float = Field(
        default=0.95,
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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """Get application settings instance.

    Returns:
        Settings: Application settings loaded from environment.
    """
    return Settings()
