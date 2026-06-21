# Open follow-ups

The "Solid Foundation" phase (P0–P7) is complete and pushed to `master`.
These are the remaining quality items, deferred deliberately. Pick up here.

## #12 — Cut caches over to Redis backend
**Why:** P6 added the Redis client + `RedisJSONCache` + `CACHE_BACKEND` setting, but
the existing caches still run on local diskcache, so multiple app instances don't
share a cache (blocks horizontal scaling and inflates LLM cost across replicas).

**What:** reimplement `ExtractionCache` (`backend/app/core/cache_manager.py`),
`ValuationCache` (`backend/app/services/valuation_engine.py`), and `AnalysisCache`
(`backend/app/services/ai_analyst.py`) behind one shared interface selected by
`settings.CACHE_BACKEND` (`disk` | `redis`). The Redis path is async, so the
`.get()/.set()` call sites in the (already-async) services become `await`ed.
Add tests against a fake Redis (see `tests/db/test_persistence.py::FakeRedis`).
Keep `disk` as the default so local dev is unchanged.

**Risk:** widest change — touches the cache call-sites across all three services.
Do it in isolation with the suite green before/after.

## #13 — Resolve mypy errors, make mypy CI-blocking ✅ DONE
**Why:** ruff was blocking in CI; mypy was still informational (~13 errors).

**What was done:** introduced `ValuationInputProtocol` (a read-only `Protocol`)
plus `HistoricalFinancialsLike` in `models/valuation_input.py` describing the
valuation-input interface that both `StandardizedValuationInput` and
`FlexibleInputAdapter` satisfy; retyped every `ValuationEngine` method that
consumed `input_data` against it, clearing the adapter `arg-type` errors. Fixed
the remaining no-any-return / missing-annotation / var-annotated errors in
`valuation_engine.py`, `config.py`, `stock.py`, and `data_loader.py`. The
slowapi handler in `main.py` was not flagged by mypy 1.14.1, so no change was
needed there. Dropped `continue-on-error` from the mypy step in
`.github/workflows/ci.yml` and restored mypy in `.pre-commit-config.yaml` as a
`local`/`system` hook that mirrors CI (`cd backend && mypy app`), so the
project's own env supplies runtime deps (redis et al.) and the pyproject config.
`cd backend && mypy app` → "Success: no issues found in 54 source files";
105 backend tests still pass.

## How to resume in a fresh session
1. `git -C <repo> pull` — all foundation work is on `master`.
2. Read this file + `C:\Users\vorar\.claude\plans\what-should-be-add-hashed-marshmallow.md`
   (the full plan, incl. the later commercialization phase).
3. Verify the baseline: `cd backend && pytest -q` (105 pass) and `cd ingestion && pytest -q` (18 pass).
4. #12 is the only open follow-up — work it on a branch.

## Done this effort (for reference)
P0 tooling · P1 valuation tests · P2 CI · P3 AI SDK migration · P4 observability ·
P5 ingestion pipeline · P6 Postgres+Redis substrate · P7 arq job queue ·
follow-ups #9 (adapter CAGR), #10 (ruff blocking), #11 (no error leaks),
#13 (mypy clean + CI-blocking).
