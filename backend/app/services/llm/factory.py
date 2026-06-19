"""Provider selection / singleton wiring."""

from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.services.llm.base import LLMProvider


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider singleton.

    Selected via the ``LLM_PROVIDER`` setting so a future swap (or a fake in
    tests) requires no changes at call sites.
    """
    settings = get_settings()
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        from app.services.llm.gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=settings.GOOGLE_API_KEY,
            model=settings.GEMINI_MODEL_NAME,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER!r}")
