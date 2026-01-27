"""Sanitization pipeline orchestrator with two-layer approach.

Layer 1: Deterministic detection (regex-based)
Layer 2: LLM-based intelligent sanitization (Gemini)
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .llm_sanitizer import (
    LLMSanitizationResult,
    sanitize_code_with_llm,
    sanitize_context_with_llm,
    sanitize_error_message_with_llm,
)
from .mre_synthesizer import MREResult, synthesize_mre
from .pii_scrubber import PIIScanResult, scrub_pii
from .secret_detector import SecretScanResult, detect_secrets


@dataclass
class SanitizationResult:
    """Final result of the sanitization pipeline.

    Attributes:
        success: Whether sanitization succeeded.
        sanitized_error: Sanitized error message.
        sanitized_context: Sanitized context/description.
        sanitized_mre: Synthesized minimal reproducible example.
        confidence_score: Overall confidence in sanitization (0.0-1.0).
        warnings: List of warnings during processing.
        secret_scan: Secret detection result (Layer 1).
        pii_scan: PII scrubbing result (Layer 1).
        mre_result: MRE synthesis result.
        llm_sanitization_used: Whether LLM was used for sanitization.
    """

    success: bool = False
    sanitized_error: str = ""
    sanitized_context: str = ""
    sanitized_mre: str = ""
    confidence_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    secret_scan: Optional[SecretScanResult] = None
    pii_scan: Optional[PIIScanResult] = None
    mre_result: Optional[MREResult] = None
    llm_sanitization_used: bool = False


def calculate_confidence_score(
    secret_result: SecretScanResult,
    pii_result: PIIScanResult,
    mre_result: Optional[MREResult],
    llm_used: bool = False,
) -> float:
    """Calculate overall sanitization confidence score.

    Formula:
    confidence = (secret_scan_conf × 0.35) + (pii_scan_conf × 0.25) +
                 (mre_quality × 0.2) + (syntax_valid × 0.1) + (llm_bonus × 0.1)

    Args:
        secret_result: Result from secret detection.
        pii_result: Result from PII scrubbing.
        mre_result: Result from MRE synthesis.
        llm_used: Whether LLM sanitization was applied.

    Returns:
        float: Confidence score between 0.0 and 1.0.
    """
    # Secret detection confidence (35% weight)
    secret_conf = secret_result.scan_confidence * (1 - secret_result.remaining_risk * 0.5)
    secret_score = secret_conf * 0.35

    # PII scan confidence (25% weight)
    pii_conf = pii_result.scan_confidence * (1 - pii_result.remaining_risk * 0.5)
    pii_score = pii_conf * 0.25

    # MRE quality score (20% weight)
    if mre_result:
        mre_score = mre_result.quality_score * 0.2
    else:
        mre_score = 0.15  # Partial credit if no MRE needed

    # Syntax validity (10% weight)
    if mre_result:
        syntax_score = 0.1 if mre_result.syntax_valid else 0.05
    else:
        syntax_score = 0.1  # Full credit if no code to validate

    # LLM sanitization bonus (10% weight)
    llm_score = 0.1 if llm_used else 0.05

    total_confidence = secret_score + pii_score + mre_score + syntax_score + llm_score

    return min(max(total_confidence, 0.0), 1.0)


async def run_sanitization_pipeline(
    error_message: str,
    error_context: Optional[str] = None,
    code_snippet: Optional[str] = None,
    use_llm: bool = True,
) -> SanitizationResult:
    """Run the two-layer sanitization pipeline.

    Layer 1 (Deterministic):
    - Secret Detection - Find API keys, tokens, credentials
    - PII Scrubbing - Remove emails, paths, names, IPs
    - MRE Synthesis - Abstract code to minimal reproducible example

    Layer 2 (LLM-based):
    - Intelligent rewriting using Gemini
    - Context-aware sanitization
    - Domain name abstraction

    Args:
        error_message: The error message to sanitize.
        error_context: Optional context/description to sanitize.
        code_snippet: Optional code snippet to process into MRE.
        use_llm: Whether to use LLM for Layer 2 sanitization.

    Returns:
        SanitizationResult: Complete sanitization result.
    """
    result = SanitizationResult()
    all_warnings: List[str] = []

    # =========================================================================
    # LAYER 1: Deterministic Detection & Sanitization
    # =========================================================================

    # --- Process Error Message ---
    error_secret_result = detect_secrets(error_message)
    result.secret_scan = error_secret_result
    sanitized_error = error_secret_result.sanitized_text

    error_pii_result = scrub_pii(sanitized_error)
    result.pii_scan = error_pii_result
    sanitized_error = error_pii_result.sanitized_text

    if error_secret_result.secrets:
        all_warnings.append(
            f"Layer 1: Removed {len(error_secret_result.secrets)} potential secrets from error"
        )
    if error_pii_result.pii_items:
        all_warnings.append(
            f"Layer 1: Replaced {len(error_pii_result.pii_items)} PII items in error"
        )

    # --- Process Context ---
    sanitized_context = ""
    if error_context:
        context_secret_result = detect_secrets(error_context)
        sanitized_context = context_secret_result.sanitized_text

        context_pii_result = scrub_pii(sanitized_context)
        sanitized_context = context_pii_result.sanitized_text

        # Merge results for scoring
        error_secret_result.secrets.extend(context_secret_result.secrets)
        error_secret_result.remaining_risk = max(
            error_secret_result.remaining_risk,
            context_secret_result.remaining_risk
        )
        error_pii_result.pii_items.extend(context_pii_result.pii_items)
        error_pii_result.pii_types_found.update(context_pii_result.pii_types_found)

    # --- Process Code Snippet ---
    sanitized_code = ""
    mre_result: Optional[MREResult] = None

    if code_snippet:
        # First pass: deterministic sanitization
        code_secret_result = detect_secrets(code_snippet)
        sanitized_code = code_secret_result.sanitized_text

        code_pii_result = scrub_pii(sanitized_code)
        sanitized_code = code_pii_result.sanitized_text

        # Merge results
        error_secret_result.secrets.extend(code_secret_result.secrets)
        error_secret_result.remaining_risk = max(
            error_secret_result.remaining_risk,
            code_secret_result.remaining_risk
        )

        # MRE synthesis (deterministic name abstraction)
        mre_result = synthesize_mre(
            code=sanitized_code,
            error_message=sanitized_error,
            max_lines=50,
        )
        result.mre_result = mre_result
        sanitized_code = mre_result.synthesized_mre

        if mre_result.warnings:
            all_warnings.extend([f"Layer 1: {w}" for w in mre_result.warnings])
        if mre_result.names_replaced:
            all_warnings.append(
                f"Layer 1: Abstracted {len(mre_result.names_replaced)} domain-specific names"
            )

    # =========================================================================
    # LAYER 2: LLM-based Intelligent Sanitization
    # =========================================================================

    llm_used = False

    if use_llm:
        try:
            # Sanitize error message with LLM
            llm_error_result = await sanitize_error_message_with_llm(sanitized_error)
            if llm_error_result.success and llm_error_result.sanitized_text:
                sanitized_error = llm_error_result.sanitized_text
                if llm_error_result.changes_made:
                    all_warnings.extend([f"Layer 2: {c}" for c in llm_error_result.changes_made])
                    llm_used = True

            # Sanitize context with LLM
            if sanitized_context:
                llm_context_result = await sanitize_context_with_llm(sanitized_context)
                if llm_context_result.success and llm_context_result.sanitized_text:
                    sanitized_context = llm_context_result.sanitized_text
                    if llm_context_result.changes_made:
                        all_warnings.extend([f"Layer 2: {c}" for c in llm_context_result.changes_made])
                        llm_used = True

            # Sanitize code with LLM (most important)
            if sanitized_code:
                llm_code_result = await sanitize_code_with_llm(
                    sanitized_code,
                    error_context=sanitized_error,
                )
                if llm_code_result.success and llm_code_result.sanitized_text:
                    sanitized_code = llm_code_result.sanitized_text
                    if llm_code_result.changes_made:
                        all_warnings.extend([f"Layer 2: {c}" for c in llm_code_result.changes_made])
                        llm_used = True

        except Exception as e:
            all_warnings.append(f"Layer 2: LLM sanitization failed: {str(e)}, using Layer 1 only")

    result.llm_sanitization_used = llm_used

    # =========================================================================
    # Calculate Confidence Score
    # =========================================================================

    confidence = calculate_confidence_score(
        error_secret_result,
        error_pii_result,
        mre_result,
        llm_used=llm_used,
    )

    # =========================================================================
    # Build Result (Always succeed - no rejection)
    # =========================================================================

    result.success = True
    result.sanitized_error = sanitized_error
    result.sanitized_context = sanitized_context
    result.sanitized_mre = sanitized_code
    result.confidence_score = confidence
    result.warnings = all_warnings

    return result


def run_sanitization_pipeline_sync(
    error_message: str,
    error_context: Optional[str] = None,
    code_snippet: Optional[str] = None,
    use_llm: bool = False,
) -> SanitizationResult:
    """Synchronous version of sanitization pipeline (Layer 1 only).

    This version does not use LLM and runs synchronously.
    Useful for testing and cases where async is not available.

    Args:
        error_message: The error message to sanitize.
        error_context: Optional context/description to sanitize.
        code_snippet: Optional code snippet to process into MRE.
        use_llm: Ignored in sync version (always False).

    Returns:
        SanitizationResult: Complete sanitization result.
    """
    result = SanitizationResult()
    all_warnings: List[str] = []

    # Process Error Message
    error_secret_result = detect_secrets(error_message)
    result.secret_scan = error_secret_result
    sanitized_error = error_secret_result.sanitized_text

    error_pii_result = scrub_pii(sanitized_error)
    result.pii_scan = error_pii_result
    sanitized_error = error_pii_result.sanitized_text

    if error_secret_result.secrets:
        all_warnings.append(f"Removed {len(error_secret_result.secrets)} potential secrets")
    if error_pii_result.pii_items:
        all_warnings.append(f"Replaced {len(error_pii_result.pii_items)} PII items")

    # Process Context
    sanitized_context = ""
    if error_context:
        context_secret_result = detect_secrets(error_context)
        sanitized_context = context_secret_result.sanitized_text
        context_pii_result = scrub_pii(sanitized_context)
        sanitized_context = context_pii_result.sanitized_text

        error_secret_result.secrets.extend(context_secret_result.secrets)
        error_pii_result.pii_items.extend(context_pii_result.pii_items)

    # Process Code
    sanitized_code = ""
    mre_result: Optional[MREResult] = None

    if code_snippet:
        code_secret_result = detect_secrets(code_snippet)
        sanitized_code = code_secret_result.sanitized_text
        code_pii_result = scrub_pii(sanitized_code)
        sanitized_code = code_pii_result.sanitized_text

        mre_result = synthesize_mre(
            code=sanitized_code,
            error_message=sanitized_error,
            max_lines=50,
        )
        result.mre_result = mre_result
        sanitized_code = mre_result.synthesized_mre

        if mre_result.warnings:
            all_warnings.extend(mre_result.warnings)

    # Calculate confidence
    confidence = calculate_confidence_score(
        error_secret_result,
        error_pii_result,
        mre_result,
        llm_used=False,
    )

    result.success = True
    result.sanitized_error = sanitized_error
    result.sanitized_context = sanitized_context
    result.sanitized_mre = sanitized_code
    result.confidence_score = confidence
    result.warnings = all_warnings
    result.llm_sanitization_used = False

    return result


def quick_sanitize(text: str) -> tuple[str, List[str]]:
    """Quick sanitization for search queries and simple text.

    This is a lighter-weight sanitization for cases where full pipeline
    is not needed (e.g., search queries). Uses Layer 1 only.

    Args:
        text: The text to sanitize.

    Returns:
        Tuple of (sanitized_text, list of warnings).
    """
    warnings = []

    # Detect and remove secrets
    secret_result = detect_secrets(text)
    if secret_result.secrets:
        warnings.append(f"Removed {len(secret_result.secrets)} potential secrets")

    # Scrub PII
    pii_result = scrub_pii(secret_result.sanitized_text)
    if pii_result.pii_items:
        warnings.append(f"Replaced {len(pii_result.pii_items)} PII items")

    return pii_result.sanitized_text, warnings
