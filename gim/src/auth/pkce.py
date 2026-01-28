"""PKCE (Proof Key for Code Exchange) utilities for OAuth 2.1.

This module provides functions for generating and validating PKCE
code verifiers and challenges as per RFC 7636.
"""

import base64
import hashlib
import secrets
import string
from typing import Literal


# PKCE code verifier character set (unreserved URI characters)
PKCE_CHARSET = string.ascii_letters + string.digits + "-._~"


def generate_code_verifier(length: int = 64) -> str:
    """Generate a cryptographically random code verifier.

    Args:
        length: Length of the verifier (43-128 characters per RFC 7636).

    Returns:
        str: A random code verifier string.

    Raises:
        ValueError: If length is not between 43 and 128.
    """
    if length < 43 or length > 128:
        raise ValueError("Code verifier length must be between 43 and 128")

    return "".join(secrets.choice(PKCE_CHARSET) for _ in range(length))


def compute_code_challenge(
    code_verifier: str,
    method: Literal["S256"] = "S256",
) -> str:
    """Compute the code challenge from a code verifier.

    Args:
        code_verifier: The code verifier string.
        method: Challenge method (only "S256" supported per OAuth 2.1).

    Returns:
        str: The computed code challenge.

    Raises:
        ValueError: If method is not "S256".
    """
    if method == "S256":
        # SHA-256 hash, then base64url encode without padding
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    else:
        raise ValueError(f"Unsupported code challenge method: {method}. Only S256 is supported.")


def verify_code_challenge(
    code_verifier: str,
    code_challenge: str,
    method: str = "S256",
) -> bool:
    """Verify that a code verifier matches a code challenge.

    Args:
        code_verifier: The code verifier provided by the client.
        code_challenge: The code challenge stored during authorization.
        method: The challenge method used (only S256 supported).

    Returns:
        bool: True if the verifier matches the challenge, False otherwise.
    """
    if not code_verifier or not code_challenge:
        return False

    # Only S256 is supported per OAuth 2.1
    if method != "S256":
        return False

    try:
        computed_challenge = compute_code_challenge(code_verifier, "S256")
        return secrets.compare_digest(computed_challenge, code_challenge)
    except Exception:
        return False


def validate_code_verifier(code_verifier: str) -> bool:
    """Validate that a code verifier meets RFC 7636 requirements.

    Args:
        code_verifier: The code verifier to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not code_verifier:
        return False

    # Length must be 43-128 characters
    if len(code_verifier) < 43 or len(code_verifier) > 128:
        return False

    # Must only contain unreserved URI characters
    return all(c in PKCE_CHARSET for c in code_verifier)


def generate_authorization_code(length: int = 32) -> str:
    """Generate a cryptographically secure authorization code.

    Args:
        length: Length of the authorization code.

    Returns:
        str: A random authorization code string.
    """
    return secrets.token_urlsafe(length)
