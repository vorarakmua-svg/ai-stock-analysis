"""Provider-agnostic LLM interface, response container, and errors."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Normalized result of a single LLM generation.

    Carries token accounting so callers can record cost/usage regardless of the
    underlying provider (groundwork for per-user metering).
    """

    text: str
    model: str
    finish_reason: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    total_tokens: int = 0


class LLMError(Exception):
    """Base error for LLM generation.

    ``retryable`` lets callers avoid wasting API calls on deterministic failures
    (truncation, safety blocks) while still retrying transient ones.
    """

    def __init__(self, message: str, *, retryable: bool = True):
        self.retryable = retryable
        super().__init__(message)


class LLMTruncatedError(LLMError):
    """Output hit the token ceiling (finish_reason == MAX_TOKENS)."""

    def __init__(self, message: str):
        super().__init__(message, retryable=False)


class LLMBlockedError(LLMError):
    """Response was blocked (safety / recitation / prohibited content)."""

    def __init__(self, message: str):
        super().__init__(message, retryable=False)


class LLMEmptyError(LLMError):
    """Provider returned no usable text but no explicit failure reason."""

    def __init__(self, message: str, *, retryable: bool = True):
        super().__init__(message, retryable=retryable)


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal interface every provider implements."""

    async def generate(
        self,
        *,
        system: str,
        user: str,
        response_json: bool = False,
        max_output_tokens: int = 8192,
        temperature: float = 0.0,
        top_p: float = 0.95,
        top_k: int = 40,
        thinking_budget: int | None = None,
    ) -> LLMResponse:
        """Generate a completion. Raises LLMError (or a subclass) on failure."""
        ...


def record_llm_usage(
    response: LLMResponse,
    *,
    purpose: str,
    ticker: str | None = None,
) -> None:
    """Emit a structured usage record for cost tracking.

    For now this just logs; P6 will persist these rows to Postgres so usage can
    be attributed per user and enforced against plan quotas.
    """
    logger.info(
        "llm_usage purpose=%s ticker=%s model=%s input_tokens=%d "
        "output_tokens=%d thinking_tokens=%d total_tokens=%d finish=%s",
        purpose,
        ticker or "-",
        response.model,
        response.input_tokens,
        response.output_tokens,
        response.thinking_tokens,
        response.total_tokens,
        response.finish_reason,
    )

    # Best-effort metric (never let observability break a request).
    try:
        from app.core.metrics import record_llm_tokens

        record_llm_tokens(
            response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            thinking_tokens=response.thinking_tokens,
        )
    except Exception:  # pragma: no cover - metrics are non-critical
        pass
