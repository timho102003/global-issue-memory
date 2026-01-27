"""PII (Personally Identifiable Information) scrubbing module."""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .patterns import PII_PATTERNS, PII_REPLACEMENTS


@dataclass
class DetectedPII:
    """A detected PII item with its metadata.

    Attributes:
        pii_type: Type of PII detected (email, path, etc.).
        original_text: The original text that was matched.
        replacement: The replacement text to use.
        start_pos: Start position in the original text.
        end_pos: End position in the original text.
    """

    pii_type: str
    original_text: str
    replacement: str
    start_pos: int
    end_pos: int


@dataclass
class PIIScanResult:
    """Result of scanning text for PII.

    Attributes:
        pii_items: List of detected PII items.
        sanitized_text: Text with PII replaced.
        pii_types_found: Set of PII types that were found.
        remaining_risk: Estimated remaining PII risk (0.0-1.0).
        scan_confidence: Confidence in the scan completeness (0.0-1.0).
    """

    pii_items: List[DetectedPII] = field(default_factory=list)
    sanitized_text: str = ""
    pii_types_found: Set[str] = field(default_factory=set)
    remaining_risk: float = 0.0
    scan_confidence: float = 1.0


def _replace_file_paths(text: str) -> tuple[str, List[DetectedPII]]:
    """Replace file paths with generic placeholders.

    Handles Unix-style paths (/Users/username/..., /home/username/...)
    and Windows-style paths (C:\\Users\\username\\...).

    Args:
        text: The text to process.

    Returns:
        Tuple of (sanitized_text, list of detected PII items).
    """
    pii_items = []

    # Unix home paths
    unix_pattern = PII_PATTERNS["unix_home_path"]
    for match in unix_pattern.finditer(text):
        username = match.group(1)
        full_match = match.group(0)

        pii_items.append(
            DetectedPII(
                pii_type="unix_home_path",
                original_text=full_match,
                replacement="/path/to",
                start_pos=match.start(),
                end_pos=match.end(),
            )
        )

    # Windows user paths
    windows_pattern = PII_PATTERNS["windows_user_path"]
    for match in windows_pattern.finditer(text):
        username = match.group(1)
        full_match = match.group(0)

        pii_items.append(
            DetectedPII(
                pii_type="windows_user_path",
                original_text=full_match,
                replacement="C:\\path\\to",
                start_pos=match.start(),
                end_pos=match.end(),
            )
        )

    return text, pii_items


def scrub_pii(text: str) -> PIIScanResult:
    """Scrub PII from text by replacing with generic placeholders.

    This function detects and replaces:
    - Email addresses
    - File paths with usernames
    - IP addresses
    - Internal URLs
    - Phone numbers
    - Credit card numbers
    - Social Security Numbers

    Args:
        text: The text to scrub.

    Returns:
        PIIScanResult: Result containing detected PII and sanitized text.
    """
    if not text:
        return PIIScanResult(
            sanitized_text="",
            scan_confidence=1.0,
            remaining_risk=0.0,
        )

    all_pii: List[DetectedPII] = []

    # Detect all PII types
    for pii_type, pattern in PII_PATTERNS.items():
        replacement = PII_REPLACEMENTS.get(pii_type, "<REDACTED>")

        for match in pattern.finditer(text):
            # For paths, we want the full path, not just the username
            if pii_type in ("unix_home_path", "windows_user_path"):
                # Find the full path starting from the match
                full_match = match.group(0)
                # Extend to include the rest of the path
                end_pos = match.end()
                while end_pos < len(text) and text[end_pos] not in (' ', '\n', '\t', '"', "'", ')'):
                    end_pos += 1
                full_match = text[match.start():end_pos]

                # Adjust replacement to preserve path structure
                if pii_type == "unix_home_path":
                    replacement = "/path/to/project" + full_match[len(match.group(0)):]
                else:
                    replacement = "C:\\path\\to\\project" + full_match[len(match.group(0)):]

                all_pii.append(
                    DetectedPII(
                        pii_type=pii_type,
                        original_text=full_match,
                        replacement=replacement,
                        start_pos=match.start(),
                        end_pos=end_pos,
                    )
                )
            else:
                all_pii.append(
                    DetectedPII(
                        pii_type=pii_type,
                        original_text=match.group(0),
                        replacement=replacement,
                        start_pos=match.start(),
                        end_pos=match.end(),
                    )
                )

    # Remove duplicates (overlapping matches)
    all_pii = _remove_overlapping_matches(all_pii)

    # Sort by position (reverse for safe replacement)
    all_pii.sort(key=lambda p: p.start_pos, reverse=True)

    # Replace PII in text (from end to start to preserve positions)
    sanitized = text
    for pii in all_pii:
        sanitized = sanitized[:pii.start_pos] + pii.replacement + sanitized[pii.end_pos:]

    # Re-sort for output
    all_pii.sort(key=lambda p: p.start_pos)

    # Collect PII types found
    pii_types_found = set(p.pii_type for p in all_pii)

    # Calculate remaining risk
    sensitive_types = {"email", "credit_card", "ssn", "phone_us"}
    sensitive_found = pii_types_found & sensitive_types

    if sensitive_found:
        remaining_risk = 0.1 * len(sensitive_found)
    else:
        remaining_risk = 0.05 if all_pii else 0.0

    # Calculate scan confidence
    # Lower confidence if we found many PII items (might have missed some)
    scan_confidence = max(0.85, 1.0 - (len(all_pii) * 0.02))

    return PIIScanResult(
        pii_items=all_pii,
        sanitized_text=sanitized,
        pii_types_found=pii_types_found,
        remaining_risk=min(remaining_risk, 0.5),
        scan_confidence=scan_confidence,
    )


def _remove_overlapping_matches(pii_items: List[DetectedPII]) -> List[DetectedPII]:
    """Remove overlapping PII matches, keeping the longer one.

    Args:
        pii_items: List of detected PII items.

    Returns:
        List[DetectedPII]: Filtered list with no overlaps.
    """
    if not pii_items:
        return []

    # Sort by start position, then by length (longer first)
    sorted_items = sorted(
        pii_items,
        key=lambda p: (p.start_pos, -(p.end_pos - p.start_pos))
    )

    result = []
    last_end = -1

    for item in sorted_items:
        if item.start_pos >= last_end:
            result.append(item)
            last_end = item.end_pos

    return result


def get_pii_summary(result: PIIScanResult) -> Dict[str, int]:
    """Get a summary of PII types found.

    Args:
        result: The PII scan result.

    Returns:
        Dict[str, int]: Count of each PII type found.
    """
    summary: Dict[str, int] = {}
    for pii in result.pii_items:
        summary[pii.pii_type] = summary.get(pii.pii_type, 0) + 1
    return summary
