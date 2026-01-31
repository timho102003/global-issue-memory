"""Pipeline orchestrator connecting state manager to batch submission service.

Fetches EXTRACTED records from crawler_state, submits them via
the batch submission service, and updates state accordingly.
"""

from typing import Dict, List

from src.crawler.state_manager import (
    get_issues_by_status,
    update_to_dropped,
    update_to_error,
    update_to_submitted,
)
from src.logging_config import get_logger
from src.models.crawler_state import CrawlerStatus
from src.services.batch_submission_service import submit_crawled_issue

logger = get_logger("crawler.batch_submitter")


async def process_extracted_issues(
    limit: int = 50,
    dry_run: bool = False,
    quality_threshold: float = 0.6,
) -> Dict[str, int]:
    """Process EXTRACTED records through the submission pipeline.

    Fetches EXTRACTED records, filters by quality threshold,
    and submits qualifying issues to GIM.

    Args:
        limit: Maximum number of records to process.
        dry_run: If True, log what would be submitted but don't submit.
        quality_threshold: Minimum quality_score for submission.

    Returns:
        Dict[str, int]: Counts of submitted, dropped, and errored records.
    """
    records = await get_issues_by_status(
        status=CrawlerStatus.EXTRACTED,
        limit=limit,
    )

    counts = {"submitted": 0, "dropped": 0, "errored": 0, "total": len(records)}

    for record in records:
        record_id = record["id"]
        quality_score = record.get("quality_score", 0.0)
        repo = record.get("repo", "unknown")
        issue_number = record.get("issue_number", 0)

        # Filter by quality threshold
        if quality_score < quality_threshold:
            logger.info(
                f"Dropping {repo}#{issue_number}: "
                f"quality_score={quality_score:.2f} < {quality_threshold}"
            )
            if not dry_run:
                await update_to_dropped(record_id, "LOW_QUALITY")
            counts["dropped"] += 1
            continue

        if dry_run:
            logger.info(
                f"[DRY RUN] Would submit {repo}#{issue_number} "
                f"(quality={quality_score:.2f})"
            )
            counts["submitted"] += 1
            continue

        # Submit to GIM
        try:
            result = await submit_crawled_issue(
                error_message=record.get("extracted_error", ""),
                root_cause=record.get("extracted_root_cause", ""),
                fix_summary=record.get("extracted_fix_summary", ""),
                fix_steps=record.get("extracted_fix_steps", []),
                language=record.get("extracted_language"),
                framework=record.get("extracted_framework"),
                source_repo=repo,
                source_issue_number=issue_number,
            )

            if result.success:
                await update_to_submitted(record_id, result.issue_id)
                counts["submitted"] += 1
                logger.info(
                    f"Submitted {repo}#{issue_number} -> "
                    f"{result.issue_type} {result.issue_id}"
                )
            else:
                await update_to_error(record_id, result.error or "Unknown error")
                counts["errored"] += 1
                logger.warning(
                    f"Failed to submit {repo}#{issue_number}: {result.error}"
                )

        except Exception as e:
            await update_to_error(record_id, str(e))
            counts["errored"] += 1
            logger.error(f"Error submitting {repo}#{issue_number}: {e}")

    logger.info(
        f"Batch processing complete: {counts['submitted']} submitted, "
        f"{counts['dropped']} dropped, {counts['errored']} errored "
        f"out of {counts['total']} total"
    )
    return counts
