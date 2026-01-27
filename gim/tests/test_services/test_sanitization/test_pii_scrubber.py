"""Tests for PII scrubbing module."""

import pytest

from src.services.sanitization.pii_scrubber import (
    get_pii_summary,
    scrub_pii,
)


class TestScrubPII:
    """Tests for PII scrubbing."""

    def test_scrubs_email(self) -> None:
        """Test email address scrubbing."""
        text = "Contact: john.doe@company.com for support"
        result = scrub_pii(text)
        assert "john.doe@company.com" not in result.sanitized_text
        assert "user@example.com" in result.sanitized_text
        assert "email" in result.pii_types_found

    def test_scrubs_multiple_emails(self) -> None:
        """Test multiple email addresses."""
        text = "Send to alice@corp.com and bob@company.org"
        result = scrub_pii(text)
        assert "alice@corp.com" not in result.sanitized_text
        assert "bob@company.org" not in result.sanitized_text
        assert result.sanitized_text.count("user@example.com") == 2

    def test_scrubs_unix_path(self) -> None:
        """Test Unix home path scrubbing."""
        text = "File not found: /Users/johndoe/project/main.py"
        result = scrub_pii(text)
        assert "/Users/johndoe" not in result.sanitized_text
        assert "/path/to" in result.sanitized_text

    def test_scrubs_linux_path(self) -> None:
        """Test Linux home path scrubbing."""
        text = "Config at /home/alice/config.yml"
        result = scrub_pii(text)
        assert "/home/alice" not in result.sanitized_text
        assert "/path/to" in result.sanitized_text

    def test_scrubs_windows_path(self) -> None:
        """Test Windows user path scrubbing."""
        text = r"Error in C:\Users\JohnDoe\Documents\project\script.py"
        result = scrub_pii(text)
        assert "JohnDoe" not in result.sanitized_text
        assert r"C:\path\to" in result.sanitized_text

    def test_scrubs_ipv4_address(self) -> None:
        """Test IPv4 address scrubbing."""
        text = "Connect to server at 192.168.1.100:8080"
        result = scrub_pii(text)
        assert "192.168.1.100" not in result.sanitized_text
        assert "0.0.0.0" in result.sanitized_text

    def test_scrubs_internal_url(self) -> None:
        """Test internal URL scrubbing."""
        text = "API endpoint: https://internal.company.corp/api/v1"
        result = scrub_pii(text)
        assert "internal.company.corp" not in result.sanitized_text
        assert "api.example.com" in result.sanitized_text

    def test_scrubs_localhost(self) -> None:
        """Test localhost URL scrubbing."""
        text = "Server running at http://localhost:3000"
        result = scrub_pii(text)
        assert "localhost" not in result.sanitized_text
        assert "api.example.com" in result.sanitized_text

    def test_scrubs_phone_number(self) -> None:
        """Test US phone number scrubbing."""
        text = "Call support at (555) 123-4567"
        result = scrub_pii(text)
        assert "555" not in result.sanitized_text
        assert "000-000-0000" in result.sanitized_text

    def test_preserves_clean_text(self) -> None:
        """Test that clean text is preserved."""
        text = "AttributeError: 'NoneType' object has no attribute 'status'"
        result = scrub_pii(text)
        assert result.sanitized_text == text
        assert len(result.pii_items) == 0
        assert result.remaining_risk == 0.0

    def test_empty_text(self) -> None:
        """Test handling of empty text."""
        result = scrub_pii("")
        assert result.sanitized_text == ""
        assert result.scan_confidence == 1.0

    def test_mixed_pii(self) -> None:
        """Test text with multiple PII types."""
        text = """
        Contact john@company.com at 192.168.1.1
        File: /Users/john/project/app.py
        """
        result = scrub_pii(text)
        assert "john@company.com" not in result.sanitized_text
        assert "192.168.1.1" not in result.sanitized_text
        assert "/Users/john" not in result.sanitized_text
        assert len(result.pii_types_found) >= 2


class TestGetPIISummary:
    """Tests for PII summary function."""

    def test_summary_counts(self) -> None:
        """Test that summary counts are correct."""
        text = "Email: a@b.com and c@d.com. IP: 1.2.3.4"
        result = scrub_pii(text)
        summary = get_pii_summary(result)
        assert summary.get("email", 0) == 2
        assert summary.get("ipv4_address", 0) == 1

    def test_empty_summary(self) -> None:
        """Test summary for clean text."""
        text = "No PII here"
        result = scrub_pii(text)
        summary = get_pii_summary(result)
        assert len(summary) == 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_email_in_code(self) -> None:
        """Test email detection in code context."""
        text = 'user_email = "test@example.org"'
        result = scrub_pii(text)
        assert "test@example.org" not in result.sanitized_text

    def test_preserves_example_domains(self) -> None:
        """Test that example.com domains are preserved."""
        text = "See documentation at https://api.example.com/docs"
        result = scrub_pii(text)
        # example.com should not be treated as internal
        assert "api.example.com" in result.sanitized_text

    def test_handles_special_characters(self) -> None:
        """Test handling of special characters in text."""
        text = "Error: /Users/john's/path/to/file.py"
        result = scrub_pii(text)
        # Should handle the apostrophe correctly
        assert "/Users/john" not in result.sanitized_text
