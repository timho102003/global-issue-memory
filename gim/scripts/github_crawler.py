"""CLI entry point for the GitHub issue crawler.

Usage:
    python -m scripts.github_crawler [OPTIONS]

Options:
    --repos REPO [REPO ...]   Repos to crawl (default: popular repos)
    --since DATE              ISO date, only issues closed after this
    --max-issues N            Max issues per repo (default: 50)
    --dry-run                 Extract and score but don't submit to GIM
    --phase {discover,fetch,extract,submit,full}
                              Run specific phase (default: full)
    --status-report           Print status counts and exit
    --retry-errors            Retry ERROR state issues
    --revisit-dropped         Revisit DROPPED issues to check if resolved
    --revisit-days N          Days threshold for revisit (default: 5)
    --quality-threshold F     Quality score threshold (default: 0.6)
    --limit N                 Max records per phase (default: 100)
"""

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from typing import List, Optional

from src.crawler.batch_submitter import process_extracted_issues
from src.crawler.github_fetcher import discover_issues, fetch_issue_details
from src.crawler.issue_filter import filter_issue
from src.crawler.llm_extractor import extract_issue_data, score_quality
from src.crawler.state_manager import (
    create_pending_issues,
    get_dropped_issues_for_revisit,
    get_issues_by_status,
    get_last_closed_date,
    get_retryable_errors,
    get_stats,
    reset_dropped_to_pending,
    update_last_revisited_at,
    update_to_dropped,
    update_to_error,
    update_to_extracted,
    update_to_fetched,
)
from src.db.supabase_client import update_record
from src.logging_config import configure_logging, get_logger
from src.models.crawler_state import (
    CrawlerStateCreate,
    CrawlerStateExtracted,
    CrawlerStateFetched,
    CrawlerStatus,
)

logger = get_logger("scripts.github_crawler")

DEFAULT_REPOS = [
    # -- LLM / AI Agent Frameworks --
    "langchain-ai/langchain",
    "BerriAI/litellm",
    "openai/openai-python",
    "openai/openai-agents-python",
    "anthropics/anthropic-sdk-python",
    "run-llama/llama_index",
    "crewAIInc/crewAI",
    "microsoft/autogen",
    "deepset-ai/haystack",
    "microsoft/semantic-kernel",
    "ollama/ollama",
    "vllm-project/vllm",
    "QwenLM/Qwen3-TTS",
    # -- Vector Databases --
    "qdrant/qdrant",
    "chroma-core/chroma",
    "weaviate/weaviate",
    "milvus-io/pymilvus",
    "pinecone-io/pinecone-python-client",
    # -- AI Agent Frameworks (additional) --
    "pydantic/pydantic-ai",
    "google/adk-python",
    # -- Vibe Coding / AI Coding Agents --
    "openclaw/openclaw",
    "stackblitz-labs/bolt.diy",
    "dyad-sh/dyad",
    "continuedev/continue",
    "Aider-AI/aider",
    "openinterpreter/open-interpreter",
    # -- Frontend Frameworks --
    "vercel/next.js",
    "facebook/react",
    "vuejs/core",
    "sveltejs/kit",
    "withastro/astro",
    "nuxt/nuxt",
    "remix-run/remix",
    "TanStack/query",
    "TanStack/router",
    "TanStack/table",
    # -- Backend Frameworks --
    "tiangolo/fastapi",
    "pallets/flask",
    "expressjs/express",
    "django/django",
    "nestjs/nest",
    "honojs/hono",
    "elysiajs/elysia",
    # -- Machine Learning --
    "pytorch/pytorch",
    "tensorflow/tensorflow",
    "huggingface/transformers",
    "scikit-learn/scikit-learn",
    "jax-ml/jax",
    # -- Python Ecosystem --
    "psf/requests",
    "pydantic/pydantic",
    "sqlalchemy/sqlalchemy",
    "celery/celery",
    "encode/httpx",
    # -- MCP Ecosystem --
    "modelcontextprotocol/python-sdk",
    "modelcontextprotocol/typescript-sdk",
    # -- Workflow Automation --
    "n8n-io/n8n",
    # -- RAG / Web Data --
    "infiniflow/ragflow",
    "firecrawl/firecrawl",
    # -- AI SDKs --
    "vercel/ai",
    "mastra-ai/mastra",
    # -- UI Frameworks & Components --
    "shadcn-ui/ui",
    "tailwindlabs/tailwindcss",
    "reflex-dev/reflex",
    # -- Database Clients / ORMs --
    "prisma/prisma",
    "drizzle-team/drizzle-orm",
    "supabase/supabase-js",
    "supabase/supabase-py",
    # -- AI Bot --
    "HKUDS/nanobot",
    "openclaw/openclaw"
]


async def run_discover(
    repos: List[str],
    since: Optional[datetime],
    max_issues: int,
) -> int:
    """Discover phase: find closed issues from GitHub repos.

    Args:
        repos: List of repos to crawl.
        since: Only issues closed after this date.
        max_issues: Max issues per repo.

    Returns:
        int: Total issues created.
    """
    total_created = 0
    for repo in repos:
        logger.info(f"Discovering issues from {repo}...")

        # Resume from last crawled date if no explicit since
        effective_since = since
        if effective_since is None:
            last_date = await get_last_closed_date(repo)
            if last_date:
                effective_since = datetime.fromisoformat(
                    last_date.replace("Z", "+00:00")
                )
                logger.info(f"Resuming from {effective_since}")

        raw_issues = await discover_issues(
            repo_name=repo,
            since=effective_since,
            max_issues=max_issues,
        )

        issues = [CrawlerStateCreate(**issue) for issue in raw_issues]
        created = await create_pending_issues(issues)
        total_created += created
        logger.info(f"Created {created} PENDING issues from {repo}")

    return total_created


async def run_fetch(repo: Optional[str] = None, limit: int = 100) -> dict:
    """Fetch phase: get detailed data for PENDING issues.

    Paginates in batches to work around Supabase's 1000-row cap.

    Args:
        repo: Optional repo filter.
        limit: Maximum records to process.

    Returns:
        dict: Counts of fetched and dropped issues.
    """
    batch_size = min(limit, 1000)
    counts = {"fetched": 0, "dropped": 0, "errored": 0}
    processed = 0

    while processed < limit:
        batch_limit = min(batch_size, limit - processed)
        pending = await get_issues_by_status(
            CrawlerStatus.PENDING, repo=repo, limit=batch_limit,
        )
        if not pending:
            break

        for record in pending:
            record_id = record["id"]
            record_repo = record["repo"]
            issue_number = record["issue_number"]

            try:
                details = await fetch_issue_details(record_repo, issue_number)

                # Apply filter
                passes, drop_reason = filter_issue(
                    state_reason=record.get("state_reason"),
                    has_merged_pr=details.get("has_merged_pr", False),
                    issue_labels=record.get("issue_labels", []),
                    issue_body=details.get("raw_issue_body", ""),
                    pr_additions=details.get("pr_additions", 0),
                )

                if not passes:
                    await update_to_dropped(record_id, drop_reason or "NOT_A_FIX")
                    counts["dropped"] += 1
                    logger.debug(
                        f"Dropped {record_repo}#{issue_number}: {drop_reason}"
                    )
                    continue

                fetched_data = CrawlerStateFetched(
                    has_merged_pr=details.get("has_merged_pr", False),
                    pr_number=details.get("pr_number"),
                    raw_issue_body=details.get("raw_issue_body"),
                    raw_comments=details.get("raw_comments", []),
                    raw_pr_body=details.get("raw_pr_body"),
                    raw_pr_diff_summary=details.get("raw_pr_diff_summary"),
                )
                await update_to_fetched(record_id, fetched_data)
                counts["fetched"] += 1

            except Exception as e:
                await update_to_error(record_id, str(e))
                counts["errored"] += 1
                logger.error(f"Error fetching {record_repo}#{issue_number}: {e}")

        processed += len(pending)
        logger.info(
            f"Fetch batch done ({processed} processed so far): "
            f"{counts['fetched']} fetched, {counts['dropped']} dropped"
        )

    logger.info(
        f"Fetch complete: {counts['fetched']} fetched, "
        f"{counts['dropped']} dropped, {counts['errored']} errored"
    )
    return counts


async def run_extract(repo: Optional[str] = None, limit: int = 100) -> dict:
    """Extract phase: LLM extraction for FETCHED issues.

    Paginates in batches to work around Supabase's 1000-row cap.

    Args:
        repo: Optional repo filter.
        limit: Maximum records to process.

    Returns:
        dict: Counts of extracted and dropped issues.
    """
    batch_size = min(limit, 1000)
    counts = {"extracted": 0, "dropped": 0, "errored": 0}
    processed = 0

    while processed < limit:
        batch_limit = min(batch_size, limit - processed)
        fetched = await get_issues_by_status(
            CrawlerStatus.FETCHED, repo=repo, limit=batch_limit,
        )
        if not fetched:
            break

        for record in fetched:
            record_id = record["id"]
            record_repo = record["repo"]
            issue_number = record["issue_number"]

            try:
                # Extract structured data
                extraction = await extract_issue_data(
                    issue_title=record.get("issue_title", ""),
                    issue_body=record.get("raw_issue_body"),
                    comments=record.get("raw_comments", []),
                    pr_body=record.get("raw_pr_body"),
                    pr_diff_summary=record.get("raw_pr_diff_summary"),
                )

                if not extraction.success:
                    await update_to_dropped(record_id, "EXTRACTION_FAILED")
                    counts["dropped"] += 1
                    logger.debug(
                        f"Extraction failed for {record_repo}#{issue_number}: "
                        f"{extraction.error}"
                    )
                    continue

                # Score quality
                quality = await score_quality(
                    error_message=extraction.error_message,
                    root_cause=extraction.root_cause,
                    fix_summary=extraction.fix_summary,
                    language=extraction.language,
                    framework=extraction.framework,
                )

                extracted_data = CrawlerStateExtracted(
                    extracted_error=extraction.error_message,
                    extracted_root_cause=extraction.root_cause,
                    extracted_fix_summary=extraction.fix_summary,
                    extracted_fix_steps=extraction.fix_steps,
                    extracted_language=extraction.language,
                    extracted_framework=extraction.framework,
                    extraction_confidence=extraction.confidence,
                    quality_score=quality,
                )
                await update_to_extracted(record_id, extracted_data)
                counts["extracted"] += 1

            except Exception as e:
                await update_to_error(record_id, str(e))
                counts["errored"] += 1
                logger.error(f"Error extracting {record_repo}#{issue_number}: {e}")

        processed += len(fetched)
        logger.info(
            f"Extract batch done ({processed} processed so far): "
            f"{counts['extracted']} extracted, {counts['dropped']} dropped"
        )

    logger.info(
        f"Extract complete: {counts['extracted']} extracted, "
        f"{counts['dropped']} dropped, {counts['errored']} errored"
    )
    return counts


async def run_submit(
    dry_run: bool = False,
    quality_threshold: float = 0.6,
) -> dict:
    """Submit phase: submit EXTRACTED issues to GIM.

    Args:
        dry_run: If True, don't actually submit.
        quality_threshold: Minimum quality score for submission.

    Returns:
        dict: Counts of submitted, dropped, and errored issues.
    """
    return await process_extracted_issues(
        limit=100,
        dry_run=dry_run,
        quality_threshold=quality_threshold,
    )


async def run_status_report() -> None:
    """Print pipeline status counts."""
    stats = await get_stats()
    total = sum(stats.values())

    print("\n=== GitHub Crawler Status Report ===")
    print(f"Total records: {total}")
    for status, count in sorted(stats.items()):
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {status:12s}: {count:5d} ({pct:.1f}%)")
    print("===================================\n")


async def run_retry_errors() -> dict:
    """Retry ERROR state issues (up to 3 retries).

    Returns:
        dict: Counts of retried issues.
    """
    retryable = await get_retryable_errors(max_retries=3)
    logger.info(f"Found {len(retryable)} retryable errors")

    # Reset them back to their previous meaningful status for reprocessing
    # For simplicity, we reset to PENDING so they go through the full pipeline
    counts = {"retried": 0, "skipped": 0}
    for record in retryable:
        try:
            await update_record(
                table="crawler_state",
                record_id=record["id"],
                data={
                    "status": CrawlerStatus.PENDING.value,
                    "last_error": None,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            counts["retried"] += 1
        except Exception as e:
            logger.error(f"Failed to retry {record['id']}: {e}")
            counts["skipped"] += 1

    logger.info(
        f"Retry complete: {counts['retried']} reset to PENDING, "
        f"{counts['skipped']} skipped"
    )
    return counts


async def run_revisit_dropped(
    days_threshold: int = 5,
    limit: int = 100,
) -> dict:
    """Revisit dropped issues to check if they've been resolved on GitHub.

    For each dropped issue older than the threshold:
    1. Re-fetch from GitHub to get current state
    2. Re-apply filter logic
    3. If passes: reset to PENDING for reprocessing through pipeline
    4. If still fails: update last_revisited_at to now

    Args:
        days_threshold: Number of days since last revisit before checking again.
            Must be at least 1.
        limit: Maximum issues to revisit per run. Must be at least 1.

    Returns:
        dict: Counts of reset, still_dropped, and errored issues.

    Raises:
        ValueError: If days_threshold or limit is less than 1.
    """
    if days_threshold < 1:
        raise ValueError("days_threshold must be at least 1")
    if limit < 1:
        raise ValueError("limit must be at least 1")

    dropped = await get_dropped_issues_for_revisit(
        days_threshold=days_threshold,
        limit=limit,
    )
    logger.info(f"Revisiting {len(dropped)} dropped issues...")

    counts = {"reset": 0, "still_dropped": 0, "errored": 0}

    for record in dropped:
        record_id = record["id"]
        repo = record["repo"]
        issue_number = record["issue_number"]

        try:
            # Re-fetch issue details from GitHub
            details = await fetch_issue_details(repo, issue_number)

            # Re-apply filter logic
            passes, drop_reason = filter_issue(
                state_reason=record.get("state_reason"),
                has_merged_pr=details.get("has_merged_pr", False),
                issue_labels=record.get("issue_labels", []),
                issue_body=details.get("raw_issue_body", ""),
                pr_additions=details.get("pr_additions", 0),
            )

            if passes:
                # Issue now qualifies - reset to PENDING for full pipeline
                await reset_dropped_to_pending(record_id)
                counts["reset"] += 1
                logger.info(f"Reset {repo}#{issue_number} to PENDING (now qualifies)")
            else:
                # Still doesn't qualify - update last_revisited_at
                await update_last_revisited_at(record_id)
                counts["still_dropped"] += 1
                logger.debug(
                    f"Still dropped {repo}#{issue_number}: {drop_reason}"
                )

        except Exception as e:
            # Don't fail the whole run for individual errors
            counts["errored"] += 1
            logger.error(f"Error revisiting {repo}#{issue_number}: {e}")
            try:
                await update_last_revisited_at(record_id)
            except Exception as update_err:
                logger.warning(
                    f"Failed to update revisit timestamp for {record_id}: {update_err}"
                )

    logger.info(
        f"Revisit complete: {counts['reset']} reset to PENDING, "
        f"{counts['still_dropped']} still dropped, {counts['errored']} errored"
    )
    return counts


async def main(args: argparse.Namespace) -> None:
    """Main entry point for the crawler CLI.

    Args:
        args: Parsed CLI arguments.
    """
    configure_logging()

    if args.status_report:
        await run_status_report()
        return

    if args.retry_errors:
        await run_retry_errors()
        return

    if args.revisit_dropped:
        await run_revisit_dropped(
            days_threshold=args.revisit_days,
            limit=args.limit,
        )
        await run_status_report()
        return

    repos = args.repos or DEFAULT_REPOS
    since = None
    if args.since:
        since = datetime.fromisoformat(args.since)
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)

    phase = args.phase

    if phase in ("discover", "full"):
        logger.info(f"=== DISCOVER phase (repos={repos}, max={args.max_issues}) ===")
        created = await run_discover(repos, since, args.max_issues)
        logger.info(f"Discovery complete: {created} new issues")

    if phase in ("fetch", "full"):
        logger.info("=== FETCH phase ===")
        await run_fetch(limit=args.limit)

    if phase in ("extract", "full"):
        logger.info("=== EXTRACT phase ===")
        await run_extract(limit=args.limit)

    if phase in ("submit", "full"):
        logger.info(
            f"=== SUBMIT phase (dry_run={args.dry_run}, "
            f"threshold={args.quality_threshold}) ==="
        )
        await run_submit(
            dry_run=args.dry_run,
            quality_threshold=args.quality_threshold,
        )

    await run_status_report()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="GitHub Issue Crawler for GIM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        default=None,
        help="Repos to crawl (default: popular repos)",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="ISO date, only issues closed after this",
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=50,
        help="Max issues per repo (default: 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and score but don't submit to GIM",
    )
    parser.add_argument(
        "--phase",
        choices=["discover", "fetch", "extract", "submit", "full"],
        default="full",
        help="Run specific phase (default: full)",
    )
    parser.add_argument(
        "--status-report",
        action="store_true",
        help="Print status counts and exit",
    )
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="Retry ERROR state issues",
    )
    parser.add_argument(
        "--revisit-dropped",
        action="store_true",
        help="Revisit DROPPED issues to check if they now qualify",
    )
    parser.add_argument(
        "--revisit-days",
        type=int,
        default=5,
        help="Days threshold for revisiting dropped issues (default: 5)",
    )
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=0.6,
        help="Quality score threshold (default: 0.6)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max records per phase (default: 100)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))
