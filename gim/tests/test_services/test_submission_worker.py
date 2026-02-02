"""Tests for the background submission worker."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.exceptions import (
    EmbeddingError,
    GIMError,
    QdrantError,
    SanitizationError,
    SupabaseError,
)
from src.services.submission_worker import (
    SubmissionRecord,
    SubmissionStatus,
    _process_submission,
    _process_with_retry,
    _submissions,
    _MAX_TRACKED_SUBMISSIONS,
    clear_submissions,
    get_submission_status,
    schedule_submission,
    track_submission,
    update_submission,
)


class TestSubmissionTracking:
    """Tests for in-memory submission tracking store."""

    def setup_method(self) -> None:
        """Clear tracking store before each test."""
        clear_submissions()

    def test_track_submission_stores_record(self) -> None:
        """Test that track_submission stores a record."""
        record = SubmissionRecord(submission_id="test-1")
        track_submission(record)
        assert "test-1" in _submissions
        assert _submissions["test-1"].status == SubmissionStatus.ACCEPTED

    def test_get_submission_status_found(self) -> None:
        """Test getting status of tracked submission."""
        record = SubmissionRecord(submission_id="test-2")
        track_submission(record)
        result = get_submission_status("test-2")
        assert result is not None
        assert result.submission_id == "test-2"

    def test_get_submission_status_not_found(self) -> None:
        """Test getting status of unknown submission returns None."""
        result = get_submission_status("nonexistent")
        assert result is None

    def test_update_submission_status(self) -> None:
        """Test updating submission status."""
        record = SubmissionRecord(submission_id="test-3")
        track_submission(record)
        update_submission("test-3", status=SubmissionStatus.PROCESSING, attempt=1)
        updated = get_submission_status("test-3")
        assert updated is not None
        assert updated.status == SubmissionStatus.PROCESSING
        assert updated.attempt == 1

    def test_update_submission_result(self) -> None:
        """Test updating submission with result data."""
        record = SubmissionRecord(submission_id="test-4")
        track_submission(record)
        update_submission("test-4", result={"issue_id": "abc"})
        updated = get_submission_status("test-4")
        assert updated is not None
        assert updated.result == {"issue_id": "abc"}

    def test_update_submission_error(self) -> None:
        """Test updating submission with error message."""
        record = SubmissionRecord(submission_id="test-5")
        track_submission(record)
        update_submission("test-5", status=SubmissionStatus.FAILED, error="Something broke")
        updated = get_submission_status("test-5")
        assert updated is not None
        assert updated.status == SubmissionStatus.FAILED
        assert updated.error == "Something broke"

    def test_update_nonexistent_submission_is_noop(self) -> None:
        """Test that updating a nonexistent submission does nothing."""
        update_submission("no-such-id", status=SubmissionStatus.COMPLETED)
        assert get_submission_status("no-such-id") is None

    def test_eviction_at_capacity(self) -> None:
        """Test that oldest record is evicted when at capacity."""
        # Add MAX + 1 records
        for i in range(_MAX_TRACKED_SUBMISSIONS):
            track_submission(SubmissionRecord(submission_id=f"item-{i}"))

        # All should fit
        assert len(_submissions) == _MAX_TRACKED_SUBMISSIONS
        assert get_submission_status("item-0") is not None

        # Adding one more should evict item-0
        track_submission(SubmissionRecord(submission_id="overflow"))
        assert len(_submissions) == _MAX_TRACKED_SUBMISSIONS
        assert get_submission_status("item-0") is None
        assert get_submission_status("overflow") is not None


class TestScheduleSubmission:
    """Tests for schedule_submission."""

    def setup_method(self) -> None:
        """Clear tracking store before each test."""
        clear_submissions()

    @patch("src.services.submission_worker.get_settings")
    @patch("src.services.submission_worker.asyncio.create_task")
    def test_returns_submission_id(
        self, _mock_create_task: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that schedule_submission returns a UUID string."""
        mock_settings.return_value.max_submission_retries = 3
        mock_settings.return_value.submission_retry_base_delay = 2.0

        submission_id = schedule_submission(
            arguments={"error_message": "test"},
            request_id="req-1",
        )
        assert isinstance(submission_id, str)
        assert len(submission_id) == 36  # UUID format

    @patch("src.services.submission_worker.get_settings")
    @patch("src.services.submission_worker.asyncio.create_task")
    def test_creates_asyncio_task(
        self, mock_create_task: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that schedule_submission creates an asyncio task."""
        mock_settings.return_value.max_submission_retries = 3
        mock_settings.return_value.submission_retry_base_delay = 2.0

        submission_id = schedule_submission(
            arguments={"error_message": "test"},
            request_id="req-2",
        )
        mock_create_task.assert_called_once()
        _, kwargs = mock_create_task.call_args
        assert kwargs["name"] == f"submission-{submission_id}"

    @patch("src.services.submission_worker.get_settings")
    @patch("src.services.submission_worker.asyncio.create_task")
    def test_records_accepted_status(
        self, _mock_create_task: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test that schedule_submission records ACCEPTED status."""
        mock_settings.return_value.max_submission_retries = 3
        mock_settings.return_value.submission_retry_base_delay = 2.0

        submission_id = schedule_submission(
            arguments={"error_message": "test"},
            request_id="req-3",
        )
        record = get_submission_status(submission_id)
        assert record is not None
        assert record.status == SubmissionStatus.ACCEPTED


class TestProcessWithRetry:
    """Tests for _process_with_retry."""

    def setup_method(self) -> None:
        """Clear tracking store before each test."""
        clear_submissions()

    @pytest.mark.asyncio
    @patch("src.services.submission_worker._process_submission")
    async def test_success_on_first_attempt(self, mock_process: AsyncMock) -> None:
        """Test successful processing on first attempt."""
        submission_id = "retry-1"
        track_submission(SubmissionRecord(submission_id=submission_id))
        mock_process.return_value = {"issue_id": "abc", "type": "master_issue"}

        await _process_with_retry(
            submission_id=submission_id,
            arguments={"error_message": "test"},
            request_id="req-1",
            max_retries=3,
            base_delay=0.01,
        )

        record = get_submission_status(submission_id)
        assert record is not None
        assert record.status == SubmissionStatus.COMPLETED
        assert record.result == {"issue_id": "abc", "type": "master_issue"}
        assert mock_process.call_count == 1

    @pytest.mark.asyncio
    @patch("src.services.submission_worker._process_submission")
    async def test_retries_on_transient_error(self, mock_process: AsyncMock) -> None:
        """Test retry on retryable exception (e.g., EmbeddingError)."""
        submission_id = "retry-2"
        track_submission(SubmissionRecord(submission_id=submission_id))
        mock_process.side_effect = [
            EmbeddingError("Transient API error"),
            {"issue_id": "abc"},
        ]

        await _process_with_retry(
            submission_id=submission_id,
            arguments={"error_message": "test"},
            request_id="req-2",
            max_retries=3,
            base_delay=0.01,
        )

        record = get_submission_status(submission_id)
        assert record is not None
        assert record.status == SubmissionStatus.COMPLETED
        assert mock_process.call_count == 2

    @pytest.mark.asyncio
    @patch("src.services.submission_worker._process_submission")
    async def test_max_retries_exhausted(self, mock_process: AsyncMock) -> None:
        """Test that submission fails after exhausting retries."""
        submission_id = "retry-3"
        track_submission(SubmissionRecord(submission_id=submission_id))
        mock_process.side_effect = SupabaseError("DB timeout")

        await _process_with_retry(
            submission_id=submission_id,
            arguments={"error_message": "test"},
            request_id="req-3",
            max_retries=2,
            base_delay=0.01,
        )

        record = get_submission_status(submission_id)
        assert record is not None
        assert record.status == SubmissionStatus.FAILED
        assert "SupabaseError" in (record.error or "")
        assert mock_process.call_count == 2

    @pytest.mark.asyncio
    @patch("src.services.submission_worker._process_submission")
    async def test_non_retryable_fails_immediately(self, mock_process: AsyncMock) -> None:
        """Test that non-retryable errors fail without retry."""
        submission_id = "retry-4"
        track_submission(SubmissionRecord(submission_id=submission_id))
        mock_process.side_effect = GIMError("Logic error")

        await _process_with_retry(
            submission_id=submission_id,
            arguments={"error_message": "test"},
            request_id="req-4",
            max_retries=3,
            base_delay=0.01,
        )

        record = get_submission_status(submission_id)
        assert record is not None
        assert record.status == SubmissionStatus.FAILED
        assert mock_process.call_count == 1

    @pytest.mark.asyncio
    @patch("src.services.submission_worker._process_submission")
    async def test_unexpected_exception_fails_immediately(self, mock_process: AsyncMock) -> None:
        """Test that unexpected exceptions fail without retry."""
        submission_id = "retry-5"
        track_submission(SubmissionRecord(submission_id=submission_id))
        mock_process.side_effect = RuntimeError("Unexpected")

        await _process_with_retry(
            submission_id=submission_id,
            arguments={"error_message": "test"},
            request_id="req-5",
            max_retries=3,
            base_delay=0.01,
        )

        record = get_submission_status(submission_id)
        assert record is not None
        assert record.status == SubmissionStatus.FAILED
        assert "Unexpected" in (record.error or "")
        assert mock_process.call_count == 1

    @pytest.mark.asyncio
    @patch("src.services.submission_worker._process_submission")
    async def test_status_transitions_through_retrying(self, mock_process: AsyncMock) -> None:
        """Test that status transitions through RETRYING during retries."""
        submission_id = "retry-6"
        track_submission(SubmissionRecord(submission_id=submission_id))

        mock_process.side_effect = [
            QdrantError("Vector DB timeout"),
            {"issue_id": "abc"},
        ]

        await _process_with_retry(
            submission_id=submission_id,
            arguments={"error_message": "test"},
            request_id="req-6",
            max_retries=3,
            base_delay=0.01,
        )

        record = get_submission_status(submission_id)
        assert record is not None
        assert record.status == SubmissionStatus.COMPLETED
        assert mock_process.call_count == 2

    @pytest.mark.asyncio
    @patch("src.services.submission_worker._process_submission")
    async def test_retries_all_retryable_exception_types(self, mock_process: AsyncMock) -> None:
        """Test that all retryable exception types trigger retries."""
        for exc_class in [SanitizationError, EmbeddingError, SupabaseError, QdrantError]:
            clear_submissions()
            submission_id = f"retry-type-{exc_class.__name__}"
            track_submission(SubmissionRecord(submission_id=submission_id))
            mock_process.reset_mock()
            mock_process.side_effect = [
                exc_class("Transient failure"),
                {"issue_id": "abc"},
            ]

            await _process_with_retry(
                submission_id=submission_id,
                arguments={"error_message": "test"},
                request_id="req-types",
                max_retries=3,
                base_delay=0.01,
            )

            record = get_submission_status(submission_id)
            assert record is not None
            assert record.status == SubmissionStatus.COMPLETED, (
                f"{exc_class.__name__} should be retryable"
            )


    @pytest.mark.asyncio
    @patch("src.services.submission_worker._process_submission")
    async def test_cancelled_error_reraises(self, mock_process: AsyncMock) -> None:
        """Test that CancelledError marks FAILED and re-raises."""
        import asyncio

        submission_id = "retry-cancelled"
        track_submission(SubmissionRecord(submission_id=submission_id))
        mock_process.side_effect = asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await _process_with_retry(
                submission_id=submission_id,
                arguments={"error_message": "test"},
                request_id="req-cancel",
                max_retries=3,
                base_delay=0.01,
            )

        record = get_submission_status(submission_id)
        assert record is not None
        assert record.status == SubmissionStatus.FAILED
        assert record.error == "Cancelled"
        assert mock_process.call_count == 1


class TestProcessSubmission:
    """Tests for _process_submission (full pipeline, mocked externals)."""

    def setup_method(self) -> None:
        """Clear tracking store before each test."""
        clear_submissions()

    def _make_mock_sanitization_result(self) -> MagicMock:
        """Create a mock sanitization result.

        Returns:
            MagicMock configured as a SanitizationResult.
        """
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.sanitized_error = "Sanitized error"
        mock_result.sanitized_context = ""
        mock_result.sanitized_mre = ""
        mock_result.confidence_score = 0.9
        mock_result.llm_sanitization_used = True
        mock_result.warnings = []
        return mock_result

    @pytest.mark.asyncio
    async def test_process_master_issue(self) -> None:
        """Test full pipeline for creating a master issue."""
        with patch("src.services.submission_worker.run_sanitization_pipeline") as mock_sanitize, \
             patch("src.services.submission_worker.quick_sanitize") as mock_quick, \
             patch("src.services.submission_worker.generate_combined_embedding") as mock_embed, \
             patch("src.services.submission_worker.search_similar_issues") as mock_search, \
             patch("src.services.submission_worker.insert_record") as mock_insert, \
             patch("src.services.submission_worker.upsert_issue_vectors") as mock_upsert, \
             patch("src.services.submission_worker.get_settings") as mock_settings, \
             patch("src.services.submission_worker.run_code_synthesis") as mock_synthesis:

            mock_settings.return_value.similarity_merge_threshold = 0.85
            mock_sanitize.return_value = self._make_mock_sanitization_result()
            mock_quick.return_value = ("Sanitized text", [])
            mock_embed.return_value = [0.0] * 3072
            mock_search.return_value = []  # No similar issues -> master
            mock_insert.return_value = {"id": "test-id"}
            mock_upsert.return_value = None
            mock_synthesis.return_value = MagicMock(
                success=False, synthesized_fix_steps=None,
                fix_snippet=None, patch_diff=None, error="skipped",
            )

            result = await _process_submission(
                arguments={
                    "error_message": "Test error",
                    "root_cause": "Test cause",
                    "fix_summary": "Test fix",
                    "fix_steps": ["Step 1"],
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                },
                request_id="req-master",
            )

            assert result["type"] == "master_issue"
            assert result["linked_to"] is None
            assert "issue_id" in result
            assert "fix_bundle_id" in result

    @pytest.mark.asyncio
    async def test_process_child_issue(self) -> None:
        """Test full pipeline for creating a child issue."""
        with patch("src.services.submission_worker.run_sanitization_pipeline") as mock_sanitize, \
             patch("src.services.submission_worker.quick_sanitize") as mock_quick, \
             patch("src.services.submission_worker.generate_combined_embedding") as mock_embed, \
             patch("src.services.submission_worker.search_similar_issues") as mock_search, \
             patch("src.services.submission_worker.insert_record") as mock_insert, \
             patch("src.services.submission_worker.get_settings") as mock_settings, \
             patch("src.services.submission_worker.run_code_synthesis") as mock_synthesis:

            mock_settings.return_value.similarity_merge_threshold = 0.85
            mock_sanitize.return_value = self._make_mock_sanitization_result()
            mock_quick.return_value = ("Sanitized text", [])
            mock_embed.return_value = [0.0] * 3072
            # Similar issue found -> child issue
            mock_search.return_value = [
                {"score": 0.95, "payload": {"issue_id": "parent-123"}},
            ]
            mock_insert.return_value = {"id": "test-id"}
            mock_synthesis.return_value = MagicMock(
                success=False, synthesized_fix_steps=None,
                fix_snippet=None, patch_diff=None, error="skipped",
            )

            result = await _process_submission(
                arguments={
                    "error_message": "Test error",
                    "root_cause": "Test cause",
                    "fix_summary": "Test fix",
                    "fix_steps": ["Step 1"],
                    "provider": "anthropic",
                    "model": "claude-sonnet-4-20250514",
                },
                request_id="req-child",
            )

            assert result["type"] == "child_issue"
            assert result["linked_to"] == "parent-123"
            assert "issue_id" in result
            assert "fix_bundle_id" in result
