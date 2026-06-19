"""LLM provider abstraction.

Decouples the rest of the app from any single SDK/vendor. Services depend on the
``LLMProvider`` protocol and ``LLMResponse``; the concrete Gemini implementation
lives in ``gemini_provider`` and is selected by ``get_llm_provider()``.
"""

from app.services.llm.base import (
    LLMBlockedError,
    LLMEmptyError,
    LLMError,
    LLMProvider,
    LLMResponse,
    LLMTruncatedError,
    record_llm_usage,
)
from app.services.llm.factory import get_llm_provider

__all__ = [
    "LLMBlockedError",
    "LLMEmptyError",
    "LLMError",
    "LLMProvider",
    "LLMResponse",
    "LLMTruncatedError",
    "get_llm_provider",
    "record_llm_usage",
]
