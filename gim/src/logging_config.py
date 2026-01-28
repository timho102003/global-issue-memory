"""Centralized logging configuration for GIM.

This module provides structured logging with request context tracking,
operation timing, and consistent log formatting across all GIM components.
"""

import functools
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Optional, TypeVar

# Context variable for request ID tracking
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Type variable for decorator
F = TypeVar("F", bound=Callable[..., Any])


class RequestContextFilter(logging.Filter):
    """Logging filter that adds request ID to log records.

    This filter enriches log records with the current request ID
    from the context variable, enabling request tracing across logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to log record.

        Args:
            record: The log record to enrich.

        Returns:
            bool: Always True to include the record.
        """
        record.request_id = _request_id.get() or "no-request-id"
        return True


def configure_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> None:
    """Configure logging for GIM with structured output.

    Sets up the root logger with a console handler, request context filter,
    and a consistent format for all log messages.

    Args:
        level: Logging level (default: INFO).
        format_string: Custom format string (optional).
    """
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "[%(request_id)s] | %(message)s"
        )

    # Create formatter
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())

    # Configure root logger for GIM
    gim_logger = logging.getLogger("gim")
    gim_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    gim_logger.handlers.clear()
    gim_logger.addHandler(console_handler)

    # Prevent propagation to root logger
    gim_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger with GIM prefix.

    Creates a logger under the 'gim' namespace for consistent
    log organization.

    Args:
        name: Logger name (will be prefixed with 'gim.').

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(f"gim.{name}")


def set_request_context(request_id: Optional[str] = None) -> str:
    """Set request ID for the current context.

    Creates a unique request ID if not provided and stores it
    in the context variable for log enrichment.

    Args:
        request_id: Optional request ID (generates UUID if not provided).

    Returns:
        str: The request ID being used.
    """
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    _request_id.set(request_id)
    return request_id


def get_request_context() -> Optional[str]:
    """Get current request ID from context.

    Returns:
        Optional[str]: Current request ID or None.
    """
    return _request_id.get()


def clear_request_context() -> None:
    """Clear the current request context."""
    _request_id.set(None)


def log_operation(
    name: str,
    log_args: bool = False,
    log_result: bool = False,
) -> Callable[[F], F]:
    """Decorator for logging operation timing and status.

    Wraps functions to automatically log start, completion, and errors
    with timing information.

    Args:
        name: Operation name for logging.
        log_args: Whether to log function arguments.
        log_result: Whether to log function result.

    Returns:
        Callable: Decorated function.

    Example:
        >>> @log_operation("fetch_user")
        ... async def get_user(user_id: str) -> dict:
        ...     return {"id": user_id}
    """
    def decorator(func: F) -> F:
        logger = get_logger(name)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            operation_id = str(uuid.uuid4())[:8]

            # Log start
            log_msg = f"Starting operation {name} (op_id={operation_id})"
            if log_args and (args or kwargs):
                log_msg += f" | args={args}, kwargs={kwargs}"
            logger.debug(log_msg)

            try:
                result = await func(*args, **kwargs)
                elapsed = (time.perf_counter() - start_time) * 1000

                # Log success
                log_msg = (
                    f"Completed operation {name} (op_id={operation_id}) "
                    f"in {elapsed:.2f}ms"
                )
                if log_result and result is not None:
                    log_msg += f" | result={result}"
                logger.debug(log_msg)

                return result

            except Exception as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"Failed operation {name} (op_id={operation_id}) "
                    f"after {elapsed:.2f}ms | error={type(e).__name__}: {e}"
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            operation_id = str(uuid.uuid4())[:8]

            # Log start
            log_msg = f"Starting operation {name} (op_id={operation_id})"
            if log_args and (args or kwargs):
                log_msg += f" | args={args}, kwargs={kwargs}"
            logger.debug(log_msg)

            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start_time) * 1000

                # Log success
                log_msg = (
                    f"Completed operation {name} (op_id={operation_id}) "
                    f"in {elapsed:.2f}ms"
                )
                if log_result and result is not None:
                    log_msg += f" | result={result}"
                logger.debug(log_msg)

                return result

            except Exception as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"Failed operation {name} (op_id={operation_id}) "
                    f"after {elapsed:.2f}ms | error={type(e).__name__}: {e}"
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    return decorator
