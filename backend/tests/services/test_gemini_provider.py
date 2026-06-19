"""
Tests for GeminiProvider._to_llm_response — the SDK response translation and
failure-mode mapping. Built via __new__ so no real google-genai client is created.
"""

import pytest

from app.services.llm import LLMBlockedError, LLMEmptyError, LLMTruncatedError
from app.services.llm.gemini_provider import GeminiProvider


# --- Fake google-genai response shape --------------------------------------
class _Finish:
    def __init__(self, name):
        self.name = name


class _Part:
    def __init__(self, text="", thought=False):
        self.text = text
        self.thought = thought


class _Content:
    def __init__(self, parts):
        self.parts = parts


class _Candidate:
    def __init__(self, parts, finish="STOP"):
        self.finish_reason = _Finish(finish)
        self.content = _Content(parts)


class _Usage:
    def __init__(self, prompt=10, candidates=20, thoughts=5, total=35):
        self.prompt_token_count = prompt
        self.candidates_token_count = candidates
        self.thoughts_token_count = thoughts
        self.total_token_count = total


class FakeSDKResponse:
    def __init__(self, parts=None, finish="STOP", with_candidate=True, usage=True):
        self.candidates = [_Candidate(parts or [], finish)] if with_candidate else []
        self.usage_metadata = _Usage() if usage else None
        self.prompt_feedback = "n/a"


def _provider():
    p = GeminiProvider.__new__(GeminiProvider)
    p._model = "gemini-2.5-flash"
    return p


def test_translates_successful_response_with_tokens():
    resp = FakeSDKResponse(parts=[_Part("hello")], finish="STOP")
    out = _provider()._to_llm_response(resp)
    assert out.text == "hello"
    assert out.finish_reason == "STOP"
    assert out.input_tokens == 10
    assert out.output_tokens == 20
    assert out.thinking_tokens == 5
    assert out.total_tokens == 35
    assert out.model == "gemini-2.5-flash"


def test_skips_thought_parts():
    resp = FakeSDKResponse(
        parts=[_Part("thinking...", thought=True), _Part("answer")],
        finish="STOP",
    )
    assert _provider()._to_llm_response(resp).text == "answer"


def test_max_tokens_raises_non_retryable_truncated():
    resp = FakeSDKResponse(parts=[_Part("partial")], finish="MAX_TOKENS")
    with pytest.raises(LLMTruncatedError) as exc:
        _provider()._to_llm_response(resp)
    assert exc.value.retryable is False


@pytest.mark.parametrize("reason", ["SAFETY", "RECITATION", "PROHIBITED_CONTENT"])
def test_blocked_finish_reason_raises(reason):
    resp = FakeSDKResponse(parts=[], finish=reason)
    with pytest.raises(LLMBlockedError) as exc:
        _provider()._to_llm_response(resp)
    assert exc.value.retryable is False


def test_no_candidates_raises_empty():
    resp = FakeSDKResponse(with_candidate=False)
    with pytest.raises(LLMEmptyError):
        _provider()._to_llm_response(resp)


def test_empty_text_raises_empty():
    resp = FakeSDKResponse(parts=[_Part("")], finish="STOP")
    with pytest.raises(LLMEmptyError):
        _provider()._to_llm_response(resp)
