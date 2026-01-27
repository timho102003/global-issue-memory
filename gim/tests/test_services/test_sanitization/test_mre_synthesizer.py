"""Tests for MRE synthesizer module."""

import pytest

from src.services.sanitization.mre_synthesizer import (
    MREResult,
    synthesize_mre,
)


class TestSynthesizeMRE:
    """Tests for MRE synthesis."""

    def test_basic_synthesis(self) -> None:
        """Test basic MRE synthesis."""
        code = """
from mycompany.services import UserService

def get_user_data(user_id):
    service = UserService()
    return service.fetch_user(user_id)
"""
        result = synthesize_mre(code)
        assert result.synthesized_mre != ""
        assert result.quality_score > 0

    def test_replaces_domain_names(self) -> None:
        """Test that domain-specific names are replaced."""
        code = """
class CustomerOrderProcessor:
    def process_customer_order(self, order_id):
        customer = self.get_customer(order_id)
        return customer
"""
        result = synthesize_mre(code)
        assert "CustomerOrderProcessor" not in result.synthesized_mre
        assert "process_customer_order" not in result.synthesized_mre
        assert len(result.names_replaced) > 0

    def test_preserves_imports(self) -> None:
        """Test that import statements are preserved."""
        code = """
import json
from typing import Dict

def parse_data(data: str) -> Dict:
    return json.loads(data)
"""
        result = synthesize_mre(code)
        assert "import json" in result.synthesized_mre
        assert "from typing import Dict" in result.synthesized_mre
        assert len(result.imports_kept) == 2

    def test_adds_error_markers(self) -> None:
        """Test that error markers are added."""
        code = """
def process():
    raise ValueError("Something went wrong")
"""
        result = synthesize_mre(code, error_message="ValueError occurred")
        # Should have some indication of error location
        assert "ERROR" in result.synthesized_mre or "error" in result.synthesized_mre.lower()

    def test_validates_python_syntax(self) -> None:
        """Test syntax validation for Python code."""
        # Valid Python
        valid_code = """
def hello():
    return "world"
"""
        result = synthesize_mre(valid_code)
        assert result.syntax_valid is True

    def test_handles_invalid_syntax(self) -> None:
        """Test handling of invalid Python syntax."""
        invalid_code = """
def broken(
    # Missing closing paren
    return x
"""
        result = synthesize_mre(invalid_code)
        # Should still process but mark as invalid
        assert result.syntax_valid is False
        assert len(result.warnings) > 0

    def test_trims_long_code(self) -> None:
        """Test that long code is trimmed."""
        # Create code with many lines
        lines = [f"x{i} = {i}" for i in range(100)]
        code = "\n".join(lines)

        result = synthesize_mre(code, max_lines=50)
        assert result.line_count <= 51  # 50 + possible truncation message

    def test_empty_code(self) -> None:
        """Test handling of empty code."""
        result = synthesize_mre("")
        assert result.synthesized_mre == ""
        assert result.quality_score == 0.0
        assert "Empty code" in str(result.warnings)

    def test_quality_score_calculation(self) -> None:
        """Test that quality score is calculated correctly."""
        # Good MRE should have high score
        good_code = """
import requests

def fetch_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError("Failed to fetch")  # ERROR
    return response.json()
"""
        result = synthesize_mre(good_code)
        assert result.quality_score > 0.5

    def test_handles_non_python_code(self) -> None:
        """Test handling of non-Python code."""
        js_code = """
const fetchUser = async (userId) => {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
};
"""
        result = synthesize_mre(js_code)
        # Should process but with warning about language detection
        assert result.synthesized_mre != ""


class TestNameReplacement:
    """Tests for name replacement logic."""

    def test_replaces_service_classes(self) -> None:
        """Test replacement of service class names."""
        code = "class PaymentService:\n    pass"
        result = synthesize_mre(code)
        assert "PaymentService" not in result.synthesized_mre
        assert "Payment" not in result.synthesized_mre

    def test_replaces_handler_classes(self) -> None:
        """Test replacement of handler class names."""
        code = "class OrderHandler:\n    pass"
        result = synthesize_mre(code)
        assert "OrderHandler" not in result.synthesized_mre

    def test_replaces_function_names(self) -> None:
        """Test replacement of domain function names."""
        code = """
def process_payment(payment_id):
    return validate_payment(payment_id)
"""
        result = synthesize_mre(code)
        assert "process_payment" not in result.synthesized_mre
        assert "validate_payment" not in result.synthesized_mre

    def test_preserves_python_keywords(self) -> None:
        """Test that Python keywords are preserved."""
        code = """
def test():
    if True:
        return None
    else:
        pass
"""
        result = synthesize_mre(code)
        assert "if" in result.synthesized_mre
        assert "return" in result.synthesized_mre


class TestLanguageDetection:
    """Tests for language detection."""

    def test_detects_python(self) -> None:
        """Test Python detection."""
        code = """
def hello():
    print("world")

class MyClass:
    pass
"""
        result = synthesize_mre(code)
        # Python-specific processing should occur
        assert result.syntax_valid is True

    def test_detects_javascript(self) -> None:
        """Test JavaScript detection."""
        code = """
const hello = () => {
    console.log("world");
};

async function fetchData() {
    return await fetch(url);
}
"""
        result = synthesize_mre(code)
        # Should still process
        assert result.synthesized_mre != ""
