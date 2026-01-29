"""Migrate Qdrant collection from 3 named vectors to 1 combined vector.

Reads all master_issues from Supabase, drops the old Qdrant collection,
recreates it with scalar quantization, generates combined embeddings,
and upserts the new single-vector points.

Usage:
    cd gim/
    python -m scripts.migrate_vectors          # run migration
    python -m scripts.migrate_vectors --dry-run # preview without writing
"""

import argparse
import asyncio
import logging
import sys
import time

from src.config import get_settings
from src.db.qdrant_client import (
    COLLECTION_NAME,
    ensure_collection_exists,
    get_qdrant_client,
    upsert_issue_vectors,
)
from src.db.supabase_client import query_records
from src.services.embedding_service import generate_combined_embedding


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("migrate_vectors")


async def fetch_all_issues() -> list[dict]:
    """Fetch all master_issues from Supabase with their fix summaries.

    Returns:
        list[dict]: Issues with canonical_error, root_cause, and fix_summary.
    """
    logger.info("Fetching master_issues from Supabase...")
    issues = await query_records(
        table="master_issues",
        select="id,canonical_error,root_cause,root_cause_category,model_provider",
        limit=10000,
    )
    logger.info(f"Found {len(issues)} master_issues")

    # Fetch fix_bundle summary for each issue
    for issue in issues:
        bundles = await query_records(
            table="fix_bundles",
            filters={"issue_id": issue["id"]},
            select="summary",
            order_by="confidence_score",
            ascending=False,
            limit=1,
        )
        issue["fix_summary"] = bundles[0]["summary"] if bundles else ""

    return issues


def drop_collection() -> None:
    """Drop the existing Qdrant collection."""
    client = get_qdrant_client()
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if COLLECTION_NAME in collection_names:
        logger.info(f"Dropping collection '{COLLECTION_NAME}'...")
        client.delete_collection(collection_name=COLLECTION_NAME)
        logger.info("Collection dropped")
    else:
        logger.info(f"Collection '{COLLECTION_NAME}' does not exist, nothing to drop")


async def migrate(dry_run: bool = False) -> None:
    """Run the full migration.

    Args:
        dry_run: If True, fetches and logs but does not write to Qdrant.
    """
    settings = get_settings()
    logger.info(
        f"Migration config: collection={COLLECTION_NAME}, "
        f"embedding_model={settings.embedding_model}, "
        f"dimensions={settings.embedding_dimensions}"
    )

    # 1. Fetch all issues from Supabase
    issues = await fetch_all_issues()
    if not issues:
        logger.info("No issues to migrate. Done.")
        return

    if dry_run:
        logger.info("[DRY RUN] Would process the following issues:")
        for issue in issues:
            error_preview = (issue.get("canonical_error") or "")[:80]
            logger.info(f"  - {issue['id']}: {error_preview}...")
        logger.info(f"[DRY RUN] Would drop and recreate '{COLLECTION_NAME}', "
                     f"then embed and upsert {len(issues)} points. Exiting.")
        return

    # 2. Drop old collection
    drop_collection()

    # 3. Recreate with new schema (single vector + scalar quantization)
    logger.info("Recreating collection with new schema...")
    await ensure_collection_exists()
    logger.info("Collection recreated")

    # 4. Generate combined embeddings and upsert
    success_count = 0
    error_count = 0
    start = time.monotonic()

    for i, issue in enumerate(issues, 1):
        issue_id = issue["id"]
        canonical_error = issue.get("canonical_error") or ""
        root_cause = issue.get("root_cause") or ""
        fix_summary = issue.get("fix_summary") or ""

        try:
            embedding = await generate_combined_embedding(
                error_message=canonical_error,
                root_cause=root_cause,
                fix_summary=fix_summary,
            )

            await upsert_issue_vectors(
                issue_id=issue_id,
                vector=embedding,
                payload={
                    "issue_id": issue_id,
                    "root_cause_category": issue.get("root_cause_category"),
                    "model_provider": issue.get("model_provider"),
                    "status": "active",
                },
            )
            success_count += 1
            logger.info(f"[{i}/{len(issues)}] Upserted {issue_id}")
        except Exception as e:
            error_count += 1
            logger.error(f"[{i}/{len(issues)}] Failed {issue_id}: {e}")

    elapsed = time.monotonic() - start
    logger.info(
        f"Migration complete: {success_count} succeeded, {error_count} failed "
        f"({elapsed:.1f}s)"
    )
    if error_count > 0:
        sys.exit(1)


def main() -> None:
    """Parse args and run migration."""
    parser = argparse.ArgumentParser(
        description="Migrate Qdrant collection from 3 named vectors to 1 combined vector."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would happen without writing to Qdrant.",
    )
    args = parser.parse_args()

    asyncio.run(migrate(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
