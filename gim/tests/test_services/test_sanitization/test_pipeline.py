"""Tests for sanitization pipeline with two-layer approach."""

from unittest.mock import patch

import pytest

from src.services.sanitization.pipeline import (
    calculate_confidence_score,
    quick_sanitize,
    run_sanitization_pipeline_sync,
)
from src.services.sanitization.secret_detector import SecretScanResult
from src.services.sanitization.pii_scrubber import PIIScanResult
from src.services.sanitization.mre_synthesizer import MREResult


def _low_threshold() -> float:
    """Return a low threshold for sanitization tests.

    Returns:
        float: A low confidence threshold that allows all submissions.
    """
    return 0.0


class TestRunSanitizationPipelineSync:
    """Tests for synchronous sanitization pipeline (Layer 1 only)."""

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_clean_submission(self) -> None:
        """Test pipeline with clean submission."""
        result = run_sanitization_pipeline_sync(
            error_message="AttributeError: 'NoneType' object has no attribute 'status'",
            error_context="The API returned None instead of a response object",
        )
        assert result.success is True
        assert result.confidence_score > 0.5

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_sanitizes_private_key_without_rejection(self) -> None:
        """Test that private keys are sanitized, not rejected."""
        result = run_sanitization_pipeline_sync(
            error_message="Failed to connect",
            error_context="""
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3
-----END RSA PRIVATE KEY-----
"""
        )
        # Should succeed (no rejection)
        assert result.success is True
        # Private key should be redacted
        assert "BEGIN RSA PRIVATE KEY" not in result.sanitized_context
        assert "REDACTED" in result.sanitized_context

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_sanitizes_secrets(self) -> None:
        """Test that secrets are sanitized."""
        result = run_sanitization_pipeline_sync(
            error_message="API error with key sk-abc123XYZ789def456GHI012jkl345MNO678pqr901",
        )
        assert result.success is True
        assert "sk-" not in result.sanitized_error
        assert "REDACTED" in result.sanitized_error

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_sanitizes_pii(self) -> None:
        """Test that PII is sanitized."""
        result = run_sanitization_pipeline_sync(
            error_message="Error in /Users/johndoe/project/app.py: email john@company.com",
        )
        assert result.success is True
        assert "/Users/johndoe" not in result.sanitized_error
        assert "john@company.com" not in result.sanitized_error

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_synthesizes_mre(self) -> None:
        """Test MRE synthesis in pipeline."""
        code = """
from mycompany.services import UserService

def get_user(user_id):
    service = UserService()
    return service.fetch(user_id)  # Error here
"""
        result = run_sanitization_pipeline_sync(
            error_message="AttributeError in UserService",
            code_snippet=code,
        )
        assert result.success is True
        assert result.sanitized_mre != ""
        # Domain names should be abstracted
        assert "UserService" not in result.sanitized_mre

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_collects_warnings(self) -> None:
        """Test that warnings are collected."""
        result = run_sanitization_pipeline_sync(
            error_message="Connect to 192.168.1.1 with user@example.org",
        )
        assert result.success is True
        # Should have warnings about sanitization
        assert len(result.warnings) > 0

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_empty_error_message(self) -> None:
        """Test handling of empty error message."""
        result = run_sanitization_pipeline_sync(error_message="")
        assert result.success is True
        assert result.sanitized_error == ""

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_handles_many_secrets_without_rejection(self) -> None:
        """Test that many secrets are sanitized, not rejected."""
        # Create text with many API-key-like patterns
        keys = [f'key{i} = "sk-{"x" * 50}"' for i in range(15)]
        text = "\n".join(keys)
        result = run_sanitization_pipeline_sync(error_message=text)
        # Should succeed (no rejection)
        assert result.success is True
        # All keys should be redacted
        assert "sk-" not in result.sanitized_error


class TestQuickSanitize:
    """Tests for quick sanitization function."""

    def test_sanitizes_secrets(self) -> None:
        """Test quick sanitization of secrets."""
        text = "Search for error with key sk-abcdefghijklmnopqrstuvwxyz123456789012345678"
        sanitized, warnings = quick_sanitize(text)
        assert "sk-" not in sanitized
        assert len(warnings) > 0

    def test_sanitizes_pii(self) -> None:
        """Test quick sanitization of PII."""
        text = "Error at /Users/john/project for user@company.com"
        sanitized, warnings = quick_sanitize(text)
        assert "/Users/john" not in sanitized
        assert "user@company.com" not in sanitized

    def test_clean_text(self) -> None:
        """Test quick sanitization of clean text."""
        text = "AttributeError: module not found"
        sanitized, warnings = quick_sanitize(text)
        assert sanitized == text
        assert len(warnings) == 0


class TestCalculateConfidenceScore:
    """Tests for confidence score calculation."""

    def test_high_score_clean_input(self) -> None:
        """Test high confidence score for clean input."""
        secret_result = SecretScanResult(
            secrets=[],
            sanitized_text="clean",
            remaining_risk=0.0,
            scan_confidence=1.0,
        )
        pii_result = PIIScanResult(
            pii_items=[],
            sanitized_text="clean",
            remaining_risk=0.0,
            scan_confidence=1.0,
        )
        mre_result = MREResult(
            synthesized_mre="code",
            quality_score=1.0,
            syntax_valid=True,
        )

        score = calculate_confidence_score(secret_result, pii_result, mre_result, llm_used=True)
        assert score >= 0.9

    def test_lower_score_with_risk(self) -> None:
        """Test lower confidence with remaining risk."""
        secret_result = SecretScanResult(
            secrets=[],
            sanitized_text="text",
            remaining_risk=0.5,
            scan_confidence=0.8,
        )
        pii_result = PIIScanResult(
            pii_items=[],
            sanitized_text="text",
            remaining_risk=0.3,
            scan_confidence=0.9,
        )
        mre_result = MREResult(
            synthesized_mre="code",
            quality_score=0.5,
            syntax_valid=False,
        )

        score = calculate_confidence_score(secret_result, pii_result, mre_result, llm_used=False)
        assert score < 0.8

    def test_no_mre(self) -> None:
        """Test score calculation without MRE."""
        secret_result = SecretScanResult(
            secrets=[],
            sanitized_text="clean",
            remaining_risk=0.0,
            scan_confidence=1.0,
        )
        pii_result = PIIScanResult(
            pii_items=[],
            sanitized_text="clean",
            remaining_risk=0.0,
            scan_confidence=1.0,
        )

        score = calculate_confidence_score(secret_result, pii_result, None, llm_used=False)
        # Should still get good score without MRE
        assert score > 0.6

    def test_llm_bonus(self) -> None:
        """Test that LLM usage provides bonus to score."""
        secret_result = SecretScanResult(
            secrets=[],
            sanitized_text="clean",
            remaining_risk=0.0,
            scan_confidence=1.0,
        )
        pii_result = PIIScanResult(
            pii_items=[],
            sanitized_text="clean",
            remaining_risk=0.0,
            scan_confidence=1.0,
        )

        score_without_llm = calculate_confidence_score(
            secret_result, pii_result, None, llm_used=False
        )
        score_with_llm = calculate_confidence_score(
            secret_result, pii_result, None, llm_used=True
        )

        assert score_with_llm > score_without_llm


class TestIntegration:
    """Integration tests for sanitization pipeline."""

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_real_world_error(self) -> None:
        """Test with realistic error submission."""
        result = run_sanitization_pipeline_sync(
            error_message="AttributeError: module 'langchain.tools' has no attribute 'tool'",
            error_context="Trying to use @tool decorator from langchain",
            code_snippet="""
from langchain.tools import tool  # Error here

@tool
def search(query: str) -> str:
    \"\"\"Search for information.\"\"\"
    return f"Results for: {query}"
""",
        )
        assert result.success is True
        assert result.confidence_score > 0.5

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_error_with_mixed_sensitive_data(self) -> None:
        """Test error with various sensitive data types."""
        result = run_sanitization_pipeline_sync(
            error_message="""
Error connecting to database:
- Host: 192.168.1.50
- User: admin@company.local
- Path: /home/developer/app/config.py
""",
        )
        assert result.success is True
        assert "192.168.1.50" not in result.sanitized_error
        assert "admin@company.local" not in result.sanitized_error
        assert "/home/developer" not in result.sanitized_error

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_code_with_credentials(self) -> None:
        """Test code containing credentials is sanitized."""
        result = run_sanitization_pipeline_sync(
            error_message="Connection failed",
            code_snippet="""
import os

API_KEY = "sk-secretkey12345678901234567890123456789012345678"
DATABASE_URL = "postgresql://user:password123@localhost:5432/mydb"

def connect():
    client = Client(api_key=API_KEY)
    return client
""",
        )
        assert result.success is True
        # Secrets should be redacted
        assert "sk-secret" not in result.sanitized_mre
        assert "password123" not in result.sanitized_mre

    @patch("src.services.sanitization.pipeline._get_confidence_threshold", _low_threshold)
    def test_always_succeeds(self) -> None:
        """Test that pipeline sanitizes all data (low threshold)."""
        # Even with lots of sensitive data, should succeed with low threshold
        result = run_sanitization_pipeline_sync(
            error_message="Error with sk-key1 and sk-key2 and ghp_token123",
            error_context="Contact admin@internal.corp at 10.0.0.1",
            code_snippet="""
SECRET = "-----BEGIN PRIVATE KEY-----\\nMIIE...\\n-----END PRIVATE KEY-----"
""",
        )
        assert result.success is True
        # Everything should be sanitized
        assert "sk-key" not in result.sanitized_error
        assert "admin@internal" not in result.sanitized_context
