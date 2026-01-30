"""Sanitization pipeline for privacy-safe issue processing."""

try:
    from src.services.sanitization.code_synthesizer import (  # noqa: F401
        CodeSynthesisResult,
        run_code_synthesis,
    )
except ImportError:
    pass
