"""Issue resolver for mapping child issue IDs to their master issues.

Provides a shared function to resolve any issue ID (master or child) to
its master issue, enabling fix bundles and detail pages to work with
either type of issue ID.
"""

from typing import Any, Dict, Optional, Tuple

from src.db.supabase_client import get_record
from src.logging_config import get_logger

logger = get_logger("db.issue_resolver")


async def resolve_issue_id(
    issue_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], bool]:
    """Resolve an issue ID to its master issue, handling child->master lookup.

    Tries the master_issues table first (common path, 1 query).
    If not found, tries child_issues, extracts master_issue_id, and fetches the master.

    Args:
        issue_id: UUID string that could be a master or child issue ID.

    Returns:
        Tuple of (master_issue, child_issue, is_child):
            - master_issue: The master issue record, or None if not found.
            - child_issue: The child issue record if the ID was a child, else None.
            - is_child: True if the input ID was a child issue.
    """
    # Try master_issues first (most common path)
    master = await get_record(table="master_issues", record_id=issue_id)
    if master:
        logger.debug(f"Resolved {issue_id} as master issue")
        return master, None, False

    # Not a master — try child_issues
    child = await get_record(table="child_issues", record_id=issue_id)
    if not child:
        logger.debug(f"Issue {issue_id} not found in master or child tables")
        return None, None, False

    # Found a child — fetch its master
    master_issue_id = child.get("master_issue_id")
    if not master_issue_id:
        logger.warning(f"Child issue {issue_id} has no master_issue_id")
        return None, child, True

    master = await get_record(table="master_issues", record_id=master_issue_id)
    if not master:
        logger.warning(
            f"Child issue {issue_id} references master {master_issue_id} which does not exist"
        )
        return None, child, True

    logger.debug(f"Resolved {issue_id} as child of master {master_issue_id}")
    return master, child, True
