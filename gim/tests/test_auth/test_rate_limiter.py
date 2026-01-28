"""Tests for rate limiter service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.auth.rate_limiter import (
    RATE_LIMITED_OPERATIONS,
    UNLIMITED_OPERATIONS,
    RateLimitExceeded,
    RateLimitInfo,
    RateLimiter,
)


class TestRateLimitInfo:
    """Tests for RateLimitInfo class."""

    def test_to_headers(self) -> None:
        """Test converting rate limit info to headers."""
        reset_time = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        info = RateLimitInfo(
            limit=100,
            remaining=75,
            reset_at=reset_time,
        )

        headers = info.to_headers()

        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "75"
        assert headers["X-RateLimit-Reset"] == str(int(reset_time.timestamp()))


class TestRateLimitExceeded:
    """Tests for RateLimitExceeded exception."""

    def test_exception_attributes(self) -> None:
        """Test exception contains expected attributes."""
        reset_time = datetime.now(timezone.utc)
        exc = RateLimitExceeded(
            operation="gim_search_issues",
            limit=100,
            used=100,
            reset_at=reset_time,
        )

        assert exc.operation == "gim_search_issues"
        assert exc.limit == 100
        assert exc.used == 100
        assert exc.remaining == 0
        assert exc.reset_at == reset_time

    def test_exception_message(self) -> None:
        """Test exception has informative message."""
        reset_time = datetime.now(timezone.utc)
        exc = RateLimitExceeded(
            operation="gim_search_issues",
            limit=100,
            used=100,
            reset_at=reset_time,
        )

        assert "gim_search_issues" in str(exc)
        assert "100/100" in str(exc)


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @pytest.fixture
    def rate_limiter(self) -> RateLimiter:
        """Create a rate limiter instance."""
        return RateLimiter()

    @pytest.mark.asyncio
    async def test_unlimited_operations_always_pass(
        self,
        rate_limiter: RateLimiter,
    ) -> None:
        """Test that unlimited operations always pass rate limiting."""
        identity_id = uuid4()

        for operation in UNLIMITED_OPERATIONS:
            with patch(
                "src.auth.rate_limiter.get_record",
                new_callable=AsyncMock,
            ) as mock_get:
                mock_get.return_value = {
                    "daily_search_limit": 0,
                    "daily_search_used": 1000,
                    "daily_reset_at": datetime.now(timezone.utc).isoformat(),
                }

                info = await rate_limiter.check_rate_limit(identity_id, operation)

                assert info.limit == -1  # Unlimited
                assert info.remaining == -1

    @pytest.mark.asyncio
    async def test_rate_limited_operations_checked(
        self,
        rate_limiter: RateLimiter,
    ) -> None:
        """Test that rate-limited operations are checked."""
        identity_id = uuid4()
        reset_time = datetime.now(timezone.utc) + timedelta(hours=24)

        for operation in RATE_LIMITED_OPERATIONS:
            with patch(
                "src.auth.rate_limiter.get_record",
                new_callable=AsyncMock,
            ) as mock_get:
                mock_get.return_value = {
                    "daily_search_limit": 100,
                    "daily_search_used": 50,
                    "daily_reset_at": reset_time.isoformat(),
                }

                info = await rate_limiter.check_rate_limit(identity_id, operation)

                assert info.limit == 100
                assert info.remaining == 50

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_raises_exception(
        self,
        rate_limiter: RateLimiter,
    ) -> None:
        """Test that exceeding rate limit raises exception."""
        identity_id = uuid4()
        reset_time = datetime.now(timezone.utc) + timedelta(hours=24)

        with patch(
            "src.auth.rate_limiter.get_record",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = {
                "daily_search_limit": 100,
                "daily_search_used": 100,
                "daily_reset_at": reset_time.isoformat(),
            }

            with pytest.raises(RateLimitExceeded) as exc_info:
                await rate_limiter.check_rate_limit(
                    identity_id,
                    "gim_search_issues",
                )

            assert exc_info.value.limit == 100
            assert exc_info.value.used == 100

    @pytest.mark.asyncio
    async def test_consume_increments_usage(
        self,
        rate_limiter: RateLimiter,
    ) -> None:
        """Test that consume_rate_limit increments usage counter."""
        identity_id = uuid4()
        reset_time = datetime.now(timezone.utc) + timedelta(hours=24)

        with (
            patch(
                "src.auth.rate_limiter.get_record",
                new_callable=AsyncMock,
            ) as mock_get,
            patch(
                "src.auth.rate_limiter.update_record",
                new_callable=AsyncMock,
            ) as mock_update,
        ):
            mock_get.return_value = {
                "daily_search_limit": 100,
                "daily_search_used": 50,
                "daily_reset_at": reset_time.isoformat(),
                "total_searches": 500,
            }

            info = await rate_limiter.consume_rate_limit(
                identity_id,
                "gim_search_issues",
            )

            assert info.remaining == 49  # 100 - 51
            # Should have updated daily_search_used
            mock_update.assert_called()

    @pytest.mark.asyncio
    async def test_consume_unlimited_does_not_update(
        self,
        rate_limiter: RateLimiter,
    ) -> None:
        """Test that consuming unlimited operations doesn't update database."""
        identity_id = uuid4()

        with patch(
            "src.auth.rate_limiter.update_record",
            new_callable=AsyncMock,
        ) as mock_update:
            info = await rate_limiter.consume_rate_limit(
                identity_id,
                "gim_submit_issue",
            )

            assert info.limit == -1
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_daily_reset_resets_counters(
        self,
        rate_limiter: RateLimiter,
    ) -> None:
        """Test that daily reset clears usage counters."""
        identity_id = uuid4()
        # Set reset time to past
        past_reset = datetime.now(timezone.utc) - timedelta(hours=1)

        with (
            patch(
                "src.auth.rate_limiter.get_record",
                new_callable=AsyncMock,
            ) as mock_get,
            patch(
                "src.auth.rate_limiter.update_record",
                new_callable=AsyncMock,
            ) as mock_update,
        ):
            mock_get.return_value = {
                "daily_search_limit": 100,
                "daily_search_used": 100,  # Would normally be exceeded
                "daily_reset_at": past_reset.isoformat(),
            }

            # Should not raise because counters should reset
            info = await rate_limiter.check_rate_limit(
                identity_id,
                "gim_search_issues",
            )

            # Should have reset to 0
            assert info.remaining == 100
            # Should have called update to reset
            mock_update.assert_called()

    @pytest.mark.asyncio
    async def test_identity_not_found_raises_error(
        self,
        rate_limiter: RateLimiter,
    ) -> None:
        """Test that missing identity raises ValueError."""
        identity_id = uuid4()

        with patch(
            "src.auth.rate_limiter.get_record",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = None

            with pytest.raises(ValueError, match="Identity not found"):
                await rate_limiter.check_rate_limit(
                    identity_id,
                    "gim_search_issues",
                )


class TestOperationSets:
    """Tests for operation set constants."""

    def test_rate_limited_operations(self) -> None:
        """Test rate limited operations set."""
        assert "gim_search_issues" in RATE_LIMITED_OPERATIONS
        assert "gim_get_fix_bundle" in RATE_LIMITED_OPERATIONS

    def test_unlimited_operations(self) -> None:
        """Test unlimited operations set."""
        assert "gim_submit_issue" in UNLIMITED_OPERATIONS
        assert "gim_confirm_fix" in UNLIMITED_OPERATIONS
        assert "gim_report_usage" in UNLIMITED_OPERATIONS

    def test_no_overlap(self) -> None:
        """Test that rate limited and unlimited sets don't overlap."""
        assert RATE_LIMITED_OPERATIONS.isdisjoint(UNLIMITED_OPERATIONS)
