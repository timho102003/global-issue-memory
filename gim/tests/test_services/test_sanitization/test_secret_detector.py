"""Tests for secret detection module."""

import pytest

from src.services.sanitization.secret_detector import (
    SecretAction,
    calculate_entropy,
    detect_high_entropy_strings,
    detect_secrets,
    should_reject_submission,
)


class TestCalculateEntropy:
    """Tests for entropy calculation."""

    def test_empty_string(self) -> None:
        """Test entropy of empty string."""
        assert calculate_entropy("") == 0.0

    def test_single_character(self) -> None:
        """Test entropy of single repeated character."""
        assert calculate_entropy("aaaa") == 0.0

    def test_high_entropy_string(self) -> None:
        """Test entropy of random-looking string."""
        # API keys typically have high entropy
        entropy = calculate_entropy("sk-abc123XYZ789def456GHI012jkl345MNO")
        assert entropy > 4.0

    def test_low_entropy_string(self) -> None:
        """Test entropy of predictable string."""
        entropy = calculate_entropy("hello world")
        assert entropy < 4.0


class TestDetectHighEntropyStrings:
    """Tests for high entropy string detection."""

    def test_detects_random_string(self) -> None:
        """Test detection of high entropy strings."""
        text = "The key is abc123XYZ789def456GHI012jkl345MNO678pqr901STU"
        secrets = detect_high_entropy_strings(text, min_length=20)
        assert len(secrets) > 0

    def test_ignores_normal_text(self) -> None:
        """Test that normal text is not flagged."""
        text = "This is a normal error message without any secrets"
        secrets = detect_high_entropy_strings(text)
        assert len(secrets) == 0


class TestDetectSecrets:
    """Tests for secret detection."""

    def test_detects_openai_key(self) -> None:
        """Test detection of OpenAI API key."""
        # Long key (48+ chars) - matches openai_key pattern directly
        text = 'my_key = "sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMN"'
        result = detect_secrets(text)
        assert len(result.secrets) > 0
        assert any("openai" in s.pattern_name for s in result.secrets)

    def test_detects_openai_key_in_api_context(self) -> None:
        """Test detection of OpenAI API key in api_key context."""
        # Key with api_key = context - may match generic_api_key pattern (still detected)
        text = 'config = {"api_key": "sk-abcdefghijklmnopqrstuvwxyz1234567890ABC"}'
        result = detect_secrets(text)
        assert len(result.secrets) > 0
        # Either openai or generic pattern should match
        assert any("openai" in s.pattern_name or "api_key" in s.pattern_name for s in result.secrets)

    def test_detects_github_token(self) -> None:
        """Test detection of GitHub token."""
        text = "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        result = detect_secrets(text)
        assert len(result.secrets) > 0
        assert any("github" in s.pattern_name for s in result.secrets)

    def test_detects_aws_key(self) -> None:
        """Test detection of AWS access key."""
        text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        result = detect_secrets(text)
        assert len(result.secrets) > 0
        assert any("aws" in s.pattern_name for s in result.secrets)

    def test_detects_jwt_token(self) -> None:
        """Test detection of JWT token."""
        text = "token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = detect_secrets(text)
        assert len(result.secrets) > 0
        assert any("jwt" in s.pattern_name for s in result.secrets)

    def test_detects_private_key(self) -> None:
        """Test detection of private key."""
        text = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy
-----END RSA PRIVATE KEY-----"""
        result = detect_secrets(text)
        assert len(result.secrets) > 0
        # Private keys are now sanitized (REMOVE), not rejected
        assert any(s.action == SecretAction.REMOVE for s in result.secrets)
        assert "BEGIN RSA PRIVATE KEY" not in result.sanitized_text

    def test_detects_postgres_url(self) -> None:
        """Test detection of PostgreSQL connection string."""
        text = "DATABASE_URL=postgresql://user:password123@localhost:5432/mydb"
        result = detect_secrets(text)
        assert len(result.secrets) > 0
        assert any("postgres" in s.pattern_name for s in result.secrets)

    def test_sanitizes_text(self) -> None:
        """Test that secrets are replaced in sanitized text."""
        text = "api_key = sk-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKL"
        result = detect_secrets(text)
        assert "sk-" not in result.sanitized_text
        assert "REDACTED" in result.sanitized_text

    def test_no_secrets_in_clean_text(self) -> None:
        """Test that clean text passes without changes."""
        text = "AttributeError: 'NoneType' object has no attribute 'status'"
        result = detect_secrets(text)
        assert len(result.secrets) == 0
        assert result.sanitized_text == text
        assert result.remaining_risk == 0.0

    def test_empty_text(self) -> None:
        """Test handling of empty text."""
        result = detect_secrets("")
        assert result.sanitized_text == ""
        assert result.scan_confidence == 1.0


class TestShouldRejectSubmission:
    """Tests for rejection logic."""

    def test_sanitizes_private_key(self) -> None:
        """Test that private keys are sanitized, not rejected."""
        text = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC
-----END PRIVATE KEY-----"""
        result = detect_secrets(text)
        # Private keys are now sanitized (no rejection)
        should_reject, reason = should_reject_submission(result)
        assert should_reject is False
        # But they should be redacted
        assert "BEGIN PRIVATE KEY" not in result.sanitized_text
        assert "REDACTED" in result.sanitized_text

    def test_accepts_cleaned_text(self) -> None:
        """Test that cleaned text is accepted."""
        text = "Error: Module not found"
        result = detect_secrets(text)
        should_reject, reason = should_reject_submission(result)
        assert should_reject is False
        assert reason is None

    def test_rejects_too_many_secrets(self) -> None:
        """Test that many secrets cause rejection."""
        # Create text with many API-key-like patterns
        keys = [f'key{i} = "sk-{"x" * 50}"' for i in range(15)]
        text = "\n".join(keys)
        result = detect_secrets(text)
        should_reject, reason = should_reject_submission(result)
        assert should_reject is True
        assert "too many" in reason.lower()


class TestGenericPatterns:
    """Tests for generic secret patterns."""

    def test_detects_generic_api_key(self) -> None:
        """Test detection of generic API key pattern."""
        text = 'config = {"api_key": "very_secret_key_12345678901234567890"}'
        result = detect_secrets(text)
        assert len(result.secrets) > 0

    def test_detects_generic_password(self) -> None:
        """Test detection of generic password pattern."""
        text = 'password = "super_secret_password_123"'
        result = detect_secrets(text)
        assert len(result.secrets) > 0

    def test_detects_bearer_token(self) -> None:
        """Test detection of Bearer token."""
        text = 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature'
        result = detect_secrets(text)
        assert len(result.secrets) > 0
