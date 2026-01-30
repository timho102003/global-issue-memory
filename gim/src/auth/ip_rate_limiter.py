"""IP-based rate limiter for sensitive endpoints.

Provides a sliding window rate limiter that tracks requests per IP address.
Designed for endpoints like GIM ID creation that are abuse targets.
"""

import time
import threading
from collections import defaultdict
from typing import Dict, List, Optional


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
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, ip: str) -> bool:
        """Check if a request from this IP is allowed.

        Records the request if allowed.

        Args:
            ip: The client IP address.

        Returns:
            bool: True if the request is allowed.
        """
        now = time.time()
        cutoff = now - self._window_seconds

        with self._lock:
            # Clean old entries
            self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

            if len(self._requests[ip]) >= self._max_requests:
                return False

            self._requests[ip].append(now)
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
            self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]
            return max(0, self._max_requests - len(self._requests[ip]))


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
