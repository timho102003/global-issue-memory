"""IP-based rate limiter for sensitive endpoints.

Provides a sliding window rate limiter that tracks requests per IP address.
Designed for endpoints like GIM ID creation that are abuse targets.
"""

import time
import threading
from typing import Dict, List, Optional

from starlette.requests import Request


class IPRateLimiter:
    """In-memory IP-based sliding window rate limiter.

    Limits requests per IP address using a sliding window approach.
    Designed for endpoints like GIM ID creation that are abuse targets.
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 3600) -> None:
        """Initialize IP rate limiter.

        Args:
            max_requests: Maximum requests allowed per window.
            window_seconds: Window duration in seconds.
        """
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._cleanup_counter: int = 0

    def is_allowed(self, ip: str) -> bool:
        """Check if a request from this IP is allowed.

        Records the request if allowed. Periodically cleans up stale entries
        to prevent unbounded memory growth.

        Args:
            ip: The client IP address.

        Returns:
            bool: True if the request is allowed.
        """
        now = time.time()
        cutoff = now - self._window_seconds

        with self._lock:
            # Clean old entries for this IP
            timestamps = self._requests.get(ip, [])
            timestamps = [t for t in timestamps if t > cutoff]

            if len(timestamps) >= self._max_requests:
                self._requests[ip] = timestamps
                return False

            timestamps.append(now)
            self._requests[ip] = timestamps

            # Periodic cleanup of stale IPs to prevent memory growth
            self._cleanup_counter += 1
            if self._cleanup_counter >= 100:
                self._cleanup_counter = 0
                stale_ips = [
                    k for k, v in self._requests.items()
                    if not v or all(t <= cutoff for t in v)
                ]
                for k in stale_ips:
                    del self._requests[k]

            return True

    def get_remaining(self, ip: str) -> int:
        """Get remaining requests for an IP.

        Args:
            ip: The client IP address.

        Returns:
            int: Number of remaining requests in current window.
        """
        now = time.time()
        cutoff = now - self._window_seconds

        with self._lock:
            timestamps = [t for t in self._requests.get(ip, []) if t > cutoff]
            if timestamps:
                self._requests[ip] = timestamps
            elif ip in self._requests:
                del self._requests[ip]
            return max(0, self._max_requests - len(timestamps))


# Module-level singleton for GIM ID creation endpoint
_gim_id_limiter: Optional[IPRateLimiter] = None


def get_gim_id_rate_limiter() -> IPRateLimiter:
    """Get the GIM ID creation rate limiter singleton.

    Returns:
        IPRateLimiter: Rate limiter for GIM ID creation (5 req/hour).
    """
    global _gim_id_limiter
    if _gim_id_limiter is None:
        _gim_id_limiter = IPRateLimiter(max_requests=5, window_seconds=3600)
    return _gim_id_limiter


def get_client_ip(request: Request) -> str:
    """Extract the real client IP from the request.

    Checks headers in order of trust, but only when trust_proxy_headers
    is enabled in settings. This prevents IP spoofing when not behind
    a trusted reverse proxy like Cloudflare.

    Args:
        request: The Starlette request object.

    Returns:
        str: The client IP address, or "unknown" if unavailable.
    """
    from src.config import get_settings
    settings = get_settings()

    if settings.trust_proxy_headers:
        # Cloudflare real IP (most trusted when behind CF)
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip.strip()

        # Standard proxy header (first entry is original client)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

    # Direct connection
    if request.client:
        return request.client.host

    import logging
    logging.getLogger(__name__).warning(
        "Could not determine client IP from request; using shared 'unknown' bucket"
    )
    return "unknown"


_submit_issue_limiter: Optional[IPRateLimiter] = None


def get_submit_issue_rate_limiter() -> IPRateLimiter:
    """Get the submit issue rate limiter singleton.

    Reads limits from config settings.

    Returns:
        IPRateLimiter: Rate limiter for issue submissions.
    """
    global _submit_issue_limiter
    if _submit_issue_limiter is None:
        from src.config import get_settings
        settings = get_settings()
        _submit_issue_limiter = IPRateLimiter(
            max_requests=settings.ip_submit_max_requests,
            window_seconds=settings.ip_submit_window_seconds,
        )
    return _submit_issue_limiter
