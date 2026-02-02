"""Background submission worker for async issue processing.

Processes gim_submit_issue submissions in the background with exponential
backoff retry for transient failures (Gemini API, Supabase, Qdrant).
Tracks submission status in memory for observability.
"""

import asyncio
import enum
import random
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from src.config import get_settings
from src.db.qdrant_client import search_similar_issues, upsert_issue_vectors
from src.db.supabase_client import insert_record
from src.exceptions import (
    EmbeddingError,
    GIMError,
    QdrantError,
    SanitizationError,
    SupabaseError,
    ValidationError,
)
from src.logging_config import get_logger
from src.services.contribution_classifier import classify_contribution_type
from src.services.embedding_service import generate_combined_embedding
from src.services.environment_extractor import extract_environment_info
from src.services.model_parser import parse_model_info
from src.services.sanitization.code_synthesizer import run_code_synthesis
from src.services.sanitization.pipeline import quick_sanitize, run_sanitization_pipeline
from src.tools.gim_submit_issue import (
    _classify_root_cause,
    _log_submission_event,
    _sanitize_structured_data,
)

logger = get_logger("services.submission_worker")

# Maximum number of tracked submissions (FIFO eviction)
_MAX_TRACKED_SUBMISSIONS = 10_000

# Maximum delay between retries (cap exponential backoff at 5 minutes)
_MAX_RETRY_DELAY_SECONDS = 300.0

# Retryable exception types (transient infrastructure failures)
_RETRYABLE_EXCEPTIONS = (SanitizationError, EmbeddingError, SupabaseError, QdrantError)


class SubmissionStatus(str, enum.Enum):
    """Status of a background submission."""

    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class SubmissionRecord(BaseModel):
    """Tracks the state of a background submission.

    Attributes:
        submission_id: Unique identifier for this submission.
        status: Current processing status.
        attempt: Current attempt number (1-indexed).
        result: Processing result on success.
        error: Error message on failure.
        created_at: When the submission was accepted.
        updated_at: When the record was last updated.
    """

    submission_id: str
    status: SubmissionStatus = SubmissionStatus.ACCEPTED
    attempt: int = Field(default=0, ge=0)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# In-memory tracking store (single-threaded asyncio — no locks needed)
_submissions: OrderedDict[str, SubmissionRecord] = OrderedDict()

# Active asyncio tasks for background submissions (enables graceful shutdown)
_active_tasks: Dict[str, asyncio.Task] = {}  # type: ignore[type-arg]


def track_submission(record: SubmissionRecord) -> None:
    """Store a new submission record, evicting oldest if at capacity.

    Args:
        record: The submission record to track.
    """
    if len(_submissions) >= _MAX_TRACKED_SUBMISSIONS:
        _submissions.popitem(last=False)
    _submissions[record.submission_id] = record


def clear_submissions() -> None:
    """Clear all tracked submissions and active tasks. Intended for testing."""
    _submissions.clear()
    _active_tasks.clear()


def get_submission_status(submission_id: str) -> Optional[SubmissionRecord]:
    """Retrieve the current state of a submission.

    Args:
        submission_id: The submission ID to look up.

    Returns:
        The submission record, or None if not found.
    """
    return _submissions.get(submission_id)


def update_submission(
    submission_id: str,
    *,
    status: Optional[SubmissionStatus] = None,
    attempt: Optional[int] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """Update fields on an existing submission record.

    Args:
        submission_id: The submission ID to update.
        status: New status value.
        attempt: New attempt count.
        result: Processing result dict.
        error: Error message string.
    """
    record = _submissions.get(submission_id)
    if record is None:
        return
    if status is not None:
        record.status = status
    if attempt is not None:
        record.attempt = attempt
    if result is not None:
        record.result = result
    if error is not None:
        record.error = error
    record.updated_at = datetime.now(timezone.utc).isoformat()


async def _process_submission(
    arguments: Dict[str, Any],
    request_id: str,
) -> Dict[str, Any]:
    """Run the full submission pipeline (sanitize, embed, dedup, DB writes, code synthesis).

    This contains the processing logic previously in gim_submit_issue.execute().

    Args:
        arguments: The original tool arguments.
        request_id: Request ID for logging.

    Returns:
        Dict with issue_id, fix_bundle_id, type, linked_to, sanitization info.
    """
    # Extract arguments
    error_message = arguments.get("error_message", "")
    error_context = arguments.get("error_context", "")
    code_snippet = arguments.get("code_snippet", "")
    root_cause = arguments.get("root_cause", "")
    fix_summary = arguments.get("fix_summary", "")
    fix_steps = arguments.get("fix_steps", [])
    code_changes = arguments.get("code_changes", [])
    environment_actions = arguments.get("environment_actions", [])
    verification_steps = arguments.get("verification_steps", [])
    model = arguments.get("model")
    provider = arguments.get("provider")
    language = arguments.get("language")
    framework = arguments.get("framework")
    gim_id = arguments.get("gim_id")

    # New fields
    language_version = arguments.get("language_version")
    framework_version = arguments.get("framework_version")
    os_info = arguments.get("os")
    model_behavior_notes = arguments.get("model_behavior_notes", [])
    validation_success = arguments.get("validation_success")
    validation_notes = arguments.get("validation_notes")

    # Run sanitization pipeline
    logger.debug(f"[{request_id}] Running sanitization pipeline")
    try:
        sanitization_result = await run_sanitization_pipeline(
            error_message=error_message,
            error_context=error_context,
            code_snippet=code_snippet,
            use_llm=True,
        )
    except Exception as e:
        logger.warning(f"[{request_id}] Sanitization pipeline error: {e}")
        raise SanitizationError(
            f"Failed to sanitize content: {str(e)}",
            stage="pipeline",
            original_error=e,
        )

    # Check sanitization confidence
    if not sanitization_result.success:
        raise SanitizationError(
            "Sanitization confidence too low to safely store this submission. "
            f"Confidence: {sanitization_result.confidence_score:.2f}",
            stage="confidence_check",
        )

    # Sanitize root cause and fix summary
    sanitized_root_cause, _ = quick_sanitize(root_cause)
    sanitized_fix_summary, _ = quick_sanitize(fix_summary)
    sanitized_fix_steps = [quick_sanitize(step)[0] for step in fix_steps]

    # Sanitize structured data fields
    code_changes = _sanitize_structured_data(code_changes)
    environment_actions = _sanitize_structured_data(environment_actions)
    verification_steps = _sanitize_structured_data(verification_steps)

    # Generate combined embedding
    logger.debug(f"[{request_id}] Generating combined embedding")
    try:
        embedding = await generate_combined_embedding(
            error_message=sanitization_result.sanitized_error,
            root_cause=sanitized_root_cause,
            fix_summary=sanitized_fix_summary,
        )
    except Exception as e:
        logger.error(f"[{request_id}] Embedding generation error: {e}")
        raise EmbeddingError(
            f"Failed to generate embeddings: {str(e)}",
            original_error=e,
        )

    # Check for similar existing issues
    settings = get_settings()
    similar_issues = await search_similar_issues(
        query_vector=embedding,
        limit=5,
        score_threshold=settings.similarity_merge_threshold,
    )

    # Determine if child or master issue
    is_child_issue = False
    parent_issue_id = None

    if similar_issues and similar_issues[0]["score"] >= settings.similarity_merge_threshold:
        is_child_issue = True
        parent_issue_id = similar_issues[0]["payload"].get("issue_id")

    # Create issue record
    issue_id = str(uuid.uuid4())

    if is_child_issue and parent_issue_id:
        contribution_type = classify_contribution_type(
            error_message=sanitization_result.sanitized_error,
            root_cause=sanitized_root_cause,
            fix_steps=sanitized_fix_steps,
            environment_actions=environment_actions,
            model_behavior_notes=model_behavior_notes,
            validation_success=validation_success,
        )

        environment_info = extract_environment_info(
            language=language,
            framework=framework,
            error_context=error_context,
            language_version=language_version,
            framework_version=framework_version,
            os=os_info,
        )

        model_provider, model_name, model_version = parse_model_info(
            model=model,
            provider=provider,
        )

        logger.info(f"[{request_id}] Creating child issue linked to {parent_issue_id}")
        await insert_record(
            table="child_issues",
            data={
                "id": issue_id,
                "master_issue_id": parent_issue_id,
                "original_error": sanitization_result.sanitized_error,
                "original_context": sanitization_result.sanitized_context,
                "code_snippet": sanitization_result.sanitized_mre,
                "model": model,
                "provider": model_provider,
                "language": language,
                "framework": framework,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "contribution_type": contribution_type.value,
                    "environment": environment_info,
                    "model_name": model_name,
                    "model_version": model_version,
                    "model_behavior_notes": model_behavior_notes,
                    "validation_success": validation_success,
                    "validation_notes": validation_notes,
                },
            },
        )

        result_type = "child_issue"
        result_id = issue_id
        linked_to = parent_issue_id

    else:
        root_cause_category = _classify_root_cause(sanitized_root_cause)

        logger.info(f"[{request_id}] Creating master issue with category {root_cause_category}")
        await insert_record(
            table="master_issues",
            data={
                "id": issue_id,
                "canonical_error": sanitization_result.sanitized_error,
                "sanitized_context": sanitization_result.sanitized_context,
                "sanitized_mre": sanitization_result.sanitized_mre,
                "root_cause": sanitized_root_cause,
                "root_cause_category": root_cause_category,
                "model_provider": provider,
                "language": language,
                "framework": framework,
                "verification_count": 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_verified_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        await upsert_issue_vectors(
            issue_id=issue_id,
            vector=embedding,
            payload={
                "issue_id": issue_id,
                "root_cause_category": root_cause_category,
                "model_provider": provider,
                "status": "active",
            },
        )

        result_type = "master_issue"
        result_id = issue_id
        linked_to = None

    # Run code synthesis (non-blocking — failure does not block submission)
    synthesis_result = None
    try:
        logger.debug(f"[{request_id}] Running code synthesis pipeline")
        synthesis_result = await run_code_synthesis(
            error_message=sanitization_result.sanitized_error,
            error_context=sanitization_result.sanitized_context,
            code_snippet=sanitization_result.sanitized_mre,
            root_cause=sanitized_root_cause,
            fix_steps=sanitized_fix_steps,
            code_changes=code_changes,
        )
        if synthesis_result.success:
            logger.debug(f"[{request_id}] Code synthesis completed successfully")
        else:
            logger.warning(f"[{request_id}] Code synthesis partial failure: {synthesis_result.error}")
    except Exception as e:
        logger.warning(f"[{request_id}] Code synthesis pipeline error (non-blocking): {e}")

    # Create fix bundle
    fix_bundle_id = str(uuid.uuid4())
    logger.debug(f"[{request_id}] Creating fix bundle {fix_bundle_id}")

    final_fix_steps = (
        synthesis_result.synthesized_fix_steps
        if synthesis_result and synthesis_result.synthesized_fix_steps
        else sanitized_fix_steps
    )
    final_code_fix = (
        synthesis_result.fix_snippet
        if synthesis_result and synthesis_result.fix_snippet
        else None
    )
    final_patch_diff = (
        synthesis_result.patch_diff
        if synthesis_result and synthesis_result.patch_diff
        else None
    )

    fix_bundle_data: Dict[str, Any] = {
        "id": fix_bundle_id,
        "master_issue_id": issue_id if not is_child_issue else parent_issue_id,
        "summary": sanitized_fix_summary,
        "fix_steps": final_fix_steps,
        "code_changes": code_changes,
        "environment_actions": environment_actions,
        "verification_steps": verification_steps,
        "confidence_score": sanitization_result.confidence_score,
        "verification_count": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_confirmed_at": datetime.now(timezone.utc).isoformat(),
    }
    if final_code_fix:
        fix_bundle_data["code_fix"] = final_code_fix
    if final_patch_diff:
        fix_bundle_data["patch_diff"] = final_patch_diff

    await insert_record(
        table="fix_bundles",
        data=fix_bundle_data,
    )

    # Log submission event (non-critical)
    await _log_submission_event(
        issue_id=result_id,
        is_child=is_child_issue,
        model=model,
        provider=provider,
        gim_id=gim_id,
    )

    logger.info(f"[{request_id}] Successfully submitted {result_type} {result_id}")
    return {
        "issue_id": result_id,
        "fix_bundle_id": fix_bundle_id,
        "type": result_type,
        "linked_to": linked_to,
        "sanitization": {
            "confidence_score": sanitization_result.confidence_score,
            "llm_used": sanitization_result.llm_sanitization_used,
            "warnings": sanitization_result.warnings,
        },
    }


async def _process_with_retry(
    submission_id: str,
    arguments: Dict[str, Any],
    request_id: str,
    max_retries: int,
    base_delay: float,
) -> None:
    """Process a submission with exponential backoff retry.

    Updates the submission record at each status transition.

    Args:
        submission_id: Unique submission identifier.
        arguments: Original tool arguments.
        request_id: Request ID for logging.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.
    """
    for attempt in range(1, max_retries + 1):
        update_submission(submission_id, status=SubmissionStatus.PROCESSING, attempt=attempt)
        try:
            result = await _process_submission(arguments, request_id)
            update_submission(
                submission_id,
                status=SubmissionStatus.COMPLETED,
                result=result,
            )
            logger.info(f"Submission {submission_id} completed on attempt {attempt}")
            return
        except asyncio.CancelledError:
            logger.info(f"Submission {submission_id} cancelled")
            update_submission(
                submission_id,
                status=SubmissionStatus.FAILED,
                error="Cancelled",
            )
            raise  # Re-raise to properly cancel the task
        except _RETRYABLE_EXCEPTIONS as e:
            if attempt < max_retries:
                delay = min(
                    base_delay * (2 ** (attempt - 1)),
                    _MAX_RETRY_DELAY_SECONDS,
                ) + random.uniform(0, 1)
                logger.warning(
                    f"Submission {submission_id} attempt {attempt} failed "
                    f"({type(e).__name__}: {e}), retrying in {delay:.1f}s"
                )
                update_submission(
                    submission_id,
                    status=SubmissionStatus.RETRYING,
                    error=f"{type(e).__name__}: {e}",
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"Submission {submission_id} exhausted {max_retries} retries "
                    f"({type(e).__name__}: {e})"
                )
                update_submission(
                    submission_id,
                    status=SubmissionStatus.FAILED,
                    error=f"{type(e).__name__}: {e}",
                )
                return
        except (ValidationError, GIMError) as e:
            logger.error(
                f"Submission {submission_id} non-retryable error "
                f"({type(e).__name__}: {e})"
            )
            update_submission(
                submission_id,
                status=SubmissionStatus.FAILED,
                error=f"{type(e).__name__}: {e}",
            )
            return
        except Exception as e:
            logger.exception(
                f"Submission {submission_id} unexpected error "
                f"({type(e).__name__}: {e})"
            )
            update_submission(
                submission_id,
                status=SubmissionStatus.FAILED,
                error=f"Unexpected: {type(e).__name__}: {e}",
            )
            return


def schedule_submission(arguments: Dict[str, Any], request_id: str) -> str:
    """Accept a submission and schedule background processing.

    Creates a tracking record and launches an asyncio task.

    Args:
        arguments: The original tool arguments (already validated).
        request_id: Request ID for logging.

    Returns:
        The submission_id for tracking.
    """
    submission_id = str(uuid.uuid4())
    record = SubmissionRecord(submission_id=submission_id)
    track_submission(record)

    settings = get_settings()
    task = asyncio.create_task(
        _process_with_retry(
            submission_id=submission_id,
            arguments=arguments,
            request_id=request_id,
            max_retries=settings.max_submission_retries,
            base_delay=settings.submission_retry_base_delay,
        ),
        name=f"submission-{submission_id}",
    )
    _active_tasks[submission_id] = task
    task.add_done_callback(lambda _t: _active_tasks.pop(submission_id, None))

    logger.info(f"Scheduled submission {submission_id} (request_id={request_id})")
    return submission_id
