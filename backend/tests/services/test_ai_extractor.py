"""
Tests for AIExtractor response handling and retry logic. No real Gemini calls.

Covers the robustness logic the earlier bug-fix pass introduced:
- `_extract_text` inspects finish_reason before touching `.text`
- non-retryable failures (MAX_TOKENS / safety) don't waste retries
- `_parse_response` / `_fix_json` recover from messy model output
"""

from unittest.mock import Mock

import pytest

from app.services.ai_extractor import AIExtractor, GeminiAPIError, InvalidResponseError


# ---------------------------------------------------------------------------
# Fake Gemini response objects (mirror the google-generativeai shape)
# ---------------------------------------------------------------------------
class _Finish:
    def __init__(self, name: str):
        self.name = name


class _Part:
    def __init__(self, text: str):
        self.text = text


class _Content:
    def __init__(self, parts):
        self.parts = parts


class _Candidate:
    def __init__(self, text="", finish="STOP"):
        self.finish_reason = _Finish(finish)
        self.content = _Content([_Part(text)] if text else [])


class FakeResponse:
    def __init__(self, text="", finish="STOP", with_candidate=True):
        self.candidates = [_Candidate(text, finish)] if with_candidate else []
        self.prompt_feedback = "n/a"


@pytest.fixture
def extractor(monkeypatch):
    """Build an AIExtractor with a dummy key and a stub cache (no network)."""
    from app.config import get_settings

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    get_settings.cache_clear()
    ext = AIExtractor(cache=Mock())
    yield ext
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# _extract_text
# ---------------------------------------------------------------------------
def test_extract_text_returns_joined_parts():
    resp = FakeResponse(text="hello world", finish="STOP")
    assert AIExtractor._extract_text(resp) == "hello world"


def test_extract_text_raises_non_retryable_on_max_tokens():
    resp = FakeResponse(text="partial", finish="MAX_TOKENS")
    with pytest.raises(GeminiAPIError) as exc:
        AIExtractor._extract_text(resp)
    assert exc.value.retryable is False
    assert "MAX_TOKENS" in str(exc.value)


@pytest.mark.parametrize("reason", ["SAFETY", "RECITATION", "PROHIBITED_CONTENT"])
def test_extract_text_raises_non_retryable_on_block(reason):
    resp = FakeResponse(text="", finish=reason)
    with pytest.raises(GeminiAPIError) as exc:
        AIExtractor._extract_text(resp)
    assert exc.value.retryable is False


def test_extract_text_raises_when_no_candidates():
    resp = FakeResponse(with_candidate=False)
    with pytest.raises(GeminiAPIError) as exc:
        AIExtractor._extract_text(resp)
    assert exc.value.retryable is False


# ---------------------------------------------------------------------------
# _fix_json / _parse_response
# ---------------------------------------------------------------------------
def test_fix_json_removes_trailing_commas(extractor):
    fixed = extractor._fix_json('{"a": 1, "b": 2,}')
    assert fixed == '{"a": 1, "b": 2}'


def test_fix_json_quotes_bare_keys(extractor):
    fixed = extractor._fix_json("{a: 1}")
    assert '"a"' in fixed


def test_parse_response_rejects_non_json(extractor):
    with pytest.raises(InvalidResponseError):
        extractor._parse_response("this is not json at all")


# ---------------------------------------------------------------------------
# _call_gemini retry behavior
# ---------------------------------------------------------------------------
async def test_call_gemini_retries_then_succeeds(extractor, monkeypatch):
    async def _no_sleep(*_a, **_k):
        return None

    monkeypatch.setattr("app.services.ai_extractor.asyncio.sleep", _no_sleep)

    async def _no_rate_limit():
        return None

    monkeypatch.setattr(extractor, "_rate_limit", _no_rate_limit)

    gen = Mock(side_effect=[ValueError("transient"), FakeResponse(text="ok", finish="STOP")])
    extractor.model = Mock(generate_content=gen)

    result = await extractor._call_gemini("prompt", is_flexible=False)
    assert result == "ok"
    assert gen.call_count == 2


async def test_call_gemini_does_not_retry_non_retryable(extractor, monkeypatch):
    async def _no_rate_limit():
        return None

    monkeypatch.setattr(extractor, "_rate_limit", _no_rate_limit)

    gen = Mock(return_value=FakeResponse(text="partial", finish="MAX_TOKENS"))
    extractor.model = Mock(generate_content=gen)

    with pytest.raises(GeminiAPIError) as exc:
        await extractor._call_gemini("prompt", is_flexible=False)
    assert exc.value.retryable is False
    # Non-retryable -> only one API call, no wasted retries.
    assert gen.call_count == 1
