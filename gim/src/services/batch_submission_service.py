"""Batch submission service for crawled GitHub issues.

Follows the same pipeline as gim_submit_issue.py but bypasses
MCP transport and rate limiting for bulk processing.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.config import get_settings
from src.db.qdrant_client import search_similar_issues, upsert_issue_vectors
from src.db.supabase_client import insert_record
from src.exceptions import (
    EmbeddingError,
    GIMError,
    SanitizationError,
)
from src.logging_config import get_logger
from src.services.embedding_service import generate_combined_embedding
from src.services.sanitization.pipeline import quick_sanitize, run_sanitization_pipeline

logger = get_logger("services.batch_submission")

# Confidence penalty for crawler-sourced issues (less reliable than human-reported)
CRAWLER_CONFIDENCE_PENALTY = 0.7


@dataclass
class SubmissionResult:
    """Result of a single issue submission.

    Attributes:
        success: Whether submission succeeded.
        issue_id: GIM issue UUID (master or child).
        fix_bundle_id: Fix bundle UUID.
        issue_type: 'master_issue' or 'child_issue'.
        linked_to: Parent issue ID if child.
        error: Error message if failed.
    """

    success: bool = False
    issue_id: Optional[str] = None
    fix_bundle_id: Optional[str] = None
    issue_type: Optional[str] = None
    linked_to: Optional[str] = None
    error: Optional[str] = None


@dataclass
class BatchResult:
    """Result of a batch submission operation.

    Attributes:
        total: Total issues processed.
        submitted: Number successfully submitted.
        failed: Number that failed.
        results: Per-issue results.
    """

    total: int = 0
    submitted: int = 0
    failed: int = 0
    results: List[SubmissionResult] = field(default_factory=list)


def _classify_root_cause(root_cause: str) -> str:
    """Classify root cause into a RootCauseCategory value.

    Replicates the logic from gim_submit_issue.py for consistency.

    Args:
        root_cause: Root cause description.

    Returns:
        str: Root cause category.
    """
    root_cause_lower = root_cause.lower()

    model_behavior_keywords = [
        "model", "llm", "ai", "claude", "gpt", "openai", "anthropic",
        "tool calling", "function calling", "schema", "prompt",
        "hallucination", "context", "token", "response format",
    ]
    framework_keywords = [
        "langchain", "llamaindex", "fastapi", "django", "flask",
        "react", "next", "vue", "angular", "tensorflow", "pytorch",
        "pandas", "numpy", "framework", "library", "sdk",
    ]
    api_integration_keywords = [
        "api", "endpoint", "request", "response", "http", "rest",
        "auth", "authentication", "permission", "forbidden", "unauthorized",
        "connection", "timeout", "network", "socket", "cors", "header",
    ]
    code_generation_keywords = [
        "type error", "type mismatch", "cannot be", "expected",
        "syntax", "parse", "invalid", "none", "null", "undefined",
        "nonetype", "attribute", "key error", "index", "logic",
    ]
    environment_keywords = [
        "missing", "not found", "import error", "module not found",
        "dependency", "package", "install", "pip", "npm", "version",
        "incompatible", "upgrade", "downgrade", "config", "configuration",
    ]

    if any(kw in root_cause_lower for kw in model_behavior_keywords):
        return "model_behavior"
    if any(kw in root_cause_lower for kw in framework_keywords):
        return "framework_specific"
    if any(kw in root_cause_lower for kw in api_integration_keywords):
        return "api_integration"
    if any(kw in root_cause_lower for kw in code_generation_keywords):
        return "code_generation"
    if any(kw in root_cause_lower for kw in environment_keywords):
        return "environment"

    return "environment"


async def submit_crawled_issue(
    error_message: str,
    root_cause: str,
    fix_summary: str,
    fix_steps: List[str],
    language: Optional[str] = None,
    framework: Optional[str] = None,
    source_repo: Optional[str] = None,
    source_issue_number: Optional[int] = None,
) -> SubmissionResult:
    """Submit a single crawled issue to GIM.

    Follows the same pipeline as gim_submit_issue.py:
    1. Sanitize content
    2. Generate embedding
    3. Check for similar issues
    4. Create master or child issue
    5. Create fix bundle with confidence penalty

    Args:
        error_message: Extracted error message.
        root_cause: Extracted root cause.
        fix_summary: Extracted fix summary.
        fix_steps: List of fix step strings.
        language: Programming language.
        framework: Framework name.
        source_repo: Source GitHub repository.
        source_issue_number: Source GitHub issue number.

    Returns:
        SubmissionResult: Result of the submission.
    """
    try:
        # 1. Run sanitization pipeline
        sanitization_result = await run_sanitization_pipeline(
            error_message=error_message,
            error_context="",
            code_snippet="",
            use_llm=True,
        )

        if not sanitization_result.success:
            return SubmissionResult(
                success=False,
                error=f"Sanitization failed: confidence={sanitization_result.confidence_score:.2f}",
            )

        # Quick-sanitize root cause, fix summary, fix steps
        sanitized_root_cause, _ = quick_sanitize(root_cause)
        sanitized_fix_summary, _ = quick_sanitize(fix_summary)
        sanitized_fix_steps = [quick_sanitize(step)[0] for step in fix_steps]

        # 2. Generate combined embedding
        try:
            embedding = await generate_combined_embedding(
                error_message=sanitization_result.sanitized_error,
                root_cause=sanitized_root_cause,
                fix_summary=sanitized_fix_summary,
            )
        except Exception as e:
            raise EmbeddingError(
                f"Failed to generate embeddings: {e}",
                original_error=e,
            )

        # 3. Check for similar existing issues
        settings = get_settings()
        similar_issues = await search_similar_issues(
            query_vector=embedding,
            limit=5,
            score_threshold=settings.similarity_merge_threshold,
        )

        # 4. Create master or child issue
        issue_id = str(uuid.uuid4())
        is_child_issue = False
        parent_issue_id = None

        if similar_issues and similar_issues[0]["score"] >= settings.similarity_merge_threshold:
            is_child_issue = True
            parent_issue_id = similar_issues[0]["payload"].get("issue_id")

            await insert_record(
                table="child_issues",
                data={
                    "id": issue_id,
                    "master_issue_id": parent_issue_id,
                    "original_error": sanitization_result.sanitized_error,
                    "original_context": sanitization_result.sanitized_context,
                    "code_snippet": sanitization_result.sanitized_mre,
                    "model": "github-crawler",
                    "provider": "github-crawler",
                    "language": language,
                    "framework": framework,
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "source": "github_crawler",
                        "source_repo": source_repo,
                        "source_issue_number": source_issue_number,
                    },
                },
            )
        else:
            root_cause_category = _classify_root_cause(sanitized_root_cause)

            await insert_record(
                table="master_issues",
                data={
                    "id": issue_id,
                    "canonical_error": sanitization_result.sanitized_error,
                    "sanitized_context": sanitization_result.sanitized_context,
                    "sanitized_mre": sanitization_result.sanitized_mre,
                    "root_cause": sanitized_root_cause,
                    "root_cause_category": root_cause_category,
                    "model_provider": "github-crawler",
                    "language": language,
                    "framework": framework,
                    "source": "github_crawler",
                    "verification_count": 1,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_verified_at": datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "source_repo": source_repo,
                        "source_issue_number": source_issue_number,
                    },
                },
            )

            # Store vector in Qdrant
            await upsert_issue_vectors(
                issue_id=issue_id,
                vector=embedding,
                payload={
                    "issue_id": issue_id,
                    "root_cause_category": root_cause_category,
                    "model_provider": "github-crawler",
                    "status": "active",
                },
            )

        # 5. Create fix bundle with confidence penalty
        fix_bundle_id = str(uuid.uuid4())
        penalized_confidence = sanitization_result.confidence_score * CRAWLER_CONFIDENCE_PENALTY

        fix_bundle_data: Dict[str, Any] = {
            "id": fix_bundle_id,
            "master_issue_id": issue_id if not is_child_issue else parent_issue_id,
            "summary": sanitized_fix_summary,
            "fix_steps": sanitized_fix_steps,
            "code_changes": [],
            "environment_actions": [],
            "verification_steps": [],
            "confidence_score": penalized_confidence,
            "verification_count": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_confirmed_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "source": "github_crawler",
                "source_repo": source_repo,
                "source_issue_number": source_issue_number,
                "original_confidence": sanitization_result.confidence_score,
                "penalty_factor": CRAWLER_CONFIDENCE_PENALTY,
            },
        }

        await insert_record(table="fix_bundles", data=fix_bundle_data)

        result_type = "child_issue" if is_child_issue else "master_issue"
        logger.info(
            f"Submitted {result_type} {issue_id} from "
            f"{source_repo}#{source_issue_number}"
        )

        return SubmissionResult(
            success=True,
            issue_id=issue_id,
            fix_bundle_id=fix_bundle_id,
            issue_type=result_type,
            linked_to=parent_issue_id,
        )

    except (SanitizationError, EmbeddingError, GIMError) as e:
        logger.error(f"Submission error: {e.message}")
        return SubmissionResult(success=False, error=e.message)
    except Exception as e:
        logger.exception("Unexpected error during submission")
        return SubmissionResult(success=False, error=str(e))


async def submit_batch(
    issues: List[Dict[str, Any]],
) -> BatchResult:
    """Submit multiple crawled issues to GIM with per-issue error isolation.

    Args:
        issues: List of dicts with keys: error_message, root_cause,
                fix_summary, fix_steps, language, framework,
                source_repo, source_issue_number.

    Returns:
        BatchResult: Aggregate results of the batch.
    """
    result = BatchResult(total=len(issues))

    for issue_data in issues:
        submission = await submit_crawled_issue(
            error_message=issue_data["error_message"],
            root_cause=issue_data["root_cause"],
            fix_summary=issue_data["fix_summary"],
            fix_steps=issue_data["fix_steps"],
            language=issue_data.get("language"),
            framework=issue_data.get("framework"),
            source_repo=issue_data.get("source_repo"),
            source_issue_number=issue_data.get("source_issue_number"),
        )

        result.results.append(submission)
        if submission.success:
            result.submitted += 1
        else:
            result.failed += 1
            logger.warning(
                f"Failed to submit {issue_data.get('source_repo')}#"
                f"{issue_data.get('source_issue_number')}: {submission.error}"
            )

    logger.info(
        f"Batch complete: {result.submitted}/{result.total} submitted, "
        f"{result.failed} failed"
    )
    return result
