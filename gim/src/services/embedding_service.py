"""Embedding service using Google Gemini text-embedding-004."""

from typing import List, Optional

from google import genai

from src.config import get_settings


_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    """Get or create Gemini client singleton.

    Returns:
        genai.Client: Gemini client instance.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.google_api_key)
    return _client


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text using Gemini.

    Args:
        text: Text to embed.

    Returns:
        List[float]: Embedding vector (768 dimensions for text-embedding-004).
    """
    if not text or not text.strip():
        # Return zero vector for empty text
        return [0.0] * 768

    client = _get_client()
    settings = get_settings()

    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
    )

    return list(response.embeddings[0].values)


async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts.

    Args:
        texts: List of texts to embed.

    Returns:
        List[List[float]]: List of embedding vectors.
    """
    if not texts:
        return []

    client = _get_client()
    settings = get_settings()

    # Filter out empty texts, keeping track of indices
    non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]

    if not non_empty:
        return [[0.0] * 768 for _ in texts]

    # Embed non-empty texts
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=[t for _, t in non_empty],
    )

    # Build result list with zero vectors for empty texts
    results: List[List[float]] = [[0.0] * 768 for _ in texts]
    for (original_idx, _), embedding in zip(non_empty, response.embeddings):
        results[original_idx] = list(embedding.values)

    return results


async def generate_issue_embeddings(
    error_message: str,
    root_cause: str,
    fix_summary: str,
) -> dict:
    """Generate all embeddings for an issue.

    Args:
        error_message: The sanitized error message.
        root_cause: Root cause description.
        fix_summary: Fix bundle summary.

    Returns:
        dict: Dictionary containing all embedding vectors.
    """
    embeddings = await generate_embeddings_batch([
        error_message,
        root_cause,
        fix_summary,
    ])

    return {
        "error_signature": embeddings[0],
        "root_cause": embeddings[1],
        "fix_summary": embeddings[2],
    }


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
