"""Google Gemini implementation of LLMProvider using the current google-genai SDK.

Replaces the deprecated google-generativeai package. Encapsulates the response
shape (candidates / finish_reason / usage_metadata / thought parts) so the rest
of the app never touches SDK internals.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from google import genai
from google.genai import types

from app.services.llm.base import (
    LLMBlockedError,
    LLMEmptyError,
    LLMResponse,
    LLMTruncatedError,
)

logger = logging.getLogger(__name__)

_BLOCK_REASONS = {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII"}


class GeminiProvider:
    """LLMProvider backed by Gemini (google-genai)."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for GeminiProvider")
        self._client = genai.Client(api_key=api_key)
        self._model = model
        logger.info("GeminiProvider initialized with model: %s", model)

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
        config_kwargs: dict[str, Any] = {
            "system_instruction": system,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
        }
        if response_json:
            config_kwargs["response_mime_type"] = "application/json"
        # thinking_budget: 0 disables thinking (saves tokens for deterministic
        # extraction); -1 lets the model decide; None leaves the SDK default.
        if thinking_budget is not None:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)

        config = types.GenerateContentConfig(**config_kwargs)

        # generate_content is synchronous/blocking; keep the event loop free.
        response = await asyncio.to_thread(
            self._client.models.generate_content,
            model=self._model,
            contents=user,
            config=config,
        )

        return self._to_llm_response(response)

    def _to_llm_response(self, response: Any) -> LLMResponse:
        """Translate an SDK response into LLMResponse, raising on failure modes."""
        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", 0) or 0
        output_tokens = getattr(usage, "candidates_token_count", 0) or 0
        thinking_tokens = getattr(usage, "thoughts_token_count", 0) or 0
        total_tokens = getattr(usage, "total_token_count", 0) or 0

        candidates = getattr(response, "candidates", None)
        if not candidates:
            feedback = getattr(response, "prompt_feedback", None)
            raise LLMEmptyError(
                f"No candidates in Gemini response (prompt_feedback={feedback})",
                retryable=False,
            )

        candidate = candidates[0]
        finish_reason = getattr(candidate, "finish_reason", None)
        finish_name = getattr(finish_reason, "name", None) or str(finish_reason)

        if finish_name == "MAX_TOKENS":
            raise LLMTruncatedError(
                "Gemini response truncated (finish_reason=MAX_TOKENS). Increase "
                "max_output_tokens / thinking_budget or reduce the input payload."
            )
        if finish_name in _BLOCK_REASONS:
            raise LLMBlockedError(f"Gemini response blocked (finish_reason={finish_name})")

        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        # Skip "thought" parts; collect only answer text.
        text = "".join(
            getattr(p, "text", "") or "" for p in parts if not getattr(p, "thought", False)
        )

        if not text:
            raise LLMEmptyError("Gemini returned an empty completion")

        return LLMResponse(
            text=text,
            model=self._model,
            finish_reason=finish_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            total_tokens=total_tokens,
        )
