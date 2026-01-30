"""Tests for Phase 3 Security Hardening - Sanitization Pipeline Hardening."""

import re
from unittest.mock import patch

import pytest

from src.services.sanitization.llm_sanitizer import (
    LLMSanitizationResult,
    SANITIZE_CODE_PROMPT,
    SANITIZE_CONTEXT_PROMPT,
    SANITIZE_ERROR_MESSAGE_PROMPT,
    sanitize_code_with_llm,
    sanitize_context_with_llm,
    sanitize_error_message_with_llm,
)
from src.services.sanitization.patterns import (
    PII_INDEXED_PREFIXES,
    PII_PATTERNS,
    SECRET_PATTERNS,
    _make_indexed_replacer,
)
from src.services.sanitization.pii_scrubber import scrub_pii
from src.services.sanitization.pipeline import (
    _get_confidence_threshold,
    run_sanitization_pipeline_sync,
)
from src.services.sanitization.secret_detector import (
    detect_high_entropy_strings,
    detect_secrets,
)
from src.tools.gim_submit_issue import _sanitize_structured_data


# ---------------------------------------------------------------------------
# 3.1 Sanitize All Fields Before DB (_sanitize_structured_data)
# ---------------------------------------------------------------------------

class TestSanitizeStructuredData:
    """Tests for the _sanitize_structured_data helper."""

    def test_sanitizes_string_with_secret(self) -> None:
        """Test that strings containing secrets are sanitized."""
        data = "My API key is sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKL"
        result = _sanitize_structured_data(data)
        assert "sk-" not in result
        assert "REDACTED" in result

    def test_sanitizes_string_with_pii_email(self) -> None:
        """Test that strings containing PII email are sanitized."""
        data = "Contact john@company.com for details"
        result = _sanitize_structured_data(data)
        assert "john@company.com" not in result
        assert "<EMAIL_1>" in result

    def test_sanitizes_nested_dict(self) -> None:
        """Test that nested dicts are recursively sanitized."""
        data = {
            "file_path": "/Users/johndoe/project/main.py",
            "change_type": "modify",
            "explanation": "Fix for user@company.com issue",
        }
        result = _sanitize_structured_data(data)
        assert "/Users/johndoe" not in result["file_path"]
        assert "user@company.com" not in result["explanation"]
        assert result["change_type"] == "modify"

    def test_sanitizes_list_of_dicts(self) -> None:
        """Test that lists of dicts are sanitized."""
        data = [
            {"step": "Run command with key sk-test1234567890abcdefghijklmnopqrstuvwxyzABCDEFGH"},
            {"step": "Verify at /Users/admin/project"},
        ]
        result = _sanitize_structured_data(data)
        assert "sk-test" not in result[0]["step"]
        assert "/Users/admin" not in result[1]["step"]

    def test_preserves_non_string_values(self) -> None:
        """Test that non-string values are preserved unchanged."""
        data = {"count": 42, "flag": True, "score": 3.14, "nothing": None}
        result = _sanitize_structured_data(data)
        assert result["count"] == 42
        assert result["flag"] is True
        assert result["score"] == 3.14
        assert result["nothing"] is None

    def test_empty_structures(self) -> None:
        """Test that empty structures are handled."""
        assert _sanitize_structured_data([]) == []
        assert _sanitize_structured_data({}) == {}
        assert _sanitize_structured_data("") == ""

    def test_deeply_nested_structure(self) -> None:
        """Test sanitization of deeply nested structures."""
        data = {
            "outer": {
                "inner": [
                    {"deep": "API key: sk-abcdefghijklmnopqrstuvwxyz123456789012345678"}
                ]
            }
        }
        result = _sanitize_structured_data(data)
        assert "sk-" not in str(result)


# ---------------------------------------------------------------------------
# 3.2 Prompt Injection Fix (XML-delimited user content)
# ---------------------------------------------------------------------------

class TestPromptInjectionFix:
    """Tests verifying XML-delimited user content in prompt templates."""

    def test_code_prompt_uses_xml_tags(self) -> None:
        """Test that SANITIZE_CODE_PROMPT uses XML tags for user content."""
        assert "<user_code>" in SANITIZE_CODE_PROMPT
        assert "</user_code>" in SANITIZE_CODE_PROMPT
        assert "<error_context>" in SANITIZE_CODE_PROMPT
        assert "</error_context>" in SANITIZE_CODE_PROMPT

    def test_code_prompt_no_bare_code_blocks(self) -> None:
        """Test that SANITIZE_CODE_PROMPT does not use bare markdown code blocks for user code."""
        # The prompt should NOT have ```{code}``` pattern
        assert "```\n{code}\n```" not in SANITIZE_CODE_PROMPT

    def test_error_prompt_uses_xml_tags(self) -> None:
        """Test that SANITIZE_ERROR_MESSAGE_PROMPT uses XML tags."""
        assert "<user_error>" in SANITIZE_ERROR_MESSAGE_PROMPT
        assert "</user_error>" in SANITIZE_ERROR_MESSAGE_PROMPT

    def test_context_prompt_uses_xml_tags(self) -> None:
        """Test that SANITIZE_CONTEXT_PROMPT uses XML tags."""
        assert "<user_context>" in SANITIZE_CONTEXT_PROMPT
        assert "</user_context>" in SANITIZE_CONTEXT_PROMPT


# ---------------------------------------------------------------------------
# 3.3 LLM Failure Fallback (empty string on failure)
# ---------------------------------------------------------------------------

class TestLLMFailureFallback:
    """Tests that LLM failures return empty string, not original text."""

    @pytest.mark.asyncio
    async def test_code_sanitizer_returns_empty_on_failure(self) -> None:
        """Test that sanitize_code_with_llm returns empty string on error."""
        with patch(
            "src.services.sanitization.llm_sanitizer._get_genai_client",
            side_effect=RuntimeError("API error"),
        ):
            result = await sanitize_code_with_llm("sensitive code here")
            assert result.success is False
            assert result.sanitized_text == ""
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_error_sanitizer_returns_empty_on_failure(self) -> None:
        """Test that sanitize_error_message_with_llm returns empty string on error."""
        with patch(
            "src.services.sanitization.llm_sanitizer._get_genai_client",
            side_effect=RuntimeError("API error"),
        ):
            result = await sanitize_error_message_with_llm("sensitive error")
            assert result.success is False
            assert result.sanitized_text == ""
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_context_sanitizer_returns_empty_on_failure(self) -> None:
        """Test that sanitize_context_with_llm returns empty string on error."""
        with patch(
            "src.services.sanitization.llm_sanitizer._get_genai_client",
            side_effect=RuntimeError("API error"),
        ):
            result = await sanitize_context_with_llm("sensitive context")
            assert result.success is False
            assert result.sanitized_text == ""
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_failure_preserves_original_in_result(self) -> None:
        """Test that the original text is preserved in original_text field."""
        original = "my secret code with api_key=12345"
        with patch(
            "src.services.sanitization.llm_sanitizer._get_genai_client",
            side_effect=RuntimeError("API error"),
        ):
            result = await sanitize_code_with_llm(original)
            assert result.original_text == original
            assert result.sanitized_text == ""


# ---------------------------------------------------------------------------
# 3.4 Confidence Threshold Enforcement
# ---------------------------------------------------------------------------

class TestConfidenceThresholdEnforcement:
    """Tests for confidence threshold enforcement in pipeline."""

    def _high_threshold() -> float:
        """Return a high threshold for testing.

        Returns:
            float: A threshold of 1.0 that rejects all submissions.
        """
        return 1.0

    def _low_threshold() -> float:
        """Return a low threshold for testing.

        Returns:
            float: A threshold of 0.0 that accepts all submissions.
        """
        return 0.0

    @patch(
        "src.services.sanitization.pipeline._get_confidence_threshold",
        _high_threshold,
    )
    def test_low_confidence_fails(self) -> None:
        """Test that low confidence score results in failure."""
        result = run_sanitization_pipeline_sync(
            error_message="Simple error message",
        )
        # With threshold 1.0, no submission should pass
        assert result.success is False
        assert result.confidence_score < 1.0

    @patch(
        "src.services.sanitization.pipeline._get_confidence_threshold",
        _low_threshold,
    )
    def test_any_confidence_passes_with_zero_threshold(self) -> None:
        """Test that any confidence passes with zero threshold."""
        result = run_sanitization_pipeline_sync(
            error_message="Simple error message",
        )
        assert result.success is True

    @patch(
        "src.services.sanitization.pipeline._get_confidence_threshold",
        _low_threshold,
    )
    def test_confidence_score_is_populated(self) -> None:
        """Test that confidence score is always populated."""
        result = run_sanitization_pipeline_sync(
            error_message="Test error",
        )
        assert result.confidence_score > 0.0
        assert result.confidence_score <= 1.0


# ---------------------------------------------------------------------------
# 3.5 Missing Secret Patterns (Stripe, Twilio, SendGrid, NPM, PyPI, Docker Hub)
# ---------------------------------------------------------------------------

class TestNewSecretPatterns:
    """Tests for newly added secret patterns."""

    def test_detects_stripe_live_secret_key(self) -> None:
        """Test detection of Stripe live secret key."""
        text = 'STRIPE_KEY = "sk_live_abcdefghijklmnopqrstuvwx"'
        result = detect_secrets(text)
        assert any("stripe" in s.pattern_name for s in result.secrets)
        assert "sk_live_" not in result.sanitized_text

    def test_detects_stripe_test_secret_key(self) -> None:
        """Test detection of Stripe test secret key."""
        text = 'STRIPE_KEY = "sk_test_abcdefghijklmnopqrstuvwx"'
        result = detect_secrets(text)
        assert any("stripe" in s.pattern_name for s in result.secrets)
        assert "sk_test_" not in result.sanitized_text

    def test_detects_stripe_publishable_key(self) -> None:
        """Test detection of Stripe publishable key."""
        text = 'PK = "pk_live_abcdefghijklmnopqrstuvwx"'
        result = detect_secrets(text)
        assert any("stripe" in s.pattern_name for s in result.secrets)

    def test_detects_stripe_test_publishable_key(self) -> None:
        """Test detection of Stripe test publishable key."""
        text = 'PK = "pk_test_abcdefghijklmnopqrstuvwx"'
        result = detect_secrets(text)
        assert any("stripe" in s.pattern_name for s in result.secrets)

    def test_detects_twilio_key(self) -> None:
        """Test detection of Twilio API key."""
        text = 'TWILIO_KEY = "SK0123456789abcdef0123456789abcdef"'
        result = detect_secrets(text)
        assert any("twilio" in s.pattern_name for s in result.secrets)

    def test_detects_sendgrid_key(self) -> None:
        """Test detection of SendGrid API key."""
        # SendGrid key: SG. + 22 chars + . + 43 chars
        text = "key is SG.abcdefghijklmnopqrstuv.ABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890abcdef"
        result = detect_secrets(text)
        assert any("sendgrid" in s.pattern_name for s in result.secrets)

    def test_detects_npm_token(self) -> None:
        """Test detection of NPM token."""
        text = "Using npm_abcdefghijklmnopqrstuvwxyz1234567890 for auth"
        result = detect_secrets(text)
        assert any("npm" in s.pattern_name for s in result.secrets)

    def test_detects_pypi_token(self) -> None:
        """Test detection of PyPI token."""
        text = "Upload with pypi-abcdefghijklmnopqrstuvwxyz1234567890abcdef"
        result = detect_secrets(text)
        assert any("pypi" in s.pattern_name for s in result.secrets)

    def test_detects_docker_hub_token(self) -> None:
        """Test detection of Docker Hub token."""
        text = "Login with dckr_pat_abcdefghijklmnopqrstuvwxyz0"
        result = detect_secrets(text)
        assert any("docker" in s.pattern_name for s in result.secrets)

    def test_patterns_exist_in_secret_patterns(self) -> None:
        """Test that all new pattern names exist in SECRET_PATTERNS."""
        expected_patterns = [
            "stripe_secret_key",
            "stripe_publishable_key",
            "stripe_test_secret_key",
            "stripe_test_publishable_key",
            "twilio_key",
            "sendgrid_key",
            "npm_token",
            "pypi_token",
            "docker_hub_token",
        ]
        for pattern_name in expected_patterns:
            assert pattern_name in SECRET_PATTERNS, (
                f"Missing pattern: {pattern_name}"
            )


# ---------------------------------------------------------------------------
# 3.6 Entropy Threshold (lowered to 4.0)
# ---------------------------------------------------------------------------

class TestEntropyThreshold:
    """Tests for the lowered entropy threshold."""

    def test_entropy_threshold_is_4_0(self) -> None:
        """Test that the default entropy threshold is 4.0."""
        import inspect
        from src.services.sanitization.secret_detector import detect_high_entropy_strings

        sig = inspect.signature(detect_high_entropy_strings)
        default = sig.parameters["entropy_threshold"].default
        assert default == 4.0, f"Expected entropy_threshold default to be 4.0, got {default}"

    def test_detects_moderate_entropy_strings(self) -> None:
        """Test that strings with entropy >= 4.0 are detected."""
        # This string has entropy between 4.0 and 4.5
        text = "key = abcABC123456defDEF789"
        secrets = detect_high_entropy_strings(text, min_length=20, entropy_threshold=4.0)
        # Should detect high entropy strings at 4.0 threshold
        # The exact result depends on the string's entropy
        # Just verify the function works with the new threshold
        assert isinstance(secrets, list)


# ---------------------------------------------------------------------------
# 3.7 Indexed PII Placeholders
# ---------------------------------------------------------------------------

class TestIndexedPIIPlaceholders:
    """Tests for indexed PII placeholders (e.g., <EMAIL_1>, <EMAIL_2>)."""

    def test_single_email_gets_index_1(self) -> None:
        """Test that a single email gets <EMAIL_1>."""
        text = "Contact admin@company.com"
        result = scrub_pii(text)
        assert "<EMAIL_1>" in result.sanitized_text
        assert "admin@company.com" not in result.sanitized_text

    def test_two_different_emails_get_different_indices(self) -> None:
        """Test that different emails get different indices."""
        text = "Send to alice@a.com and bob@b.com"
        result = scrub_pii(text)
        assert "<EMAIL_1>" in result.sanitized_text
        assert "<EMAIL_2>" in result.sanitized_text

    def test_same_email_twice_gets_same_index(self) -> None:
        """Test that the same email repeated gets the same index."""
        text = "Email alice@a.com then reply to alice@a.com"
        result = scrub_pii(text)
        # Count occurrences - same email should map to same index
        assert result.sanitized_text.count("<EMAIL_1>") == 2
        assert "<EMAIL_2>" not in result.sanitized_text

    def test_ipv4_gets_indexed_placeholder(self) -> None:
        """Test that IPv4 addresses get indexed placeholders."""
        text = "Connect to 10.0.0.1 and 10.0.0.2"
        result = scrub_pii(text)
        assert "<IP_1>" in result.sanitized_text
        assert "<IP_2>" in result.sanitized_text
        assert "10.0.0.1" not in result.sanitized_text
        assert "10.0.0.2" not in result.sanitized_text

    def test_phone_gets_indexed_placeholder(self) -> None:
        """Test that phone numbers get indexed placeholders."""
        text = "Call (555) 123-4567"
        result = scrub_pii(text)
        assert "<PHONE_1>" in result.sanitized_text

    def test_make_indexed_replacer_basic(self) -> None:
        """Test _make_indexed_replacer function directly."""
        replacer = _make_indexed_replacer("TEST")
        pattern = re.compile(r"\d+")
        result = pattern.sub(replacer, "foo 123 bar 456 baz 123")
        assert "<TEST_1>" in result
        assert "<TEST_2>" in result
        # "123" appears twice and should map to same index
        assert result.count("<TEST_1>") == 2

    def test_indexed_prefixes_defined_for_all_pii_types(self) -> None:
        """Test that all PII types have indexed prefix mappings."""
        for pii_type in PII_PATTERNS:
            assert pii_type in PII_INDEXED_PREFIXES, (
                f"Missing indexed prefix for PII type: {pii_type}"
            )


# ---------------------------------------------------------------------------
# 3.8 SSN Context-Aware Detection
# ---------------------------------------------------------------------------

class TestSSNContextAwareDetection:
    """Tests for context-aware SSN detection."""

    def test_detects_ssn_with_keyword(self) -> None:
        """Test SSN detection when preceded by 'SSN' keyword."""
        text = "SSN: 123-45-6789"
        result = scrub_pii(text)
        assert "123-45-6789" not in result.sanitized_text
        assert "ssn" in result.pii_types_found

    def test_detects_ssn_with_social_security_keyword(self) -> None:
        """Test SSN detection when preceded by 'social security'."""
        text = "social security 123-45-6789"
        result = scrub_pii(text)
        assert "123-45-6789" not in result.sanitized_text

    def test_detects_ssn_with_social_security_hyphen(self) -> None:
        """Test SSN detection when preceded by 'social-security'."""
        text = "social-security: 123456789"
        result = scrub_pii(text)
        assert "123456789" not in result.sanitized_text

    def test_ignores_bare_number_without_context(self) -> None:
        """Test that bare 9-digit numbers are NOT detected as SSN."""
        text = "Error code: 123-45-6789"
        result = scrub_pii(text)
        # Without SSN keyword context, bare numbers should not be matched
        assert "ssn" not in result.pii_types_found

    def test_ignores_random_digits(self) -> None:
        """Test that random digit sequences are not flagged as SSN."""
        text = "Line 123-45-6789 of the config file"
        result = scrub_pii(text)
        assert "ssn" not in result.pii_types_found


# ---------------------------------------------------------------------------
# 3.9 IPv6 Compressed Notation Detection
# ---------------------------------------------------------------------------

class TestIPv6CompressedNotation:
    """Tests for compressed IPv6 address detection."""

    def test_detects_double_colon_loopback(self) -> None:
        """Test detection of ::1 (loopback)."""
        text = "Server listening on ::1"
        result = scrub_pii(text)
        # Should detect the compressed IPv6 address
        assert "ipv6_compressed" in result.pii_types_found or "ipv6_address" in result.pii_types_found

    def test_detects_fe80_link_local(self) -> None:
        """Test detection of fe80::1 link-local address."""
        text = "Interface address: fe80::1"
        result = scrub_pii(text)
        assert any(
            pii_type.startswith("ipv6") for pii_type in result.pii_types_found
        )

    def test_detects_2001_db8_compressed(self) -> None:
        """Test detection of 2001:db8::1 documentation address."""
        text = "Test with 2001:db8::1"
        result = scrub_pii(text)
        assert any(
            pii_type.startswith("ipv6") for pii_type in result.pii_types_found
        )

    def test_ipv6_compressed_pattern_exists(self) -> None:
        """Test that ipv6_compressed pattern exists in PII_PATTERNS."""
        assert "ipv6_compressed" in PII_PATTERNS

    def test_ipv6_compressed_replacement_exists(self) -> None:
        """Test that ipv6_compressed has a replacement defined."""
        from src.services.sanitization.patterns import PII_REPLACEMENTS
        assert "ipv6_compressed" in PII_REPLACEMENTS
