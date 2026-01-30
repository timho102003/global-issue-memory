"""Secret detection module for sanitization pipeline."""

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from .patterns import SECRET_PATTERNS


class SecretAction(str, Enum):
    """Action to take when a secret is detected.

    Attributes:
        REMOVE: Remove the secret and replace with placeholder.
        REJECT: Reject the entire submission due to sensitive content.
    """

    REMOVE = "remove"
    REJECT = "reject"


@dataclass
class DetectedSecret:
    """A detected secret with its metadata.

    Attributes:
        pattern_name: Name of the pattern that matched.
        matched_text: The actual text that was matched.
        start_pos: Start position in the original text.
        end_pos: End position in the original text.
        confidence: Confidence score for this detection (0.0-1.0).
        action: Recommended action for this secret.
    """

    pattern_name: str
    matched_text: str
    start_pos: int
    end_pos: int
    confidence: float
    action: SecretAction


@dataclass
class SecretScanResult:
    """Result of scanning text for secrets.

    Attributes:
        secrets: List of detected secrets.
        sanitized_text: Text with secrets removed/replaced.
        remaining_risk: Estimated remaining risk (0.0-1.0).
        scan_confidence: Confidence in the scan completeness (0.0-1.0).
    """

    secrets: List[DetectedSecret] = field(default_factory=list)
    sanitized_text: str = ""
    remaining_risk: float = 0.0
    scan_confidence: float = 1.0


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of a string.

    Higher entropy indicates more randomness, which is characteristic
    of secrets, API keys, and encrypted data.

    Args:
        text: The text to analyze.

    Returns:
        float: Shannon entropy value (0.0 to ~4.7 for random ASCII).
    """
    if not text:
        return 0.0

    # Count character frequencies
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1

    # Calculate entropy
    length = len(text)
    entropy = 0.0
    for count in freq.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    return entropy


def detect_high_entropy_strings(
    text: str,
    min_length: int = 20,
    entropy_threshold: float = 4.0,
) -> List[DetectedSecret]:
    """Detect high-entropy strings that may be secrets.

    Args:
        text: The text to scan.
        min_length: Minimum length of strings to consider.
        entropy_threshold: Minimum entropy to flag as potential secret.

    Returns:
        List[DetectedSecret]: List of detected high-entropy strings.
    """
    secrets = []

    # Pattern to find potential secret-like strings
    # Matches alphanumeric strings with common secret characters
    pattern = re.compile(r'[A-Za-z0-9+/=_\-]{' + str(min_length) + r',}')

    for match in pattern.finditer(text):
        matched = match.group()
        entropy = calculate_entropy(matched)

        if entropy >= entropy_threshold:
            # Higher entropy = higher confidence it's a secret
            confidence = min((entropy - 3.0) / 2.0, 1.0)

            secrets.append(
                DetectedSecret(
                    pattern_name="high_entropy_string",
                    matched_text=matched,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=confidence,
                    action=SecretAction.REMOVE,
                )
            )

    return secrets


def detect_secrets(text: str) -> SecretScanResult:
    """Detect secrets in text using pattern matching and entropy analysis.

    This is the main entry point for secret detection. It combines:
    1. Known secret patterns (API keys, tokens, etc.)
    2. High-entropy string detection
    3. Context-aware analysis

    Args:
        text: The text to scan for secrets.

    Returns:
        SecretScanResult: Result containing detected secrets and sanitized text.
    """
    if not text:
        return SecretScanResult(
            sanitized_text="",
            scan_confidence=1.0,
            remaining_risk=0.0,
        )

    all_secrets: List[DetectedSecret] = []

    # Phase 1: Pattern-based detection
    for pattern_name, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            # For patterns with groups, use the group; otherwise use full match
            if match.groups():
                matched_text = match.group(1) if match.group(1) else match.group(0)
            else:
                matched_text = match.group(0)

            # All secrets are removed (sanitized), no rejection
            action = SecretAction.REMOVE

            # High confidence for known patterns
            confidence = 0.95

            all_secrets.append(
                DetectedSecret(
                    pattern_name=pattern_name,
                    matched_text=matched_text,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=confidence,
                    action=action,
                )
            )

    # Phase 2: High-entropy string detection
    entropy_secrets = detect_high_entropy_strings(text)

    # Filter out entropy detections that overlap with pattern detections
    pattern_ranges = [(s.start_pos, s.end_pos) for s in all_secrets]
    for secret in entropy_secrets:
        overlaps = any(
            not (secret.end_pos <= start or secret.start_pos >= end)
            for start, end in pattern_ranges
        )
        if not overlaps:
            all_secrets.append(secret)

    # Sort by position for consistent replacement, then by length (longest first)
    all_secrets.sort(key=lambda s: (s.start_pos, -(s.end_pos - s.start_pos)))

    # Remove overlapping detections (keep the longest match)
    non_overlapping: List[DetectedSecret] = []
    for secret in all_secrets:
        overlaps = False
        for existing in non_overlapping:
            # Check if this secret overlaps with an existing one
            if not (secret.end_pos <= existing.start_pos or secret.start_pos >= existing.end_pos):
                overlaps = True
                break
        if not overlaps:
            non_overlapping.append(secret)

    # Sort by position for replacement
    non_overlapping.sort(key=lambda s: s.start_pos)
    all_secrets = non_overlapping

    # Sanitize text by replacing secrets
    sanitized = text
    offset = 0
    for secret in all_secrets:
        if secret.action == SecretAction.REMOVE:
            placeholder = f"<{secret.pattern_name.upper()}_REDACTED>"
            start = secret.start_pos + offset
            end = secret.end_pos + offset
            sanitized = sanitized[:start] + placeholder + sanitized[end:]
            offset += len(placeholder) - (secret.end_pos - secret.start_pos)

    # Calculate remaining risk
    reject_count = sum(1 for s in all_secrets if s.action == SecretAction.REJECT)
    remove_count = sum(1 for s in all_secrets if s.action == SecretAction.REMOVE)

    if reject_count > 0:
        remaining_risk = 1.0  # Private keys should cause rejection
    elif remove_count > 5:
        remaining_risk = 0.3  # Many secrets removed, some risk remains
    elif remove_count > 0:
        remaining_risk = 0.1  # Some secrets removed
    else:
        remaining_risk = 0.0  # No secrets found

    # Calculate scan confidence based on coverage
    scan_confidence = 0.95 if all_secrets else 0.98

    return SecretScanResult(
        secrets=all_secrets,
        sanitized_text=sanitized,
        remaining_risk=remaining_risk,
        scan_confidence=scan_confidence,
    )


def should_reject_submission(result: SecretScanResult) -> Tuple[bool, Optional[str]]:
    """Determine if a submission should be rejected based on detected secrets.

    Args:
        result: The secret scan result.

    Returns:
        Tuple[bool, Optional[str]]: (should_reject, reason)
    """
    # Check for secrets that require rejection
    reject_secrets = [s for s in result.secrets if s.action == SecretAction.REJECT]

    if reject_secrets:
        patterns = list(set(s.pattern_name for s in reject_secrets))
        return (
            True,
            f"Submission contains sensitive content that cannot be safely sanitized: {', '.join(patterns)}",
        )

    # Check for too many secrets (potential credential dump)
    if len(result.secrets) > 10:
        return (
            True,
            "Submission contains too many detected secrets (>10). Please remove sensitive data before submitting.",
        )

    return (False, None)
