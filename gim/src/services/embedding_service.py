"""Embedding service using Google Gemini embedding models."""

import asyncio
import logging
from typing import List, Optional

from google import genai

from src.config import get_settings

logger = logging.getLogger(__name__)

# Separator used to join sections in combined embeddings.
# Must match between storage (generate_combined_embedding) and
# search (generate_search_embedding) to keep vectors in the same semantic space.
SECTION_SEPARATOR = "\n---\n"

_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """Get or create Gemini client singleton.

    Returns:
        genai.Client: Gemini client instance.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.google_api_key.get_secret_value())
    return _client


def _get_embedding_dimensions() -> int:
    """Get embedding dimensions from settings.

    Returns:
        int: Embedding vector dimensions.
    """
    return get_settings().embedding_dimensions


async def generate_embedding(
    text: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> List[float]:
    """Generate embedding vector for text using Gemini.

    Uses exponential backoff retry for transient API failures.

    Args:
        text: Text to embed.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.

    Returns:
        List[float]: Embedding vector (dimensions from config).

    Raises:
        Exception: If all retry attempts fail.
    """
    dimensions = _get_embedding_dimensions()

    if not text or not text.strip():
        # Return zero vector for empty text
        return [0.0] * dimensions

    client = _get_client()
    settings = get_settings()

    last_exception = None
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
            )
            return list(response.embeddings[0].values)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Embedding API call failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"Embedding API call failed after {max_retries} attempts: {e}")

    raise last_exception  # type: ignore[misc]


async def generate_embeddings_batch(
    texts: List[str],
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> List[List[float]]:
    """Generate embeddings for multiple texts.

    Uses exponential backoff retry for transient API failures.

    Args:
        texts: List of texts to embed.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.

    Returns:
        List[List[float]]: List of embedding vectors.

    Raises:
        Exception: If all retry attempts fail.
    """
    if not texts:
        return []

    client = _get_client()
    settings = get_settings()
    dimensions = _get_embedding_dimensions()

    # Filter out empty texts, keeping track of indices
    non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]

    if not non_empty:
        return [[0.0] * dimensions for _ in texts]

    # Embed non-empty texts with retry
    last_exception = None
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=settings.embedding_model,
                contents=[t for _, t in non_empty],
            )

            # Build result list with zero vectors for empty texts
            results: List[List[float]] = [[0.0] * dimensions for _ in texts]
            for (original_idx, _), embedding in zip(non_empty, response.embeddings):
                results[original_idx] = list(embedding.values)

            return results
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Batch embedding API call failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"Batch embedding API call failed after {max_retries} attempts: {e}"
                )

    raise last_exception  # type: ignore[misc]


async def generate_combined_embedding(
    error_message: str,
    root_cause: str,
    fix_summary: str,
) -> List[float]:
    """Generate a single combined embedding for an issue.

    Concatenates error message, root cause, and fix summary into one text
    and produces a single embedding vector.

    Args:
        error_message: The sanitized error message.
        root_cause: Root cause description.
        fix_summary: Fix bundle summary.

    Returns:
        List[float]: Combined embedding vector.
    """
    combined_text = SECTION_SEPARATOR.join([error_message, root_cause, fix_summary])
    return await generate_embedding(combined_text)


async def generate_search_embedding(error_message: str) -> List[float]:
    """Generate an embedding for a search query.

    Wraps the error message in the same section structure used by
    generate_combined_embedding so query and stored vectors share
    the same semantic space.

    Args:
        error_message: The sanitized error message to search for.

    Returns:
        List[float]: Search embedding vector.
    """
    search_text = SECTION_SEPARATOR.join([error_message, "", ""])
    return await generate_embedding(search_text)


async def compute_similarity(
    vector1: List[float],
    vector2: List[float],
) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vector1: First vector.
        vector2: Second vector.

    Returns:
        float: Cosine similarity score (0.0 to 1.0).
    """
    if len(vector1) != len(vector2):
        raise ValueError("Vectors must have the same dimension")

    dot_product = sum(a * b for a, b in zip(vector1, vector2))
    norm1 = sum(a * a for a in vector1) ** 0.5
    norm2 = sum(b * b for b in vector2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
