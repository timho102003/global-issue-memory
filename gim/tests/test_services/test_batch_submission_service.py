"""Tests for the batch submission service.

Mocks sanitization, embedding, and database operations.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.services.batch_submission_service import (
    CRAWLER_CONFIDENCE_PENALTY,
    BatchResult,
    SubmissionResult,
    _classify_root_cause,
    submit_batch,
    submit_crawled_issue,
)


@pytest.fixture
def mock_sanitize():
    """Mock run_sanitization_pipeline.

    Yields:
        AsyncMock: Mock sanitization pipeline.
    """
    with patch(
        "src.services.batch_submission_service.run_sanitization_pipeline",
        new_callable=AsyncMock,
    ) as mock:
        result = MagicMock()
        result.success = True
        result.confidence_score = 0.9
        result.sanitized_error = "TypeError: sanitized"
        result.sanitized_context = "Sanitized context"
        result.sanitized_mre = ""
        mock.return_value = result
        yield mock


@pytest.fixture
def mock_quick_sanitize():
    """Mock quick_sanitize.

    Yields:
        MagicMock: Mock quick_sanitize.
    """
    with patch(
        "src.services.batch_submission_service.quick_sanitize",
    ) as mock:
        mock.side_effect = lambda text: (text, [])
        yield mock


@pytest.fixture
def mock_embedding():
    """Mock generate_combined_embedding.

    Yields:
        AsyncMock: Mock embedding generator.
    """
    with patch(
        "src.services.batch_submission_service.generate_combined_embedding",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = [0.1] * 3072
        yield mock


@pytest.fixture
def mock_search_similar():
    """Mock search_similar_issues.

    Yields:
        AsyncMock: Mock similarity search.
    """
    with patch(
        "src.services.batch_submission_service.search_similar_issues",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_insert():
    """Mock insert_record.

    Yields:
        AsyncMock: Mock insert.
    """
    with patch(
        "src.services.batch_submission_service.insert_record",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = {"id": str(uuid4())}
        yield mock


@pytest.fixture
def mock_upsert_vectors():
    """Mock upsert_issue_vectors.

    Yields:
        AsyncMock: Mock vector upsert.
    """
    with patch(
        "src.services.batch_submission_service.upsert_issue_vectors",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_settings():
    """Mock get_settings.

    Yields:
        MagicMock: Mock settings.
    """
    with patch(
        "src.services.batch_submission_service.get_settings",
    ) as mock:
        settings = MagicMock()
        settings.similarity_merge_threshold = 0.85
        mock.return_value = settings
        yield settings


class TestClassifyRootCause:
    """Tests for _classify_root_cause helper."""

    def test_model_behavior(self) -> None:
        """Model-related root causes are classified."""
        assert _classify_root_cause("The LLM model returns incorrect format") == "model_behavior"

    def test_framework_specific(self) -> None:
        """Framework-related root causes are classified."""
        assert _classify_root_cause("Flask route handler issue") == "framework_specific"

    def test_api_integration(self) -> None:
        """API-related root causes are classified."""
        assert _classify_root_cause("API endpoint returns 401 unauthorized") == "api_integration"

    def test_code_generation(self) -> None:
        """Code-related root causes are classified."""
        assert _classify_root_cause("Type error when accessing None value") == "code_generation"

    def test_environment(self) -> None:
        """Environment-related root causes are classified."""
        assert _classify_root_cause("Missing dependency package not installed") == "environment"

    def test_unknown_defaults_environment(self) -> None:
        """Unknown root causes default to environment."""
        assert _classify_root_cause("Something went wrong somehow") == "environment"


class TestSubmitCrawledIssue:
    """Tests for submit_crawled_issue function."""

    async def test_creates_master_issue(
        self,
        mock_sanitize: AsyncMock,
        mock_quick_sanitize: MagicMock,
        mock_embedding: AsyncMock,
        mock_search_similar: AsyncMock,
        mock_insert: AsyncMock,
        mock_upsert_vectors: AsyncMock,
        mock_settings: MagicMock,
    ) -> None:
        """New issue creates master issue."""
        mock_search_similar.return_value = []  # No similar issues

        result = await submit_crawled_issue(
            error_message="TypeError: test error",
            root_cause="None check missing",
            fix_summary="Added guard clause",
            fix_steps=["Add if check", "Add test"],
            language="python",
            framework="flask",
            source_repo="pallets/flask",
            source_issue_number=42,
        )

        assert result.success is True
        assert result.issue_type == "master_issue"
        assert result.linked_to is None
        # master_issues insert + fix_bundles insert = 2 calls
        assert mock_insert.call_count == 2
        mock_upsert_vectors.assert_called_once()

    async def test_creates_child_issue_when_similar(
        self,
        mock_sanitize: AsyncMock,
        mock_quick_sanitize: MagicMock,
        mock_embedding: AsyncMock,
        mock_search_similar: AsyncMock,
        mock_insert: AsyncMock,
        mock_upsert_vectors: AsyncMock,
        mock_settings: MagicMock,
    ) -> None:
        """Similar issue creates child issue."""
        parent_id = str(uuid4())
        mock_search_similar.return_value = [
            {"score": 0.95, "payload": {"issue_id": parent_id}}
        ]

        result = await submit_crawled_issue(
            error_message="TypeError: test error",
            root_cause="None check missing",
            fix_summary="Added guard clause",
            fix_steps=["Add if check"],
        )

        assert result.success is True
        assert result.issue_type == "child_issue"
        assert result.linked_to == parent_id
        # child_issues insert + fix_bundles insert = 2 calls
        assert mock_insert.call_count == 2
        # No vector upsert for child issues
        mock_upsert_vectors.assert_not_called()

    async def test_confidence_penalty_applied(
        self,
        mock_sanitize: AsyncMock,
        mock_quick_sanitize: MagicMock,
        mock_embedding: AsyncMock,
        mock_search_similar: AsyncMock,
        mock_insert: AsyncMock,
        mock_upsert_vectors: AsyncMock,
        mock_settings: MagicMock,
    ) -> None:
        """Confidence penalty is applied to fix bundle."""
        mock_search_similar.return_value = []
        mock_sanitize.return_value.confidence_score = 0.9

        await submit_crawled_issue(
            error_message="TypeError: test",
            root_cause="Cause",
            fix_summary="Fix",
            fix_steps=["Step"],
        )

        # Find the fix_bundles insert call (second call)
        fix_bundle_call = mock_insert.call_args_list[1]
        fix_bundle_data = fix_bundle_call.kwargs.get("data") or fix_bundle_call[1]["data"]
        expected_confidence = 0.9 * CRAWLER_CONFIDENCE_PENALTY
        assert abs(fix_bundle_data["confidence_score"] - expected_confidence) < 0.001

    async def test_source_set_to_github_crawler(
        self,
        mock_sanitize: AsyncMock,
        mock_quick_sanitize: MagicMock,
        mock_embedding: AsyncMock,
        mock_search_similar: AsyncMock,
        mock_insert: AsyncMock,
        mock_upsert_vectors: AsyncMock,
        mock_settings: MagicMock,
    ) -> None:
        """Source is set to 'github_crawler' on master issues."""
        mock_search_similar.return_value = []

        await submit_crawled_issue(
            error_message="TypeError: test",
            root_cause="Cause",
            fix_summary="Fix",
            fix_steps=["Step"],
        )

        # master_issues insert is the first call
        master_call = mock_insert.call_args_list[0]
        master_data = master_call.kwargs.get("data") or master_call[1]["data"]
        assert master_data["source"] == "github_crawler"
        assert master_data["model_provider"] == "github-crawler"

    async def test_sanitization_failure(
        self,
        mock_sanitize: AsyncMock,
        mock_quick_sanitize: MagicMock,
        mock_embedding: AsyncMock,
        mock_search_similar: AsyncMock,
        mock_insert: AsyncMock,
        mock_upsert_vectors: AsyncMock,
        mock_settings: MagicMock,
    ) -> None:
        """Sanitization failure returns error result."""
        mock_sanitize.return_value.success = False
        mock_sanitize.return_value.confidence_score = 0.3

        result = await submit_crawled_issue(
            error_message="TypeError: test",
            root_cause="Cause",
            fix_summary="Fix",
            fix_steps=["Step"],
        )

        assert result.success is False
        assert "Sanitization" in result.error
        mock_insert.assert_not_called()

    async def test_embedding_failure(
        self,
        mock_sanitize: AsyncMock,
        mock_quick_sanitize: MagicMock,
        mock_embedding: AsyncMock,
        mock_search_similar: AsyncMock,
        mock_insert: AsyncMock,
        mock_upsert_vectors: AsyncMock,
        mock_settings: MagicMock,
    ) -> None:
        """Embedding failure returns error result."""
        mock_embedding.side_effect = Exception("Embedding API error")

        result = await submit_crawled_issue(
            error_message="TypeError: test",
            root_cause="Cause",
            fix_summary="Fix",
            fix_steps=["Step"],
        )

        assert result.success is False
        assert "embed" in result.error.lower() or "Embedding" in result.error


class TestSubmitBatch:
    """Tests for submit_batch function."""

    async def test_batch_processes_all(
        self,
        mock_sanitize: AsyncMock,
        mock_quick_sanitize: MagicMock,
        mock_embedding: AsyncMock,
        mock_search_similar: AsyncMock,
        mock_insert: AsyncMock,
        mock_upsert_vectors: AsyncMock,
        mock_settings: MagicMock,
    ) -> None:
        """Batch processes all issues."""
        mock_search_similar.return_value = []

        issues = [
            {
                "error_message": "Error 1",
                "root_cause": "Cause 1",
                "fix_summary": "Fix 1",
                "fix_steps": ["Step"],
                "source_repo": "pallets/flask",
                "source_issue_number": 1,
            },
            {
                "error_message": "Error 2",
                "root_cause": "Cause 2",
                "fix_summary": "Fix 2",
                "fix_steps": ["Step"],
                "source_repo": "pallets/flask",
                "source_issue_number": 2,
            },
        ]

        result = await submit_batch(issues)

        assert result.total == 2
        assert result.submitted == 2
        assert result.failed == 0

    async def test_batch_error_isolation(
        self,
        mock_sanitize: AsyncMock,
        mock_quick_sanitize: MagicMock,
        mock_embedding: AsyncMock,
        mock_search_similar: AsyncMock,
        mock_insert: AsyncMock,
        mock_upsert_vectors: AsyncMock,
        mock_settings: MagicMock,
    ) -> None:
        """Batch continues processing after individual failure."""
        mock_search_similar.return_value = []

        # First call succeeds, second fails, third succeeds
        call_count = [0]
        original_return = mock_sanitize.return_value

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                result = MagicMock()
                result.success = False
                result.confidence_score = 0.1
                return result
            return original_return

        mock_sanitize.side_effect = side_effect

        issues = [
            {
                "error_message": f"Error {i}",
                "root_cause": f"Cause {i}",
                "fix_summary": f"Fix {i}",
                "fix_steps": ["Step"],
                "source_repo": "test/repo",
                "source_issue_number": i,
            }
            for i in range(1, 4)
        ]

        result = await submit_batch(issues)

        assert result.total == 3
        assert result.submitted == 2
        assert result.failed == 1
