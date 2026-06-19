"""
Tests for AIExtractor retry/parse logic with a fake LLM provider (no network).

Since P3, the SDK-specific finish_reason handling lives in the provider
(see test_gemini_provider.py); here we verify the extractor's orchestration:
- non-retryable provider failures (MAX_TOKENS / safety) are not retried
- transient failures are retried then succeed
- request params (JSON mode, token ceiling, thinking budget) are passed through
- `_parse_response` / `_fix_json` recover from messy model output
"""

from unittest.mock import Mock

import pytest

from app.services.ai_extractor import AIExtractor, GeminiAPIError, InvalidResponseError
from app.services.llm import LLMError, LLMResponse, LLMTruncatedError


class FakeProvider:
    """Returns queued LLMResponses or raises queued exceptions, in order."""

    def __init__(self, results):
        self._results = list(results)
        self.calls = 0
        self.last_kwargs = None

    async def generate(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        result = self._results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def _ok(text="{}"):
    return LLMResponse(text=text, model="fake", finish_reason="STOP")


@pytest.fixture
def make_extractor(monkeypatch):
    """Factory building an AIExtractor with a dummy key and injected provider."""
    from app.config import get_settings

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    get_settings.cache_clear()

    async def _no_sleep(*_a, **_k):
        return None

    monkeypatch.setattr("app.services.ai_extractor.asyncio.sleep", _no_sleep)

    def _make(provider):
        ext = AIExtractor(cache=Mock(), provider=provider)

        async def _no_rate_limit():
            return None

        ext._rate_limit = _no_rate_limit  # type: ignore[method-assign]
        return ext

    yield _make
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# _call_gemini retry behavior
# ---------------------------------------------------------------------------
async def test_call_retries_then_succeeds(make_extractor):
    provider = FakeProvider([LLMError("transient", retryable=True), _ok("ok")])
    ext = make_extractor(provider)
    result = await ext._call_gemini("prompt", is_flexible=False)
    assert result == "ok"
    assert provider.calls == 2


async def test_call_does_not_retry_non_retryable(make_extractor):
    provider = FakeProvider([LLMTruncatedError("truncated")])
    ext = make_extractor(provider)
    with pytest.raises(GeminiAPIError) as exc:
        await ext._call_gemini("prompt", is_flexible=False)
    assert exc.value.retryable is False
    assert provider.calls == 1  # no wasted retries


async def test_call_passes_expected_request_params(make_extractor):
    provider = FakeProvider([_ok()])
    ext = make_extractor(provider)
    await ext._call_gemini("prompt", is_flexible=True)
    kwargs = provider.last_kwargs
    assert kwargs["response_json"] is True
    assert kwargs["max_output_tokens"] == AIExtractor.MAX_OUTPUT_TOKENS
    assert kwargs["temperature"] == 0.0
    # Default extraction thinking budget is 0 (disabled).
    assert kwargs["thinking_budget"] == 0


# ---------------------------------------------------------------------------
# _fix_json / _parse_response
# ---------------------------------------------------------------------------
def test_fix_json_removes_trailing_commas(make_extractor):
    ext = make_extractor(FakeProvider([]))
    assert ext._fix_json('{"a": 1, "b": 2,}') == '{"a": 1, "b": 2}'


def test_fix_json_quotes_bare_keys(make_extractor):
    ext = make_extractor(FakeProvider([]))
    assert '"a"' in ext._fix_json("{a: 1}")


def test_parse_response_rejects_non_json(make_extractor):
    ext = make_extractor(FakeProvider([]))
    with pytest.raises(InvalidResponseError):
        ext._parse_response("this is not json at all")
