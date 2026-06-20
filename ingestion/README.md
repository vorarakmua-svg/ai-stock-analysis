# Ingestion pipeline

Version-controlled, reproducible data pipeline that produces the per-stock JSON
files the backend consumes (`data/output/json/{TICKER}.json`) plus
`data/output/csv/summary.csv` and a run manifest (`data/output/_manifest.json`).

Sources:
- **SEC EDGAR** `companyfacts` API — fundamentals (annual 10-K figures). Requires a
  descriptive `User-Agent` and respects SEC's ~10 req/s fair-access limit.
- **yfinance** — current market data + company info (kept for now; replace with a
  licensed feed before charging external customers).

## Setup

```bash
pip install -e ingestion[dev]
export INGESTION_SEC_USER_AGENT="Intelligent Investor Pro you@example.com"   # required by SEC
```

## Usage

```bash
python -m ingestion.cli refresh --tickers AAPL,MSFT     # specific tickers
python -m ingestion.cli refresh --all                   # the default universe
python -m ingestion.cli refresh --tickers AAPL --dry-run  # fetch + validate, no writes
```

Writes are **atomic** (temp file + rename) and **idempotent**: re-running with
unchanged source data leaves files untouched (only `collected_at` would differ, so
it is excluded from change detection). The CLI exits non-zero if any ticker failed.

## Tests

```bash
cd ingestion && pytest          # SEC/yfinance are mocked; no network
```

## Design notes

- The output contract lives in `ingestion/schemas.py`; data is validated against it
  **before** writing, so a bad fetch can't corrupt an existing good file.
- Generated data is gitignored; the committed pipeline + ticker universe
  (`ingestion/universe.py`) is the reproducible source of truth.
