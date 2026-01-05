# Role: Senior Data Engineer

**Mission:** Build the Data Ingestion Engine for "ValueInvestAI".

---

## Context

We need to fetch 30 years of financial data for US and Thai stocks from external APIs and store them efficiently in our PostgreSQL database.

**Reference Document:** Use `PROJECT_BLUEPRINT.md` (Section 2: Tech Stack and Section 4: Data Engineering & Normalization).

---

## Tasks

### 1. Provider Interface
Implement the `AbstractDataProvider` class in `backend/app/data_providers/base.py`:
- Define abstract methods for:
  - `get_income_statement(ticker, years)` - Returns list of FinancialStatement
  - `get_balance_sheet(ticker, years)` - Returns list of BalanceSheet
  - `get_cash_flow(ticker, years)` - Returns list of CashFlowStatement
  - `get_stock_price(ticker, start_date, end_date)` - Returns list of price dicts
  - `normalize_ticker(ticker, market)` - Converts to provider format

### 2. EOD Historical Data Implementation
Create `EODHistoricalDataProvider` class in `backend/app/data_providers/eod.py`:
- Implement all abstract methods using httpx async client
- Handle API authentication via environment variable `EOD_API_KEY`
- Parse and normalize response data to match our Pydantic models

**Critical Constraint - Ticker Normalization:**
- If input is `PTT`, convert to `PTT.BK` for Thai stocks
- If input is `AAPL`, use as-is for US stocks
- Implement auto-detection of market from ticker format

### 3. Ticker Resolver
Create `TickerResolver` in `backend/app/data_providers/ticker_resolver.py`:
- `detect_market(ticker)` - Returns "US" or "SET"
- `normalize(ticker, provider)` - Converts to provider-specific format
- `to_display(ticker)` - Returns (base_ticker, market) tuple

### 4. Caching Logic
Implement the "Fetch-Once-Store-Forever" pattern in `backend/app/services/data_cache.py`:

**Logic:**
- Check database first before any API call
- If `fiscal_year < current_year - 1`, save to DB and NEVER fetch again
- For current/recent years, allow periodic refresh
- Log all API fetches for cost tracking

```python
class DataCacheService:
    async def get_financial_data(self, ticker, data_type, fiscal_year):
        # 1. Check DB first
        # 2. If missing and historical, fetch once and save
        # 3. If missing and recent, fetch and save with refresh flag

    async def bulk_load_history(self, ticker, years=30):
        # Efficiently load 30 years, only fetching missing years
```

### 5. CLI Tool
Create a script `backend/scripts/ingest.py` that can be run as:
```bash
python ingest.py --ticker PTT.BK --years 30
python ingest.py --ticker AAPL --years 30 --force-refresh
```

Options:
- `--ticker` - Stock ticker to fetch
- `--years` - Number of years of history (default: 30)
- `--force-refresh` - Re-fetch even cached data
- `--data-type` - Specific type (income, balance, cashflow, all)

---

## Directory Structure to Create

```
backend/app/
├── data_providers/
│   ├── __init__.py
│   ├── base.py              # AbstractDataProvider
│   ├── eod.py               # EOD Historical Data implementation
│   ├── fmp.py               # (Optional) Financial Modeling Prep
│   └── ticker_resolver.py   # Ticker normalization
├── services/
│   ├── __init__.py
│   ├── data_cache.py        # Fetch-once-store-forever logic
│   └── currency.py          # Currency handling (from blueprint)
└── scripts/
    └── ingest.py            # CLI ingestion tool
```

---

## Currency Handling Constraint

**Critical:** Handle currency carefully:
- Thai stocks (`.BK` suffix) return data in THB
- US stocks return data in USD
- Store the `currency` code in the `companies` table
- All financial values should be stored in their native currency
- Currency conversion is handled at display time, not storage time

---

## Expected Output

After running the ingestion script:
1. Company record created in `companies` table with correct market/currency
2. 30 years of income statements in `income_statements` table
3. 30 years of balance sheets in `balance_sheets` table
4. 30 years of cash flow statements in `cash_flow_statements` table
5. Fetch logs in `data_fetch_logs` table for cost tracking

---

## API Rate Limiting

- EOD API has rate limits; implement exponential backoff
- Use Redis for rate limiting tracking
- Log all API calls with response size for cost analysis
