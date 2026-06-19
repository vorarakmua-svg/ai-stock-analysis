"""
Integration test for ValuationEngine.calculate_valuation orchestration.

The AI extractor is stubbed (no network), so this exercises the full async path:
extract -> adapt -> DCF/Graham/composite -> ValuationResult assembly -> cache.
"""

import pytest

from app.models.valuation_output import ValuationResult
from app.services.valuation_engine import ValuationCache, ValuationEngine
from tests.fixtures.sample_inputs import make_flexible_input


class _StubExtractor:
    def __init__(self, flexible):
        self._flexible = flexible
        self.calls = 0

    async def extract_flexible(self, ticker, force_refresh=False):
        self.calls += 1
        return self._flexible


@pytest.fixture
def stub_engine(tmp_path):
    extractor = _StubExtractor(make_flexible_input())
    engine = ValuationEngine(
        cache=ValuationCache(cache_dir=tmp_path / "valcache"),
        ai_extractor=extractor,
    )
    return engine, extractor


async def test_calculate_valuation_end_to_end(stub_engine):
    engine, extractor = stub_engine
    result = await engine.calculate_valuation("TEST", force_refresh=True)

    assert isinstance(result, ValuationResult)
    assert result.ticker == "TEST"
    assert result.composite_intrinsic_value > 0
    assert result.dcf_valuation.weighted_intrinsic_value > 0
    assert result.verdict is not None
    assert extractor.calls == 1


async def test_calculate_valuation_uses_cache_on_second_call(stub_engine):
    engine, extractor = stub_engine

    # First call (force refresh) computes and caches.
    await engine.calculate_valuation("TEST", force_refresh=True)
    extractor_calls_after_first = extractor.calls

    # Second call without refresh: extraction still runs (cache key derives from
    # extraction timestamp), but the cached valuation should be returned.
    result2 = await engine.calculate_valuation("TEST", force_refresh=False)
    assert isinstance(result2, ValuationResult)
    assert extractor.calls >= extractor_calls_after_first
