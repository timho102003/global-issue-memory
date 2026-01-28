"""Tests for embedding service."""

import pytest
from unittest.mock import MagicMock, patch

from src.services.embedding_service import (
    generate_embedding,
    generate_embeddings_batch,
    generate_issue_embeddings,
    compute_similarity,
    _get_embedding_dimensions,
)


class TestComputeSimilarity:
    """Tests for cosine similarity computation."""

    @pytest.mark.asyncio
    async def test_identical_vectors(self) -> None:
        """Test similarity of identical vectors is 1.0."""
        vec = [1.0, 2.0, 3.0]
        similarity = await compute_similarity(vec, vec)
        assert similarity == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_orthogonal_vectors(self) -> None:
        """Test similarity of orthogonal vectors is 0.0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = await compute_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_opposite_vectors(self) -> None:
        """Test similarity of opposite vectors is -1.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        similarity = await compute_similarity(vec1, vec2)
        assert similarity == pytest.approx(-1.0)

    @pytest.mark.asyncio
    async def test_zero_vector(self) -> None:
        """Test similarity with zero vector is 0.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        similarity = await compute_similarity(vec1, vec2)
        assert similarity == 0.0

    @pytest.mark.asyncio
    async def test_different_dimensions_raises(self) -> None:
        """Test that different dimensions raise ValueError."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        with pytest.raises(ValueError, match="same dimension"):
            await compute_similarity(vec1, vec2)


class TestGenerateEmbeddingMocked:
    """Tests for generate_embedding with mocked API."""

    @pytest.mark.asyncio
    async def test_empty_text_returns_zero_vector(self) -> None:
        """Test that empty text returns a zero vector."""
        with patch("src.services.embedding_service.get_settings") as mock_settings:
            mock_settings.return_value.embedding_dimensions = 3072
            result = await generate_embedding("")
            assert len(result) == 3072
            assert all(v == 0.0 for v in result)

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_zero_vector(self) -> None:
        """Test that whitespace-only text returns a zero vector."""
        with patch("src.services.embedding_service.get_settings") as mock_settings:
            mock_settings.return_value.embedding_dimensions = 3072
            result = await generate_embedding("   \n\t  ")
            assert len(result) == 3072
            assert all(v == 0.0 for v in result)

    @pytest.mark.asyncio
    async def test_valid_text_calls_api(self) -> None:
        """Test that valid text calls the embedding API."""
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 3072

        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding]

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = mock_response

        with patch("src.services.embedding_service._get_client", return_value=mock_client), \
             patch("src.services.embedding_service.get_settings") as mock_settings:
            mock_settings.return_value.embedding_model = "gemini-embedding-001"
            mock_settings.return_value.embedding_dimensions = 3072

            result = await generate_embedding("test error")

            assert len(result) == 3072
            assert result == [0.1] * 3072
            mock_client.models.embed_content.assert_called_once()


class TestGenerateEmbeddingsBatchMocked:
    """Tests for generate_embeddings_batch with mocked API."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_empty(self) -> None:
        """Test that empty list returns empty list."""
        result = await generate_embeddings_batch([])
        assert result == []

    @pytest.mark.asyncio
    async def test_all_empty_texts_returns_zero_vectors(self) -> None:
        """Test that all empty texts return zero vectors."""
        with patch("src.services.embedding_service.get_settings") as mock_settings:
            mock_settings.return_value.embedding_dimensions = 3072
            result = await generate_embeddings_batch(["", "  ", "\n"])
            assert len(result) == 3
            for vec in result:
                assert len(vec) == 3072
                assert all(v == 0.0 for v in vec)

    @pytest.mark.asyncio
    async def test_mixed_texts_handles_empty(self) -> None:
        """Test that mixed texts handle empty entries correctly."""
        mock_embedding = MagicMock()
        mock_embedding.values = [0.5] * 3072

        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding]

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = mock_response

        with patch("src.services.embedding_service._get_client", return_value=mock_client), \
             patch("src.services.embedding_service.get_settings") as mock_settings:
            mock_settings.return_value.embedding_model = "gemini-embedding-001"
            mock_settings.return_value.embedding_dimensions = 3072

            result = await generate_embeddings_batch(["", "valid text", ""])

            assert len(result) == 3
            # First and third should be zero vectors
            assert all(v == 0.0 for v in result[0])
            assert all(v == 0.0 for v in result[2])
            # Second should be the embedding
            assert result[1] == [0.5] * 3072


class TestGenerateIssueEmbeddingsMocked:
    """Tests for generate_issue_embeddings with mocked API."""

    @pytest.mark.asyncio
    async def test_returns_all_embedding_keys(self) -> None:
        """Test that result contains all expected keys."""
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 3072

        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding, mock_embedding, mock_embedding]

        mock_client = MagicMock()
        mock_client.models.embed_content.return_value = mock_response

        with patch("src.services.embedding_service._get_client", return_value=mock_client), \
             patch("src.services.embedding_service.get_settings") as mock_settings:
            mock_settings.return_value.embedding_model = "gemini-embedding-001"
            mock_settings.return_value.embedding_dimensions = 3072

            result = await generate_issue_embeddings(
                error_message="TypeError: x is undefined",
                root_cause="Variable not initialized",
                fix_summary="Initialize variable before use",
            )

            assert "error_signature" in result
            assert "root_cause" in result
            assert "fix_summary" in result
            assert len(result["error_signature"]) == 3072
            assert len(result["root_cause"]) == 3072
            assert len(result["fix_summary"]) == 3072


class TestGenerateEmbeddingIntegration:
    """Integration tests for embedding service (requires API key)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_embedding_small_text(self) -> None:
        """Test real embedding generation with small text."""
        # Skip if no API key configured
        try:
            from src.config import get_settings
            settings = get_settings()
            if not settings.google_api_key:
                pytest.skip("GOOGLE_API_KEY not configured")
        except Exception:
            pytest.skip("Settings not configured")

        result = await generate_embedding("test")

        # Should return a vector of correct dimension
        assert len(result) == 3072
        # Should have non-zero values
        assert any(v != 0.0 for v in result)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_batch_embedding(self) -> None:
        """Test real batch embedding generation."""
        try:
            from src.config import get_settings
            settings = get_settings()
            if not settings.google_api_key:
                pytest.skip("GOOGLE_API_KEY not configured")
        except Exception:
            pytest.skip("Settings not configured")

        result = await generate_embeddings_batch(["hello", "world"])

        assert len(result) == 2
        assert len(result[0]) == 3072
        assert len(result[1]) == 3072
        # Vectors should be different
        assert result[0] != result[1]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_similar_texts_have_high_similarity(self) -> None:
        """Test that similar texts produce similar embeddings."""
        try:
            from src.config import get_settings
            settings = get_settings()
            if not settings.google_api_key:
                pytest.skip("GOOGLE_API_KEY not configured")
        except Exception:
            pytest.skip("Settings not configured")

        emb1 = await generate_embedding("Python error")
        emb2 = await generate_embedding("Python exception")
        emb3 = await generate_embedding("cooking recipe")

        sim_similar = await compute_similarity(emb1, emb2)
        sim_different = await compute_similarity(emb1, emb3)

        # Similar texts should have higher similarity
        assert sim_similar > sim_different
