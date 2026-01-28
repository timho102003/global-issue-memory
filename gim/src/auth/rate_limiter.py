"""Rate limiting service for GIM operations.

This module implements per-operation rate limiting based on GIM identity.
Search and get_fix_bundle operations are limited; submit, confirm, and report are unlimited.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from src.auth.models import GIMIdentity
from src.db.supabase_client import get_record, get_supabase_client, update_record

logger = logging.getLogger(__name__)

TABLE_NAME = "gim_identities"

# Operations that are rate-limited
RATE_LIMITED_OPERATIONS = frozenset({"gim_search_issues", "gim_get_fix_bundle"})

# Operations that are unlimited
UNLIMITED_OPERATIONS = frozenset({
    "gim_submit_issue",
    "gim_confirm_fix",
    "gim_report_usage",
})


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        operation: str,
        limit: int,
        used: int,
        reset_at: datetime,
    ) -> None:
        """Initialize rate limit exceeded exception.

        Args:
            operation: The operation that was rate limited.
            limit: The daily limit.
            used: Number of operations used.
            reset_at: When the limit resets.
        """
        self.operation = operation
        self.limit = limit
        self.used = used
        self.reset_at = reset_at
        self.remaining = max(0, limit - used)
        super().__init__(
            f"Rate limit exceeded for {operation}: {used}/{limit} "
            f"(resets at {reset_at.isoformat()})"
        )


class RateLimitInfo:
    """Rate limit information for response headers."""

    def __init__(
        self,
        limit: int,
        remaining: int,
        reset_at: datetime,
    ) -> None:
        """Initialize rate limit info.

        Args:
            limit: The daily limit.
            remaining: Remaining operations.
            reset_at: When the limit resets.
        """
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at

    def to_headers(self) -> dict[str, str]:
        """Convert to HTTP headers.

        Returns:
            dict: Rate limit headers.
        """
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_at.timestamp())),
        }


class RateLimiter:
    """Rate limiter for GIM operations.

    Implements per-GIM-ID daily rate limits for search operations.
    Submit, confirm, and report operations are unlimited.
    """

    async def check_rate_limit(
        self,
        identity_id: UUID,
        operation: str,
    ) -> RateLimitInfo:
        """Check if operation is allowed under rate limits.

        Args:
            identity_id: The GIM identity ID.
            operation: The operation being performed.

        Returns:
            RateLimitInfo: Rate limit information.

        Raises:
            RateLimitExceeded: If the rate limit is exceeded.
        """
        # Unlimited operations always pass
        if operation in UNLIMITED_OPERATIONS:
            return RateLimitInfo(
                limit=-1,  # -1 indicates unlimited
                remaining=-1,
                reset_at=datetime.now(timezone.utc),
            )

        # Rate-limited operations need checking
        if operation not in RATE_LIMITED_OPERATIONS:
            logger.warning(f"Unknown operation for rate limiting: {operation}")
            # Default to allowing unknown operations
            return RateLimitInfo(
                limit=-1,
                remaining=-1,
                reset_at=datetime.now(timezone.utc),
            )

        # Get current identity state
        record = await get_record(TABLE_NAME, str(identity_id))
        if not record:
            raise ValueError(f"Identity not found: {identity_id}")

        # Check if daily reset is needed
        now = datetime.now(timezone.utc)
        reset_at_str = record.get("daily_reset_at")
        if reset_at_str:
            reset_at = datetime.fromisoformat(reset_at_str)
            if reset_at.tzinfo is None:
                reset_at = reset_at.replace(tzinfo=timezone.utc)
        else:
            # No reset time set, initialize it
            reset_at = now

        daily_limit = record.get("daily_search_limit", 100)
        daily_used = record.get("daily_search_used", 0)

        # Reset if past reset time
        if now >= reset_at:
            daily_used = 0
            reset_at = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            # Add 24 hours for next reset
            from datetime import timedelta
            reset_at = reset_at + timedelta(days=1)

            await update_record(
                TABLE_NAME,
                str(identity_id),
                {
                    "daily_search_used": 0,
                    "daily_reset_at": reset_at.isoformat(),
                },
            )
            logger.info(f"Reset daily rate limits for identity {identity_id}")

        remaining = max(0, daily_limit - daily_used)

        # Check if limit exceeded
        if daily_used >= daily_limit:
            raise RateLimitExceeded(
                operation=operation,
                limit=daily_limit,
                used=daily_used,
                reset_at=reset_at,
            )

        return RateLimitInfo(
            limit=daily_limit,
            remaining=remaining,
            reset_at=reset_at,
        )

    async def consume_rate_limit(
        self,
        identity_id: UUID,
        operation: str,
    ) -> RateLimitInfo:
        """Consume one unit of rate limit for an operation.

        Uses atomic database operations to prevent race conditions.

        Args:
            identity_id: The GIM identity ID.
            operation: The operation being performed.

        Returns:
            RateLimitInfo: Updated rate limit information.

        Raises:
            RateLimitExceeded: If the rate limit is exceeded.
        """
        # Unlimited operations bypass rate limiting
        if operation in UNLIMITED_OPERATIONS:
            return RateLimitInfo(
                limit=-1,
                remaining=-1,
                reset_at=datetime.now(timezone.utc),
            )

        # For rate-limited operations, use atomic increment with limit check
        client = get_supabase_client()

        # First check if we need to reset (if past reset time)
        record = await get_record(TABLE_NAME, str(identity_id))
        if not record:
            raise ValueError(f"Identity not found: {identity_id}")

        now = datetime.now(timezone.utc)
        reset_at_str = record.get("daily_reset_at")
        daily_limit = record.get("daily_search_limit", 100)

        if reset_at_str:
            reset_at = datetime.fromisoformat(reset_at_str)
            if reset_at.tzinfo is None:
                reset_at = reset_at.replace(tzinfo=timezone.utc)
        else:
            reset_at = now

        # Reset counters if past reset time
        if now >= reset_at:
            new_reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0)
            new_reset_at = new_reset_at + timedelta(days=1)
            await update_record(
                TABLE_NAME,
                str(identity_id),
                {
                    "daily_search_used": 0,
                    "daily_reset_at": new_reset_at.isoformat(),
                },
            )
            reset_at = new_reset_at

        # Re-fetch to get current state after potential reset
        record = await get_record(TABLE_NAME, str(identity_id))
        daily_used = record.get("daily_search_used", 0)

        # Check limit before incrementing
        if daily_used >= daily_limit:
            raise RateLimitExceeded(
                operation=operation,
                limit=daily_limit,
                used=daily_used,
                reset_at=reset_at,
            )

        # Atomic increment using optimistic locking with retry
        # This prevents race conditions where two requests pass the check
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use Supabase's atomic update capability with optimistic lock
                result = client.table(TABLE_NAME).update({
                    "daily_search_used": daily_used + 1,
                }).eq("id", str(identity_id)).eq(
                    "daily_search_used", daily_used  # Optimistic lock
                ).execute()

                if result.data:
                    # Success - update was applied
                    break

                # Another request incremented first, re-fetch and retry
                record = await get_record(TABLE_NAME, str(identity_id))
                if not record:
                    raise ValueError(f"Identity not found: {identity_id}")

                daily_used = record.get("daily_search_used", 0)

                # Re-check limit before retrying
                if daily_used >= daily_limit:
                    raise RateLimitExceeded(
                        operation=operation,
                        limit=daily_limit,
                        used=daily_used,
                        reset_at=reset_at,
                    )

                if attempt == max_retries - 1:
                    logger.warning(
                        f"Rate limit optimistic lock failed after {max_retries} attempts"
                    )

            except RateLimitExceeded:
                raise
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.warning(f"Atomic rate limit update failed: {e}")
                    # Fall back to simple update on last attempt
                    await update_record(
                        TABLE_NAME,
                        str(identity_id),
                        {"daily_search_used": daily_used + 1},
                    )

        new_used = daily_used + 1

        # Also increment lifetime stats (non-critical, can be racy)
        stat_field = self._get_stat_field(operation)
        if stat_field:
            total = record.get(stat_field, 0)
            await update_record(
                TABLE_NAME,
                str(identity_id),
                {stat_field: total + 1},
            )

        logger.debug(
            f"Consumed rate limit for {operation}: {new_used}/{daily_limit}"
        )

        return RateLimitInfo(
            limit=daily_limit,
            remaining=max(0, daily_limit - new_used),
            reset_at=reset_at,
        )

    def _get_stat_field(self, operation: str) -> Optional[str]:
        """Get the stat field name for an operation.

        Args:
            operation: The operation name.

        Returns:
            str: The stat field name, or None if not tracked.
        """
        mapping = {
            "gim_search_issues": "total_searches",
            "gim_get_fix_bundle": "total_searches",  # Counted together
            "gim_submit_issue": "total_submissions",
            "gim_confirm_fix": "total_confirmations",
            "gim_report_usage": "total_reports",
        }
        return mapping.get(operation)

    async def get_rate_limit_status(
        self,
        identity_id: UUID,
    ) -> RateLimitInfo:
        """Get current rate limit status without consuming.

        Args:
            identity_id: The GIM identity ID.

        Returns:
            RateLimitInfo: Current rate limit information.
        """
        return await self.check_rate_limit(identity_id, "gim_search_issues")


# Module-level singleton
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter singleton.

    Returns:
        RateLimiter: The rate limiter instance.
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
