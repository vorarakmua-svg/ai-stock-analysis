# Open follow-ups

The "Solid Foundation" phase (P0–P7) is complete and pushed to `master`.
**All foundation follow-ups (#9–#13) are now done.** The next effort is the
commercialization phase (see the plan file). Nothing here is open.

## #12 — Cut caches over to Redis backend ✅ DONE
**What was done:** introduced `app/core/cache_backend.py` with a `CacheBackend`
protocol and two impls — `DiskCacheBackend` (diskcache, the default) and
`RedisCacheBackend` (a sync, namespaced Redis client). `ExtractionCache`,
`ValuationCache`, and `AnalysisCache` were refactored to delegate storage to a
backend selected by `settings.CACHE_BACKEND` (`disk` | `redis`); their public
sync interface is unchanged, so no service call sites changed. `disk` stays the
default. Tests cover both backends + a domain-cache round-trip on a fake Redis.
112 backend tests pass; ruff + mypy clean.

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
3. Verify the baseline: `cd backend && pytest -q` (112 pass) and `cd ingestion && pytest -q` (18 pass).
4. No foundation follow-ups remain — start the commercialization phase from the plan file.

## Done this effort (for reference)
P0 tooling · P1 valuation tests · P2 CI · P3 AI SDK migration · P4 observability ·
P5 ingestion pipeline · P6 Postgres+Redis substrate · P7 arq job queue ·
follow-ups #9 (adapter CAGR), #10 (ruff blocking), #11 (no error leaks),
#12 (Redis cache backend), #13 (mypy clean + CI-blocking).
