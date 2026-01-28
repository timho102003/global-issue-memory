"""Custom exception types for GIM.

This module defines a hierarchy of exceptions for different error scenarios
in the GIM (Global Issue Memory) system. Using specific exception types
enables more precise error handling and better error messages.
"""

from typing import Any, Dict, Optional


class GIMError(Exception):
    """Base exception for all GIM errors.

    Attributes:
        message: Human-readable error message.
        details: Additional error details as a dictionary.
        original_error: The original exception that caused this error.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize GIMError.

        Args:
            message: Human-readable error message.
            details: Additional error details as a dictionary.
            original_error: The original exception that caused this error.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error

    def __str__(self) -> str:
        """Return string representation of the error.

        Returns:
            str: Error message with optional details.
        """
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class SupabaseError(GIMError):
    """Exception for Supabase database operation errors.

    Raised when database operations fail, including connection issues,
    query errors, and constraint violations.

    Attributes:
        table: The table involved in the operation.
        operation: The operation that failed (insert, update, delete, query).
    """

    def __init__(
        self,
        message: str,
        table: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize SupabaseError.

        Args:
            message: Human-readable error message.
            table: The table involved in the operation.
            operation: The operation that failed.
            details: Additional error details.
            original_error: The original exception.
        """
        error_details = details or {}
        if table:
            error_details["table"] = table
        if operation:
            error_details["operation"] = operation
        super().__init__(message, error_details, original_error)
        self.table = table
        self.operation = operation


class QdrantError(GIMError):
    """Exception for Qdrant vector database errors.

    Raised when vector operations fail, including indexing,
    searching, and collection management.

    Attributes:
        collection: The collection involved in the operation.
        operation: The operation that failed (upsert, search, delete).
    """

    def __init__(
        self,
        message: str,
        collection: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize QdrantError.

        Args:
            message: Human-readable error message.
            collection: The collection involved in the operation.
            operation: The operation that failed.
            details: Additional error details.
            original_error: The original exception.
        """
        error_details = details or {}
        if collection:
            error_details["collection"] = collection
        if operation:
            error_details["operation"] = operation
        super().__init__(message, error_details, original_error)
        self.collection = collection
        self.operation = operation


class EmbeddingError(GIMError):
    """Exception for embedding generation errors.

    Raised when embedding operations fail, including API errors
    and invalid input handling.

    Attributes:
        text_length: Length of the text that failed to embed.
        model: The embedding model being used.
    """

    def __init__(
        self,
        message: str,
        text_length: Optional[int] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize EmbeddingError.

        Args:
            message: Human-readable error message.
            text_length: Length of the text that failed to embed.
            model: The embedding model being used.
            details: Additional error details.
            original_error: The original exception.
        """
        error_details = details or {}
        if text_length is not None:
            error_details["text_length"] = text_length
        if model:
            error_details["model"] = model
        super().__init__(message, error_details, original_error)
        self.text_length = text_length
        self.model = model


class SanitizationError(GIMError):
    """Exception for content sanitization errors.

    Raised when sanitization operations fail, including PII detection,
    secret detection, and LLM sanitization.

    Attributes:
        stage: The sanitization stage that failed.
        content_type: Type of content being sanitized.
    """

    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        content_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize SanitizationError.

        Args:
            message: Human-readable error message.
            stage: The sanitization stage that failed.
            content_type: Type of content being sanitized.
            details: Additional error details.
            original_error: The original exception.
        """
        error_details = details or {}
        if stage:
            error_details["stage"] = stage
        if content_type:
            error_details["content_type"] = content_type
        super().__init__(message, error_details, original_error)
        self.stage = stage
        self.content_type = content_type


class ValidationError(GIMError):
    """Exception for input validation errors.

    Raised when input validation fails, including missing required fields,
    invalid formats, and constraint violations.

    Attributes:
        field: The field that failed validation.
        constraint: The constraint that was violated.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        constraint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ) -> None:
        """Initialize ValidationError.

        Args:
            message: Human-readable error message.
            field: The field that failed validation.
            constraint: The constraint that was violated.
            details: Additional error details.
            original_error: The original exception.
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if constraint:
            error_details["constraint"] = constraint
        super().__init__(message, error_details, original_error)
        self.field = field
        self.constraint = constraint
