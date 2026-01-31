"""GitHub API integration for discovering and fetching resolved issues.

Uses PyGitHub to interact with the GitHub API. Since PyGitHub is synchronous,
all calls are wrapped in asyncio.to_thread() for async compatibility.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from github import Github
from github.GithubException import RateLimitExceededException
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository

from src.config import get_settings
from src.logging_config import get_logger

logger = get_logger("crawler.github_fetcher")

# Rate limit safety threshold
RATE_LIMIT_THRESHOLD = 100
MAX_COMMENTS = 20


def _get_github_client() -> Github:
    """Create a GitHub client using configured token.

    Returns:
        Github: Authenticated or unauthenticated GitHub client.
    """
    settings = get_settings()
    if settings.github_token:
        return Github(settings.github_token.get_secret_value())
    return Github()


def _rate_limit_guard(github: Github) -> None:
    """Check rate limits and sleep if necessary.

    Args:
        github: GitHub client instance.
    """
    rate_limit = github.get_rate_limit()
    remaining = rate_limit.rate.remaining
    reset_time = rate_limit.rate.reset

    if remaining < RATE_LIMIT_THRESHOLD:
        sleep_seconds = max(0, (reset_time - datetime.now(timezone.utc)).total_seconds()) + 5
        logger.warning(
            f"Rate limit low ({remaining} remaining). "
            f"Sleeping {sleep_seconds:.0f}s until reset."
        )
        time.sleep(sleep_seconds)


def _sync_discover_issues(
    repo_name: str,
    since: Optional[datetime],
    max_issues: int,
) -> List[Dict[str, Any]]:
    """Synchronous implementation of issue discovery.

    Args:
        repo_name: Repository in 'owner/name' format.
        since: Only issues closed after this date.
        max_issues: Maximum number of issues to return.

    Returns:
        List[Dict[str, Any]]: List of issue metadata dicts.
    """
    gh = _get_github_client()
    _rate_limit_guard(gh)

    repo = gh.get_repo(repo_name)
    issues = repo.get_issues(state="closed", sort="closed", direction="desc")

    results: List[Dict[str, Any]] = []
    checked = 0

    for issue in issues:
        if len(results) >= max_issues:
            break

        # Skip pull requests (GitHub API returns PRs as issues)
        if issue.pull_request is not None:
            continue

        # Filter by state_reason
        state_reason = getattr(issue, "state_reason", None)
        if state_reason != "completed":
            checked += 1
            if checked > max_issues * 5:
                break
            continue

        # Filter by since date (issues sorted by closed desc, so stop early)
        if since and issue.closed_at and issue.closed_at < since:
            break

        results.append({
            "repo": repo_name,
            "issue_number": issue.number,
            "github_issue_id": issue.id,
            "closed_at": issue.closed_at,
            "state_reason": state_reason,
            "issue_title": issue.title,
            "issue_labels": [label.name for label in issue.labels],
        })

        _rate_limit_guard(gh)

    logger.info(f"Discovered {len(results)} issues from {repo_name}")
    return results


async def discover_issues(
    repo_name: str,
    since: Optional[datetime] = None,
    max_issues: int = 50,
) -> List[Dict[str, Any]]:
    """Discover closed issues from a GitHub repository.

    Filters for issues with state_reason='completed' and returns
    basic metadata for pipeline processing.

    Args:
        repo_name: Repository in 'owner/name' format.
        since: Only return issues closed after this date.
        max_issues: Maximum number of issues to discover.

    Returns:
        List[Dict[str, Any]]: List of issue metadata dicts.
    """
    return await asyncio.to_thread(
        _sync_discover_issues, repo_name, since, max_issues
    )


def _find_linked_pr(
    repo: Repository,
    issue: Issue,
) -> Optional[PullRequest]:
    """Find a linked merged PR for an issue via timeline events.

    Args:
        repo: PyGitHub Repository object.
        issue: PyGitHub Issue object.

    Returns:
        Optional[PullRequest]: The linked merged PR, or None.
    """
    try:
        timeline = issue.get_timeline()
        for event in timeline:
            if event.event == "cross-referenced":
                source = getattr(event, "source", None)
                if source:
                    pr_info = getattr(source, "issue", None)
                    if pr_info and hasattr(pr_info, "pull_request"):
                        try:
                            pr = repo.get_pull(pr_info.number)
                            if pr.merged:
                                return pr
                        except Exception as e:
                            logger.debug(
                                f"Error fetching cross-referenced PR "
                                f"#{pr_info.number}: {e}"
                            )
                            continue
            elif event.event == "closed":
                commit_id = getattr(event, "commit_id", None)
                if commit_id:
                    # Try to find PR by commit
                    try:
                        commit = repo.get_commit(commit_id)
                        pulls = commit.get_pulls()
                        for pr in pulls:
                            if pr.merged:
                                return pr
                    except Exception as e:
                        logger.debug(
                            f"Error finding PR by commit {commit_id}: {e}"
                        )
    except Exception as e:
        logger.debug(f"Error finding linked PR: {e}")

    return None


def _get_pr_diff_summary(pr: PullRequest) -> str:
    """Get a summary of PR changes.

    Args:
        pr: PyGitHub PullRequest object.

    Returns:
        str: Summary of files changed, additions, and deletions.
    """
    try:
        files = pr.get_files()
        file_summaries = []
        total_additions = 0
        total_deletions = 0

        for f in files:
            file_summaries.append(
                f"{f.filename} (+{f.additions}/-{f.deletions})"
            )
            total_additions += f.additions
            total_deletions += f.deletions

        return (
            f"Total: +{total_additions}/-{total_deletions} "
            f"in {len(file_summaries)} files\n"
            + "\n".join(file_summaries[:20])  # Limit to 20 files
        )
    except Exception as e:
        logger.debug(f"Error getting PR diff summary: {e}")
        return ""


def _sync_fetch_issue_details(
    repo_name: str,
    issue_number: int,
) -> Dict[str, Any]:
    """Synchronous implementation of issue detail fetching.

    Args:
        repo_name: Repository in 'owner/name' format.
        issue_number: GitHub issue number.

    Returns:
        Dict[str, Any]: Issue details including body, comments, PR info.
    """
    gh = _get_github_client()
    _rate_limit_guard(gh)

    repo = gh.get_repo(repo_name)
    issue = repo.get_issue(issue_number)

    # Fetch comments (up to MAX_COMMENTS)
    comments = []
    for comment in issue.get_comments():
        if len(comments) >= MAX_COMMENTS:
            break
        comments.append({
            "author": comment.user.login if comment.user else "unknown",
            "body": comment.body or "",
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        })

    _rate_limit_guard(gh)

    # Find linked merged PR
    linked_pr = _find_linked_pr(repo, issue)

    result: Dict[str, Any] = {
        "raw_issue_body": issue.body or "",
        "raw_comments": comments,
        "has_merged_pr": linked_pr is not None,
        "pr_number": linked_pr.number if linked_pr else None,
        "raw_pr_body": linked_pr.body if linked_pr else None,
        "raw_pr_diff_summary": _get_pr_diff_summary(linked_pr) if linked_pr else None,
        "pr_additions": linked_pr.additions if linked_pr else 0,
    }

    return result


async def fetch_issue_details(
    repo_name: str,
    issue_number: int,
) -> Dict[str, Any]:
    """Fetch detailed information for a specific issue.

    Retrieves issue body, comments, linked PR info, and diff summary.

    Args:
        repo_name: Repository in 'owner/name' format.
        issue_number: GitHub issue number.

    Returns:
        Dict[str, Any]: Issue details dict with raw data.
    """
    return await asyncio.to_thread(
        _sync_fetch_issue_details, repo_name, issue_number
    )
