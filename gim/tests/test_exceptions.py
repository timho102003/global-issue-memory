"""Tests for custom exception types."""

import pytest

from src.exceptions import (
    GIMError,
    SupabaseError,
    QdrantError,
    EmbeddingError,
    SanitizationError,
    ValidationError,
)


class TestGIMError:
    """Test cases for GIMError base exception."""

    def test_init_with_message_only(self) -> None:
        """Test GIMError with message only."""
        error = GIMError("Test error message")
        assert error.message == "Test error message"
        assert error.details == {}
        assert error.original_error is None
        assert str(error) == "Test error message"

    def test_init_with_details(self) -> None:
        """Test GIMError with details."""
        details = {"key": "value", "count": 5}
        error = GIMError("Test error", details=details)
        assert error.message == "Test error"
        assert error.details == details
        assert "key" in str(error)
        assert "value" in str(error)

    def test_init_with_original_error(self) -> None:
        """Test GIMError wrapping another exception."""
        original = ValueError("Original error")
        error = GIMError("Wrapped error", original_error=original)
        assert error.original_error is original


class TestSupabaseError:
    """Test cases for SupabaseError."""

    def test_init_basic(self) -> None:
        """Test SupabaseError with basic parameters."""
        error = SupabaseError("Insert failed")
        assert error.message == "Insert failed"
        assert error.table is None
        assert error.operation is None

    def test_init_with_table_and_operation(self) -> None:
        """Test SupabaseError with table and operation."""
        error = SupabaseError(
            "Record not found",
            table="master_issues",
            operation="get",
        )
        assert error.table == "master_issues"
        assert error.operation == "get"
        assert error.details["table"] == "master_issues"
        assert error.details["operation"] == "get"

    def test_init_with_all_params(self) -> None:
        """Test SupabaseError with all parameters."""
        original = Exception("DB connection error")
        error = SupabaseError(
            "Connection failed",
            table="users",
            operation="insert",
            details={"extra": "info"},
            original_error=original,
        )
        assert error.table == "users"
        assert error.operation == "insert"
        assert error.details["extra"] == "info"
        assert error.original_error is original


class TestQdrantError:
    """Test cases for QdrantError."""

    def test_init_basic(self) -> None:
        """Test QdrantError with basic parameters."""
        error = QdrantError("Vector search failed")
        assert error.message == "Vector search failed"
        assert error.collection is None
        assert error.operation is None

    def test_init_with_collection_and_operation(self) -> None:
        """Test QdrantError with collection and operation."""
        error = QdrantError(
            "Collection not found",
            collection="gim_issues",
            operation="search",
        )
        assert error.collection == "gim_issues"
        assert error.operation == "search"
        assert error.details["collection"] == "gim_issues"


class TestEmbeddingError:
    """Test cases for EmbeddingError."""

    def test_init_basic(self) -> None:
        """Test EmbeddingError with basic parameters."""
        error = EmbeddingError("Embedding failed")
        assert error.message == "Embedding failed"
        assert error.text_length is None
        assert error.model is None

    def test_init_with_text_length_and_model(self) -> None:
        """Test EmbeddingError with text_length and model."""
        error = EmbeddingError(
            "Text too long",
            text_length=50000,
            model="text-embedding-3-small",
        )
        assert error.text_length == 50000
        assert error.model == "text-embedding-3-small"
        assert error.details["text_length"] == 50000


class TestSanitizationError:
    """Test cases for SanitizationError."""

    def test_init_basic(self) -> None:
        """Test SanitizationError with basic parameters."""
        error = SanitizationError("Sanitization failed")
        assert error.message == "Sanitization failed"
        assert error.stage is None
        assert error.content_type is None

    def test_init_with_stage_and_content_type(self) -> None:
        """Test SanitizationError with stage and content_type."""
        error = SanitizationError(
            "PII detection failed",
            stage="pii_scrubber",
            content_type="error_message",
        )
        assert error.stage == "pii_scrubber"
        assert error.content_type == "error_message"


class TestValidationError:
    """Test cases for ValidationError."""

    def test_init_basic(self) -> None:
        """Test ValidationError with basic parameters."""
        error = ValidationError("Field required")
        assert error.message == "Field required"
        assert error.field is None
        assert error.constraint is None

    def test_init_with_field_and_constraint(self) -> None:
        """Test ValidationError with field and constraint."""
        error = ValidationError(
            "Value too short",
            field="error_message",
            constraint="min_length:10",
        )
        assert error.field == "error_message"
        assert error.constraint == "min_length:10"
        assert error.details["field"] == "error_message"


class TestExceptionHierarchy:
    """Test that exception hierarchy is correct."""

    def test_all_inherit_from_gim_error(self) -> None:
        """Test all custom exceptions inherit from GIMError."""
        assert issubclass(SupabaseError, GIMError)
        assert issubclass(QdrantError, GIMError)
        assert issubclass(EmbeddingError, GIMError)
        assert issubclass(SanitizationError, GIMError)
        assert issubclass(ValidationError, GIMError)

    def test_gim_error_inherits_from_exception(self) -> None:
        """Test GIMError inherits from Exception."""
        assert issubclass(GIMError, Exception)

    def test_can_catch_specific_errors(self) -> None:
        """Test catching specific error types."""
        with pytest.raises(SupabaseError):
            raise SupabaseError("DB error")

        with pytest.raises(QdrantError):
            raise QdrantError("Vector error")

    def test_can_catch_as_gim_error(self) -> None:
        """Test catching any GIM error as base type."""
        with pytest.raises(GIMError):
            raise SupabaseError("DB error")

        with pytest.raises(GIMError):
            raise ValidationError("Invalid input")
