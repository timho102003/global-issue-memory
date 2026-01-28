"""Tests for centralized logging configuration."""

import asyncio
import logging
import pytest

from src.logging_config import (
    configure_logging,
    get_logger,
    set_request_context,
    get_request_context,
    clear_request_context,
    log_operation,
    RequestContextFilter,
)


class TestConfigureLogging:
    """Test cases for configure_logging function."""

    def test_configure_logging_default_level(self) -> None:
        """Test configure_logging with default level."""
        configure_logging()
        logger = logging.getLogger("gim")
        assert logger.level == logging.INFO

    def test_configure_logging_custom_level(self) -> None:
        """Test configure_logging with custom level."""
        configure_logging(level=logging.DEBUG)
        logger = logging.getLogger("gim")
        assert logger.level == logging.DEBUG

    def test_configure_logging_adds_handler(self) -> None:
        """Test configure_logging adds a handler."""
        configure_logging()
        logger = logging.getLogger("gim")
        assert len(logger.handlers) == 1


class TestGetLogger:
    """Test cases for get_logger function."""

    def test_get_logger_returns_logger(self) -> None:
        """Test get_logger returns a Logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_has_gim_prefix(self) -> None:
        """Test get_logger creates logger with gim prefix."""
        logger = get_logger("mymodule")
        assert logger.name == "gim.mymodule"

    def test_get_logger_nested_name(self) -> None:
        """Test get_logger with nested module name."""
        logger = get_logger("db.supabase")
        assert logger.name == "gim.db.supabase"


class TestRequestContext:
    """Test cases for request context functions."""

    def test_set_request_context_returns_id(self) -> None:
        """Test set_request_context returns the request ID."""
        request_id = set_request_context()
        assert isinstance(request_id, str)
        assert len(request_id) == 8

    def test_set_request_context_with_custom_id(self) -> None:
        """Test set_request_context with custom request ID."""
        request_id = set_request_context("custom-id")
        assert request_id == "custom-id"

    def test_get_request_context_returns_current_id(self) -> None:
        """Test get_request_context returns the current request ID."""
        set_request_context("test-123")
        assert get_request_context() == "test-123"

    def test_clear_request_context(self) -> None:
        """Test clear_request_context clears the context."""
        set_request_context("test-123")
        clear_request_context()
        assert get_request_context() is None

    def test_get_request_context_returns_none_initially(self) -> None:
        """Test get_request_context returns None when not set."""
        clear_request_context()
        assert get_request_context() is None


class TestRequestContextFilter:
    """Test cases for RequestContextFilter."""

    def test_filter_adds_request_id(self) -> None:
        """Test filter adds request_id to log record."""
        filter_instance = RequestContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        set_request_context("abc-123")
        result = filter_instance.filter(record)

        assert result is True
        assert hasattr(record, "request_id")
        assert record.request_id == "abc-123"

    def test_filter_uses_default_when_no_context(self) -> None:
        """Test filter uses default value when no context set."""
        clear_request_context()
        filter_instance = RequestContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)
        assert record.request_id == "no-request-id"


class TestLogOperationDecorator:
    """Test cases for log_operation decorator."""

    @pytest.mark.asyncio
    async def test_log_operation_async_success(self) -> None:
        """Test log_operation decorator with async function that succeeds."""
        @log_operation("test_operation")
        async def successful_operation() -> str:
            return "success"

        result = await successful_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_log_operation_async_raises(self) -> None:
        """Test log_operation decorator with async function that raises."""
        @log_operation("failing_operation")
        async def failing_operation() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_operation()

    def test_log_operation_sync_success(self) -> None:
        """Test log_operation decorator with sync function that succeeds."""
        @log_operation("sync_operation")
        def sync_operation() -> int:
            return 42

        result = sync_operation()
        assert result == 42

    def test_log_operation_sync_raises(self) -> None:
        """Test log_operation decorator with sync function that raises."""
        @log_operation("failing_sync")
        def failing_sync() -> None:
            raise RuntimeError("Sync error")

        with pytest.raises(RuntimeError):
            failing_sync()

    @pytest.mark.asyncio
    async def test_log_operation_preserves_function_name(self) -> None:
        """Test log_operation preserves function name."""
        @log_operation("named_op")
        async def my_function() -> None:
            pass

        assert my_function.__name__ == "my_function"

    @pytest.mark.asyncio
    async def test_log_operation_with_arguments(self) -> None:
        """Test log_operation with function arguments."""
        @log_operation("op_with_args")
        async def operation_with_args(a: int, b: str) -> str:
            return f"{a}-{b}"

        result = await operation_with_args(1, "test")
        assert result == "1-test"

    @pytest.mark.asyncio
    async def test_log_operation_with_kwargs(self) -> None:
        """Test log_operation with function keyword arguments."""
        @log_operation("op_with_kwargs")
        async def operation_with_kwargs(*, name: str, value: int) -> dict:
            return {"name": name, "value": value}

        result = await operation_with_kwargs(name="test", value=10)
        assert result == {"name": "test", "value": 10}
