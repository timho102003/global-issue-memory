"""Pydantic models for environment and model information."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelProvider(str, Enum):
    """AI model provider.

    Attributes:
        ANTHROPIC: Anthropic (Claude models).
        OPENAI: OpenAI (GPT models).
        GOOGLE: Google (Gemini models).
        GROQ: Groq (fast inference).
        TOGETHER: Together AI.
        LOCAL: Local/self-hosted models.
        OTHER: Other providers.
    """

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    GROQ = "groq"
    TOGETHER = "together"
    LOCAL = "local"
    OTHER = "other"


class ModelInfo(BaseModel):
    """Information about the AI model involved.

    Attributes:
        provider: The model provider.
        model_name: Name of the model.
        model_version: Optional version string.
        behavior_notes: Known behaviors or quirks of this model.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    provider: ModelProvider
    model_name: str = Field(..., min_length=1, max_length=100)
    model_version: Optional[str] = Field(None, max_length=50)
    behavior_notes: List[str] = Field(
        default_factory=list,
        description="Known behaviors or quirks of this model",
    )


class EnvironmentInfo(BaseModel):
    """Environment context where issue occurred.

    Attributes:
        language: Programming language.
        language_version: Version of the language.
        framework: Framework being used.
        framework_version: Version of the framework.
        os: Operating system.
        additional: Additional environment info.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    language: Optional[str] = Field(None, max_length=50)
    language_version: Optional[str] = Field(None, max_length=20)
    framework: Optional[str] = Field(None, max_length=50)
    framework_version: Optional[str] = Field(None, max_length=20)
    os: Optional[str] = Field(None, max_length=50)
    additional: dict = Field(
        default_factory=dict,
        description="Additional environment info",
    )

    def to_search_string(self) -> str:
        """Convert environment info to a searchable string.

        Returns:
            str: Concatenated string of environment details.
        """
        parts = []
        if self.language:
            parts.append(f"{self.language} {self.language_version or ''}".strip())
        if self.framework:
            parts.append(f"{self.framework} {self.framework_version or ''}".strip())
        if self.os:
            parts.append(self.os)
        return " ".join(parts)
