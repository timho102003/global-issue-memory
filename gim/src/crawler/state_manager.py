"""Crawler state management using Supabase.

Provides CRUD operations for the crawler_state table,
tracking each GitHub issue through the discovery-fetch-extract-submit pipeline.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.db.supabase_client import (
    count_records,
    insert_record,
    query_records,
    update_record,
)
from src.logging_config import get_logger
from src.models.crawler_state import (
    CrawlerStateCreate,
    CrawlerStateExtracted,
    CrawlerStateFetched,
    CrawlerStatus,
)

logger = get_logger("crawler.state_manager")

TABLE = "crawler_state"


async def create_pending_issues(
    issues: List[CrawlerStateCreate],
) -> int:
    """Bulk-insert discovered issues as PENDING, skipping duplicates.

    Args:
        issues: List of issue discovery data.

    Returns:
        int: Number of issues successfully created.
    """
    created = 0
    for issue in issues:
        try:
            exists = await issue_exists(issue.repo, issue.issue_number)
            if exists:
                logger.debug(f"Skipping duplicate: {issue.repo}#{issue.issue_number}")
                continue

            data = {
                "repo": issue.repo,
                "issue_number": issue.issue_number,
                "github_issue_id": issue.github_issue_id,
                "status": CrawlerStatus.PENDING.value,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                "state_reason": issue.state_reason,
                "issue_title": issue.issue_title,
                "issue_labels": issue.issue_labels,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await insert_record(table=TABLE, data=data)
            created += 1
            logger.debug(f"Created PENDING: {issue.repo}#{issue.issue_number}")
        except Exception as e:
            logger.warning(
                f"Failed to create {issue.repo}#{issue.issue_number}: {e}"
            )
    return created


async def update_to_fetched(
    record_id: str,
    data: CrawlerStateFetched,
) -> Dict[str, Any]:
    """Update a record to FETCHED status with raw data.

    Args:
        record_id: UUID of the crawler_state record.
        data: Fetched data to store.

    Returns:
        Dict[str, Any]: Updated record.
    """
    update_data = {
        "status": CrawlerStatus.FETCHED.value,
        "has_merged_pr": data.has_merged_pr,
        "pr_number": data.pr_number,
        "raw_issue_body": data.raw_issue_body,
        "raw_comments": data.raw_comments,
        "raw_pr_body": data.raw_pr_body,
        "raw_pr_diff_summary": data.raw_pr_diff_summary,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return await update_record(table=TABLE, record_id=record_id, data=update_data)


async def update_to_extracted(
    record_id: str,
    data: CrawlerStateExtracted,
) -> Dict[str, Any]:
    """Update a record to EXTRACTED status with LLM results.

    Args:
        record_id: UUID of the crawler_state record.
        data: Extraction results to store.

    Returns:
        Dict[str, Any]: Updated record.
    """
    update_data = {
        "status": CrawlerStatus.EXTRACTED.value,
        "extracted_error": data.extracted_error,
        "extracted_root_cause": data.extracted_root_cause,
        "extracted_fix_summary": data.extracted_fix_summary,
        "extracted_fix_steps": data.extracted_fix_steps,
        "extracted_language": data.extracted_language,
        "extracted_framework": data.extracted_framework,
        "extraction_confidence": data.extraction_confidence,
        "quality_score": data.quality_score,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return await update_record(table=TABLE, record_id=record_id, data=update_data)


async def update_to_submitted(
    record_id: str,
    gim_issue_id: str,
) -> Dict[str, Any]:
    """Update a record to SUBMITTED status with GIM issue linkage.

    Args:
        record_id: UUID of the crawler_state record.
        gim_issue_id: UUID of the created GIM issue.

    Returns:
        Dict[str, Any]: Updated record.
    """
    update_data = {
        "status": CrawlerStatus.SUBMITTED.value,
        "gim_issue_id": gim_issue_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return await update_record(table=TABLE, record_id=record_id, data=update_data)


async def update_to_dropped(
    record_id: str,
    drop_reason: str,
) -> Dict[str, Any]:
    """Update a record to DROPPED status.

    Args:
        record_id: UUID of the crawler_state record.
        drop_reason: Reason for dropping (from DropReason enum).

    Returns:
        Dict[str, Any]: Updated record.
    """
    update_data = {
        "status": CrawlerStatus.DROPPED.value,
        "drop_reason": drop_reason,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return await update_record(table=TABLE, record_id=record_id, data=update_data)


async def update_to_error(
    record_id: str,
    error_msg: str,
) -> Dict[str, Any]:
    """Update a record to ERROR status and increment retry count.

    Args:
        record_id: UUID of the crawler_state record.
        error_msg: Error message describing the failure.

    Returns:
        Dict[str, Any]: Updated record.
    """
    # First get current retry_count
    records = await query_records(
        table=TABLE,
        filters={"id": record_id},
        select="retry_count",
        limit=1,
    )
    current_retry = records[0]["retry_count"] if records else 0

    update_data = {
        "status": CrawlerStatus.ERROR.value,
        "last_error": error_msg,
        "retry_count": current_retry + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    return await update_record(table=TABLE, record_id=record_id, data=update_data)


async def get_issues_by_status(
    status: CrawlerStatus,
    repo: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Query crawler records by pipeline status.

    Args:
        status: Pipeline status to filter by.
        repo: Optional repo filter.
        limit: Maximum records to return.

    Returns:
        List[Dict[str, Any]]: Matching records.
    """
    filters: Dict[str, Any] = {"status": status.value}
    if repo:
        filters["repo"] = repo
    return await query_records(
        table=TABLE,
        filters=filters,
        limit=limit,
        order_by="created_at",
        ascending=True,
    )


async def get_retryable_errors(
    max_retries: int = 3,
) -> List[Dict[str, Any]]:
    """Get ERROR records that can be retried.

    Args:
        max_retries: Maximum retry attempts before giving up.

    Returns:
        List[Dict[str, Any]]: Error records with retry_count < max_retries.
    """
    # Query all ERROR records, then filter by retry count client-side
    # (Supabase PostgREST doesn't natively support lt filters in the simple client)
    records = await query_records(
        table=TABLE,
        filters={"status": CrawlerStatus.ERROR.value},
        limit=100,
        order_by="created_at",
        ascending=True,
    )
    return [r for r in records if r.get("retry_count", 0) < max_retries]


async def get_last_closed_date(repo: str) -> Optional[str]:
    """Get the most recent closed_at date for a repo.

    Used to resume crawling from where we left off.

    Args:
        repo: Repository in 'owner/name' format.

    Returns:
        Optional[str]: ISO date string of most recent closed_at, or None.
    """
    records = await query_records(
        table=TABLE,
        filters={"repo": repo},
        select="closed_at",
        limit=1,
        order_by="closed_at",
        ascending=False,
    )
    if records and records[0].get("closed_at"):
        return records[0]["closed_at"]
    return None


async def get_stats() -> Dict[str, int]:
    """Get count of records by status.

    Returns:
        Dict[str, int]: Mapping of status -> count.
    """
    stats: Dict[str, int] = {}
    for status in CrawlerStatus:
        count = await count_records(
            table=TABLE,
            filters={"status": status.value},
        )
        stats[status.value] = count
    return stats


async def issue_exists(repo: str, issue_number: int) -> bool:
    """Check if an issue has already been crawled.

    Args:
        repo: Repository in 'owner/name' format.
        issue_number: GitHub issue number.

    Returns:
        bool: True if the issue already exists in crawler_state.
    """
    records = await query_records(
        table=TABLE,
        filters={"repo": repo, "issue_number": issue_number},
        select="id",
        limit=1,
    )
    return len(records) > 0
