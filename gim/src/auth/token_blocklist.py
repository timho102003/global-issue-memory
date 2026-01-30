"""In-memory token blocklist with TTL for revoked tokens.

This module provides a thread-safe blocklist that tracks revoked JWT tokens
until their natural expiration, preventing the blocklist from growing unbounded.
"""

import threading
import time
from typing import Dict, Optional


class TokenBlocklist:
    """In-memory blocklist for revoked tokens.

    Uses a TTL-based approach where entries expire after the token's
    original expiration time. This prevents the blocklist from growing
    unbounded.
    """

    def __init__(self) -> None:
        """Initialize the token blocklist."""
        self._blocked: Dict[str, float] = {}  # token_hash -> expiry_timestamp
        self._lock = threading.Lock()

    def add(self, token_hash: str, expires_at: float) -> None:
        """Add a token to the blocklist.

        Args:
            token_hash: Hash of the token to block.
            expires_at: Unix timestamp when the token naturally expires.
        """
        with self._lock:
            self._blocked[token_hash] = expires_at
            self._cleanup()

    def is_blocked(self, token_hash: str) -> bool:
        """Check if a token is blocked.

        Args:
            token_hash: Hash of the token to check.

        Returns:
            bool: True if the token is in the blocklist and not expired.
        """
        with self._lock:
            if token_hash not in self._blocked:
                return False
            if self._blocked[token_hash] < time.time():
                del self._blocked[token_hash]
                return False
            return True

    def _cleanup(self) -> None:
        """Remove expired entries from the blocklist.

        Must be called while holding self._lock.
        """
        now = time.time()
        expired = [k for k, v in self._blocked.items() if v < now]
        for k in expired:
            del self._blocked[k]


# Module-level singleton
_blocklist: Optional[TokenBlocklist] = None


def get_token_blocklist() -> TokenBlocklist:
    """Get the token blocklist singleton.

    Returns:
        TokenBlocklist: The token blocklist instance.
    """
    global _blocklist
    if _blocklist is None:
        _blocklist = TokenBlocklist()
    return _blocklist
