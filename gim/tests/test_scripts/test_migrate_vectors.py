"""Tests for vector migration script."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


class TestFetchAllIssues:
    """Tests for fetch_all_issues."""

    @pytest.mark.asyncio
    async def test_fetches_issues_with_fix_summaries(self) -> None:
        """Test that issues and their fix summaries are fetched."""
        from scripts.migrate_vectors import fetch_all_issues

        mock_issues = [
            {
                "id": "issue-1",
                "canonical_error": "TypeError",
                "root_cause": "bad type",
                "root_cause_category": "type_error",
                "model_provider": "anthropic",
            },
            {
                "id": "issue-2",
                "canonical_error": "ValueError",
                "root_cause": "bad value",
                "root_cause_category": "validation",
                "model_provider": "openai",
            },
        ]
        mock_bundles_1 = [{"summary": "Fix the type"}]
        mock_bundles_2: list = []

        async def mock_query(table: str, **kwargs) -> list:
            if table == "master_issues":
                return mock_issues
            if kwargs.get("filters", {}).get("issue_id") == "issue-1":
                return mock_bundles_1
            return mock_bundles_2

        with patch("scripts.migrate_vectors.query_records", side_effect=mock_query):
            result = await fetch_all_issues()

        assert len(result) == 2
        assert result[0]["fix_summary"] == "Fix the type"
        assert result[1]["fix_summary"] == ""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_issues(self) -> None:
        """Test that empty list is returned when no issues exist."""
        from scripts.migrate_vectors import fetch_all_issues

        with patch("scripts.migrate_vectors.query_records", new_callable=AsyncMock, return_value=[]):
            result = await fetch_all_issues()

        assert result == []


class TestDropCollection:
    """Tests for drop_collection."""

    def test_drops_existing_collection(self) -> None:
        """Test that existing collection is dropped."""
        from scripts.migrate_vectors import drop_collection

        mock_collection = MagicMock()
        mock_collection.name = "gim_issues"

        mock_client = MagicMock()
        mock_client.get_collections.return_value.collections = [mock_collection]

        with patch("scripts.migrate_vectors.get_qdrant_client", return_value=mock_client):
            drop_collection()

        mock_client.delete_collection.assert_called_once_with(collection_name="gim_issues")

    def test_skips_when_collection_missing(self) -> None:
        """Test that nothing is dropped when collection does not exist."""
        from scripts.migrate_vectors import drop_collection

        mock_client = MagicMock()
        mock_client.get_collections.return_value.collections = []

        with patch("scripts.migrate_vectors.get_qdrant_client", return_value=mock_client):
            drop_collection()

        mock_client.delete_collection.assert_not_called()


class TestMigrate:
    """Tests for the full migration flow."""

    @pytest.mark.asyncio
    async def test_dry_run_does_not_write(self) -> None:
        """Test that dry run does not modify Qdrant."""
        from scripts.migrate_vectors import migrate

        mock_issues = [
            {
                "id": "issue-1",
                "canonical_error": "Error",
                "root_cause": "cause",
                "root_cause_category": "misc",
                "model_provider": "anthropic",
                "fix_summary": "fix it",
            },
        ]

        with patch("scripts.migrate_vectors.fetch_all_issues", new_callable=AsyncMock, return_value=mock_issues), \
             patch("scripts.migrate_vectors.drop_collection") as mock_drop, \
             patch("scripts.migrate_vectors.ensure_collection_exists") as mock_ensure, \
             patch("scripts.migrate_vectors.generate_combined_embedding") as mock_embed, \
             patch("scripts.migrate_vectors.upsert_issue_vectors") as mock_upsert, \
             patch("scripts.migrate_vectors.get_settings") as mock_settings:

            mock_settings.return_value.embedding_model = "gemini-embedding-001"
            mock_settings.return_value.embedding_dimensions = 3072

            await migrate(dry_run=True)

            mock_drop.assert_not_called()
            mock_ensure.assert_not_called()
            mock_embed.assert_not_called()
            mock_upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_full_migration_processes_all_issues(self) -> None:
        """Test that migration processes every issue."""
        from scripts.migrate_vectors import migrate

        mock_issues = [
            {
                "id": "issue-1",
                "canonical_error": "TypeError",
                "root_cause": "bad type",
                "root_cause_category": "type_error",
                "model_provider": "anthropic",
                "fix_summary": "fix type",
            },
            {
                "id": "issue-2",
                "canonical_error": "ValueError",
                "root_cause": "bad value",
                "root_cause_category": "validation",
                "model_provider": "openai",
                "fix_summary": "fix value",
            },
        ]
        mock_vector = [0.1] * 3072

        with patch("scripts.migrate_vectors.fetch_all_issues", new_callable=AsyncMock, return_value=mock_issues), \
             patch("scripts.migrate_vectors.drop_collection") as mock_drop, \
             patch("scripts.migrate_vectors.ensure_collection_exists", new_callable=AsyncMock) as mock_ensure, \
             patch("scripts.migrate_vectors.generate_combined_embedding", new_callable=AsyncMock, return_value=mock_vector) as mock_embed, \
             patch("scripts.migrate_vectors.upsert_issue_vectors", new_callable=AsyncMock) as mock_upsert, \
             patch("scripts.migrate_vectors.get_settings") as mock_settings:

            mock_settings.return_value.embedding_model = "gemini-embedding-001"
            mock_settings.return_value.embedding_dimensions = 3072

            await migrate(dry_run=False)

            mock_drop.assert_called_once()
            mock_ensure.assert_called_once()
            assert mock_embed.call_count == 2
            assert mock_upsert.call_count == 2

            # Verify first upsert call
            mock_upsert.assert_any_call(
                issue_id="issue-1",
                vector=mock_vector,
                payload={
                    "issue_id": "issue-1",
                    "root_cause_category": "type_error",
                    "model_provider": "anthropic",
                    "status": "active",
                },
            )

    @pytest.mark.asyncio
    async def test_no_issues_exits_early(self) -> None:
        """Test that migration exits early with no issues."""
        from scripts.migrate_vectors import migrate

        with patch("scripts.migrate_vectors.fetch_all_issues", new_callable=AsyncMock, return_value=[]), \
             patch("scripts.migrate_vectors.drop_collection") as mock_drop, \
             patch("scripts.migrate_vectors.get_settings") as mock_settings:

            mock_settings.return_value.embedding_model = "gemini-embedding-001"
            mock_settings.return_value.embedding_dimensions = 3072

            await migrate(dry_run=False)

            mock_drop.assert_not_called()

    @pytest.mark.asyncio
    async def test_continues_on_single_issue_failure(self) -> None:
        """Test that migration continues when one issue fails."""
        from scripts.migrate_vectors import migrate

        mock_issues = [
            {
                "id": "issue-1",
                "canonical_error": "Error1",
                "root_cause": "cause1",
                "root_cause_category": "misc",
                "model_provider": "anthropic",
                "fix_summary": "fix1",
            },
            {
                "id": "issue-2",
                "canonical_error": "Error2",
                "root_cause": "cause2",
                "root_cause_category": "misc",
                "model_provider": "openai",
                "fix_summary": "fix2",
            },
        ]
        mock_vector = [0.1] * 3072

        # First call raises, second succeeds
        embed_side_effects = [Exception("API error"), mock_vector]

        with patch("scripts.migrate_vectors.fetch_all_issues", new_callable=AsyncMock, return_value=mock_issues), \
             patch("scripts.migrate_vectors.drop_collection"), \
             patch("scripts.migrate_vectors.ensure_collection_exists", new_callable=AsyncMock), \
             patch("scripts.migrate_vectors.generate_combined_embedding", new_callable=AsyncMock, side_effect=embed_side_effects), \
             patch("scripts.migrate_vectors.upsert_issue_vectors", new_callable=AsyncMock) as mock_upsert, \
             patch("scripts.migrate_vectors.get_settings") as mock_settings:

            mock_settings.return_value.embedding_model = "gemini-embedding-001"
            mock_settings.return_value.embedding_dimensions = 3072

            with pytest.raises(SystemExit) as exc_info:
                await migrate(dry_run=False)

            assert exc_info.value.code == 1
            # Only the second issue should have been upserted
            assert mock_upsert.call_count == 1
