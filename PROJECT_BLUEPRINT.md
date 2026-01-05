# ValueInvestAI - Project Blueprint
## A Professional Stock Analysis Platform for Value Investors

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Tech Stack Strategy](#2-tech-stack-strategy)
3. [System Architecture](#3-system-architecture)
4. [Data Engineering & Normalization](#4-data-engineering--normalization)
5. [Database Design](#5-database-design)
6. [Financial Modeling Engine](#6-financial-modeling-engine)
7. [Buffett AI Integration](#7-buffett-ai-integration)
8. [API Design](#8-api-design)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. Executive Summary

**ValueInvestAI** is a web-based stock analysis platform designed for value investors. It provides:
- 30 years of financial history for US (NYSE/NASDAQ) and Thai (SET) stocks
- Automated valuation models (DCF, Graham Number, Peter Lynch Fair Value)
- AI-powered investment analysis using Warren Buffett's principles

**Target Markets:**
- USA: NYSE, NASDAQ (tickers: `AAPL`, `MSFT`, `GOOGL`)
- Thailand: SET (tickers: `PTT.BK`, `CPALL.BK`, `AOT.BK`)

---

## 2. Tech Stack Strategy

### 2.1 Backend: Python + FastAPI

**Justification:**
- `pandas` / `numpy` for efficient financial calculations
- `google-generativeai` SDK for Gemini Pro integration
- FastAPI provides async performance and auto-generated OpenAPI docs
- Type hints with Pydantic for data validation

**Key Dependencies:**
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
asyncpg==0.29.0
pandas==2.2.0
numpy==1.26.3
google-generativeai==0.3.2
httpx==0.26.0
python-dotenv==1.0.0
alembic==1.13.1
```

### 2.2 Frontend: Next.js 14 + TypeScript + Tailwind CSS

**Justification:**
- Server-side rendering for SEO and fast initial load
- TypeScript for type safety across financial data structures
- Tailwind for rapid UI development
- App Router for modern React patterns

**Key Dependencies:**
```json
{
  "next": "14.1.0",
  "react": "18.2.0",
  "typescript": "5.3.3",
  "tailwindcss": "3.4.1",
  "recharts": "2.10.4",
  "@tanstack/react-query": "5.17.0",
  "zustand": "4.5.0",
  "axios": "1.6.5"
}
```

### 2.3 Database: PostgreSQL 16

**Justification:**
- JSONB support for flexible financial data storage
- Window functions for time-series analysis
- Partitioning support for 30 years of data
- Excellent performance with proper indexing

### 2.4 Infrastructure: Docker + Docker Compose

**Development Stack:**
```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
  postgres:
    image: postgres:16-alpine
    volumes: [postgres_data:/var/lib/postgresql/data]
  redis:
    image: redis:7-alpine  # For API rate limiting & caching
```

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Stock Search│  │  Dashboard  │  │   Buffett AI Analysis   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Data Ingestion│  │ Valuation   │  │   AI Analysis Layer   │  │
│  │    Service   │  │   Engine    │  │    (Gemini Pro)       │  │
│  └──────┬───────┘  └──────┬───────┘  └───────────┬───────────┘  │
│         │                 │                      │               │
│  ┌──────▼─────────────────▼──────────────────────▼───────────┐  │
│  │              Financial Math Engine (pandas/numpy)          │  │
│  │   DCFCalculator │ MoatAnalysis │ FinancialHealth          │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   PostgreSQL    │  │     Redis       │  │  External APIs  │  │
│  │  (Historical)   │  │   (Cache)       │  │  (EOD/FMP)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Engineering & Normalization

### 4.1 Abstract Data Provider Pattern

```python
# backend/app/data_providers/base.py
from abc import ABC, abstractmethod
from typing import Optional
from datetime import date
from pydantic import BaseModel

class FinancialStatement(BaseModel):
    fiscal_year: int
    fiscal_period: str  # "FY", "Q1", "Q2", "Q3", "Q4"
    revenue: float
    gross_profit: float
    operating_income: float
    net_income: float
    eps: float
    shares_outstanding: float

class BalanceSheet(BaseModel):
    fiscal_year: int
    total_assets: float
    total_liabilities: float
    total_equity: float
    cash_and_equivalents: float
    total_debt: float
    working_capital: float

class CashFlowStatement(BaseModel):
    fiscal_year: int
    operating_cash_flow: float
    capital_expenditure: float
    free_cash_flow: float
    dividends_paid: float

class AbstractDataProvider(ABC):
    """Base class for all financial data providers."""

    @abstractmethod
    async def get_income_statement(
        self, ticker: str, years: int = 30
    ) -> list[FinancialStatement]:
        pass

    @abstractmethod
    async def get_balance_sheet(
        self, ticker: str, years: int = 30
    ) -> list[BalanceSheet]:
        pass

    @abstractmethod
    async def get_cash_flow(
        self, ticker: str, years: int = 30
    ) -> list[CashFlowStatement]:
        pass

    @abstractmethod
    async def get_stock_price(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[dict]:
        pass

    @abstractmethod
    def normalize_ticker(self, ticker: str, market: str) -> str:
        """Convert user ticker to provider-specific format."""
        pass
```

### 4.2 Ticker Normalization Strategy

```python
# backend/app/data_providers/ticker_resolver.py

class TickerResolver:
    """Handles ticker format differences between markets and providers."""

    MARKET_SUFFIXES = {
        "US": "",           # AAPL, MSFT
        "SET": ".BK",       # PTT.BK, CPALL.BK
    }

    PROVIDER_FORMATS = {
        "eod": {
            "US": "{ticker}.US",      # AAPL.US
            "SET": "{ticker}.BK",     # PTT.BK
        },
        "fmp": {
            "US": "{ticker}",         # AAPL
            "SET": "{ticker}.BK",     # PTT.BK
        }
    }

    @classmethod
    def detect_market(cls, ticker: str) -> str:
        """Auto-detect market from ticker format."""
        if ticker.endswith(".BK"):
            return "SET"
        return "US"

    @classmethod
    def normalize(cls, ticker: str, provider: str) -> str:
        """Convert to provider-specific format."""
        market = cls.detect_market(ticker)
        base_ticker = ticker.replace(".BK", "").replace(".US", "")
        template = cls.PROVIDER_FORMATS[provider][market]
        return template.format(ticker=base_ticker)

    @classmethod
    def to_display(cls, ticker: str) -> tuple[str, str]:
        """Return (display_ticker, market) for UI."""
        market = cls.detect_market(ticker)
        base = ticker.replace(".BK", "").replace(".US", "")
        return base, market
```

### 4.3 Currency Handling

```python
# backend/app/services/currency.py

from enum import Enum
from decimal import Decimal
import httpx

class Currency(str, Enum):
    USD = "USD"
    THB = "THB"

class CurrencyService:
    """Handles multi-currency display and conversion."""

    MARKET_CURRENCIES = {
        "US": Currency.USD,
        "SET": Currency.THB,
    }

    # Cache exchange rates (update daily)
    _rates_cache: dict[str, Decimal] = {}

    @classmethod
    async def get_exchange_rate(cls, from_curr: Currency, to_curr: Currency) -> Decimal:
        """Fetch current exchange rate."""
        if from_curr == to_curr:
            return Decimal("1.0")

        cache_key = f"{from_curr}_{to_curr}"
        if cache_key in cls._rates_cache:
            return cls._rates_cache[cache_key]

        # Fetch from exchange rate API
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
            )
            data = resp.json()
            rate = Decimal(str(data["rates"][to_curr]))
            cls._rates_cache[cache_key] = rate
            return rate

    @classmethod
    def format_currency(cls, value: float, currency: Currency) -> str:
        """Format number with currency symbol."""
        if currency == Currency.USD:
            return f"${value:,.2f}"
        elif currency == Currency.THB:
            return f"฿{value:,.2f}"
        return f"{value:,.2f}"

    @classmethod
    def get_display_currency(cls, market: str) -> Currency:
        """Get native currency for market."""
        return cls.MARKET_CURRENCIES.get(market, Currency.USD)
```

### 4.4 Caching Strategy: "Fetch-Once-Store-Forever"

**Principle:** Historical financial data doesn't change. Once we fetch FY2020 data, it's permanent.

```python
# backend/app/services/data_cache.py

from datetime import datetime, date
from sqlalchemy import select
from app.models import FinancialData, DataFetchLog

class DataCacheService:
    """Implements fetch-once-store-forever for historical data."""

    def __init__(self, db_session, data_provider):
        self.db = db_session
        self.provider = data_provider

    async def get_financial_data(
        self,
        ticker: str,
        data_type: str,  # "income", "balance", "cashflow"
        fiscal_year: int
    ) -> dict | None:
        """
        Check DB first, fetch from API only if missing.
        Historical years are NEVER re-fetched.
        """
        # Step 1: Check database
        existing = await self.db.execute(
            select(FinancialData).where(
                FinancialData.ticker == ticker,
                FinancialData.data_type == data_type,
                FinancialData.fiscal_year == fiscal_year
            )
        )
        record = existing.scalar_one_or_none()

        if record:
            return record.data  # Return cached data

        # Step 2: Determine if we should fetch
        current_year = datetime.now().year

        # Historical data (older than current year - 1): fetch once
        # Current/recent data: may need refresh
        is_historical = fiscal_year < (current_year - 1)

        # Step 3: Fetch from provider
        data = await self._fetch_from_provider(ticker, data_type, fiscal_year)

        if data:
            # Store in database
            new_record = FinancialData(
                ticker=ticker,
                data_type=data_type,
                fiscal_year=fiscal_year,
                data=data,
                is_final=is_historical,  # Mark historical as final
                fetched_at=datetime.utcnow()
            )
            self.db.add(new_record)

            # Log the fetch for cost tracking
            log = DataFetchLog(
                ticker=ticker,
                provider=self.provider.__class__.__name__,
                endpoint=data_type,
                fetched_at=datetime.utcnow()
            )
            self.db.add(log)
            await self.db.commit()

        return data

    async def bulk_load_history(self, ticker: str, years: int = 30):
        """
        Efficiently load 30 years of data.
        Only fetches missing years from API.
        """
        current_year = datetime.now().year
        start_year = current_year - years

        # Find which years we already have
        existing = await self.db.execute(
            select(FinancialData.fiscal_year).where(
                FinancialData.ticker == ticker
            ).distinct()
        )
        existing_years = {row[0] for row in existing.fetchall()}

        # Only fetch missing years
        missing_years = set(range(start_year, current_year + 1)) - existing_years

        if missing_years:
            # Batch fetch from provider (most APIs support date ranges)
            await self._batch_fetch(ticker, min(missing_years), max(missing_years))
```

**Cost Optimization Table:**

| Data Type | Refresh Frequency | API Calls/Stock/Year |
|-----------|-------------------|----------------------|
| Historical (>2 years old) | Never | 1 (one-time) |
| Recent (1-2 years) | Quarterly | 4 |
| Current Year | Monthly | 12 |
| Stock Price | Daily | 252 |

---

## 5. Database Design

### 5.1 Core Schema (PostgreSQL)

```sql
-- Core tables for financial data storage

-- Companies master table
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    market VARCHAR(10) NOT NULL,  -- 'US', 'SET'
    sector VARCHAR(100),
    industry VARCHAR(100),
    currency VARCHAR(3) NOT NULL,  -- 'USD', 'THB'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_market ON companies(market);
CREATE INDEX idx_companies_sector ON companies(sector);

-- Income Statement (30 years of data)
CREATE TABLE income_statements (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    fiscal_year INTEGER NOT NULL,
    fiscal_period VARCHAR(5) DEFAULT 'FY',  -- FY, Q1, Q2, Q3, Q4

    -- Revenue metrics
    revenue DECIMAL(20, 2),
    cost_of_revenue DECIMAL(20, 2),
    gross_profit DECIMAL(20, 2),

    -- Operating metrics
    operating_expenses DECIMAL(20, 2),
    operating_income DECIMAL(20, 2),

    -- Bottom line
    interest_expense DECIMAL(20, 2),
    pretax_income DECIMAL(20, 2),
    income_tax DECIMAL(20, 2),
    net_income DECIMAL(20, 2),

    -- Per share
    eps_basic DECIMAL(10, 4),
    eps_diluted DECIMAL(10, 4),
    shares_outstanding BIGINT,

    -- Metadata
    is_estimated BOOLEAN DEFAULT FALSE,
    data_source VARCHAR(50),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(company_id, fiscal_year, fiscal_period)
);

-- Partition by fiscal_year for efficient queries
CREATE INDEX idx_income_company_year ON income_statements(company_id, fiscal_year DESC);

-- Balance Sheet
CREATE TABLE balance_sheets (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    fiscal_year INTEGER NOT NULL,
    fiscal_period VARCHAR(5) DEFAULT 'FY',

    -- Assets
    cash_and_equivalents DECIMAL(20, 2),
    short_term_investments DECIMAL(20, 2),
    accounts_receivable DECIMAL(20, 2),
    inventory DECIMAL(20, 2),
    total_current_assets DECIMAL(20, 2),
    property_plant_equipment DECIMAL(20, 2),
    goodwill DECIMAL(20, 2),
    intangible_assets DECIMAL(20, 2),
    total_assets DECIMAL(20, 2),

    -- Liabilities
    accounts_payable DECIMAL(20, 2),
    short_term_debt DECIMAL(20, 2),
    total_current_liabilities DECIMAL(20, 2),
    long_term_debt DECIMAL(20, 2),
    total_liabilities DECIMAL(20, 2),

    -- Equity
    retained_earnings DECIMAL(20, 2),
    total_equity DECIMAL(20, 2),

    -- Metadata
    data_source VARCHAR(50),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(company_id, fiscal_year, fiscal_period)
);

CREATE INDEX idx_balance_company_year ON balance_sheets(company_id, fiscal_year DESC);

-- Cash Flow Statement
CREATE TABLE cash_flow_statements (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    fiscal_year INTEGER NOT NULL,
    fiscal_period VARCHAR(5) DEFAULT 'FY',

    -- Operating activities
    net_income DECIMAL(20, 2),
    depreciation_amortization DECIMAL(20, 2),
    stock_based_compensation DECIMAL(20, 2),
    operating_cash_flow DECIMAL(20, 2),

    -- Investing activities
    capital_expenditure DECIMAL(20, 2),
    acquisitions DECIMAL(20, 2),
    investing_cash_flow DECIMAL(20, 2),

    -- Financing activities
    debt_repayment DECIMAL(20, 2),
    dividends_paid DECIMAL(20, 2),
    share_repurchases DECIMAL(20, 2),
    financing_cash_flow DECIMAL(20, 2),

    -- Derived
    free_cash_flow DECIMAL(20, 2),  -- OCF - CapEx

    -- Metadata
    data_source VARCHAR(50),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(company_id, fiscal_year, fiscal_period)
);

CREATE INDEX idx_cashflow_company_year ON cash_flow_statements(company_id, fiscal_year DESC);

-- Stock Prices (daily)
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    price_date DATE NOT NULL,
    open_price DECIMAL(12, 4),
    high_price DECIMAL(12, 4),
    low_price DECIMAL(12, 4),
    close_price DECIMAL(12, 4),
    adjusted_close DECIMAL(12, 4),
    volume BIGINT,

    UNIQUE(company_id, price_date)
) PARTITION BY RANGE (price_date);

-- Create yearly partitions for stock prices
CREATE TABLE stock_prices_2020 PARTITION OF stock_prices
    FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');
CREATE TABLE stock_prices_2021 PARTITION OF stock_prices
    FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
-- ... continue for each year

-- Calculated Valuations (cached results)
CREATE TABLE valuations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- DCF Model
    dcf_value DECIMAL(12, 4),
    dcf_assumptions JSONB,  -- {growth_rate, discount_rate, terminal_growth}

    -- Graham Number
    graham_number DECIMAL(12, 4),

    -- Peter Lynch Fair Value
    lynch_fair_value DECIMAL(12, 4),
    peg_ratio DECIMAL(8, 4),

    -- Current Price for Comparison
    current_price DECIMAL(12, 4),
    margin_of_safety DECIMAL(8, 4),  -- (fair_value - price) / fair_value

    UNIQUE(company_id, calculated_at::date)
);

-- AI Analysis Results
CREATE TABLE ai_analyses (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Input data snapshot
    input_summary JSONB,

    -- AI Response
    verdict VARCHAR(10),  -- 'BUY', 'HOLD', 'SELL'
    confidence_score DECIMAL(5, 2),  -- 0-100

    pros JSONB,  -- ["Strong moat", "Consistent FCF"]
    cons JSONB,  -- ["High debt", "Declining margins"]

    detailed_analysis TEXT,

    -- Metadata
    model_version VARCHAR(50),
    prompt_version VARCHAR(20)
);

CREATE INDEX idx_ai_analysis_company ON ai_analyses(company_id, analyzed_at DESC);

-- API Fetch Logging (for cost tracking)
CREATE TABLE data_fetch_logs (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20),
    provider VARCHAR(50),
    endpoint VARCHAR(100),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_size INTEGER,
    was_cached BOOLEAN DEFAULT FALSE
);
```

---

## 6. Financial Modeling Engine

### 6.1 DCF Calculator (2-Stage Model)

```python
# backend/app/financial_models/dcf.py

from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass
class DCFAssumptions:
    """Configurable DCF model parameters."""
    growth_stage_years: int = 10
    growth_rate: float = 0.10  # 10% initial growth
    terminal_growth_rate: float = 0.03  # 3% perpetual growth
    discount_rate: float = 0.10  # 10% WACC
    margin_of_safety: float = 0.25  # 25% margin of safety

@dataclass
class DCFResult:
    """DCF calculation output."""
    intrinsic_value_per_share: float
    intrinsic_value_with_margin: float
    current_price: float
    upside_percentage: float
    is_undervalued: bool
    projected_fcf: list[float]
    terminal_value: float
    assumptions: DCFAssumptions

class DCFCalculator:
    """
    Two-Stage Discounted Cash Flow Model.

    Stage 1: Growth period (default 10 years) with declining growth rate
    Stage 2: Terminal value using perpetuity growth model
    """

    def __init__(self, assumptions: Optional[DCFAssumptions] = None):
        self.assumptions = assumptions or DCFAssumptions()

    def calculate(
        self,
        current_fcf: float,
        shares_outstanding: int,
        current_price: float,
        net_debt: float = 0
    ) -> DCFResult:
        """
        Calculate intrinsic value per share using 2-stage DCF.

        Args:
            current_fcf: Most recent Free Cash Flow (TTM)
            shares_outstanding: Current diluted shares
            current_price: Current stock price
            net_debt: Total debt - cash (subtracted from enterprise value)
        """
        a = self.assumptions

        # Stage 1: Project FCF for growth years with declining growth
        projected_fcf = []
        fcf = current_fcf
        growth_rate = a.growth_rate
        growth_decay = (a.growth_rate - a.terminal_growth_rate) / a.growth_stage_years

        for year in range(1, a.growth_stage_years + 1):
            # Declining growth rate each year
            effective_growth = max(growth_rate - (growth_decay * (year - 1)), a.terminal_growth_rate)
            fcf = fcf * (1 + effective_growth)
            projected_fcf.append(fcf)

        # Discount Stage 1 cash flows to present value
        pv_stage1 = sum(
            fcf / ((1 + a.discount_rate) ** year)
            for year, fcf in enumerate(projected_fcf, 1)
        )

        # Stage 2: Terminal Value (Gordon Growth Model)
        terminal_fcf = projected_fcf[-1] * (1 + a.terminal_growth_rate)
        terminal_value = terminal_fcf / (a.discount_rate - a.terminal_growth_rate)

        # Discount terminal value to present
        pv_terminal = terminal_value / ((1 + a.discount_rate) ** a.growth_stage_years)

        # Enterprise Value
        enterprise_value = pv_stage1 + pv_terminal

        # Equity Value (subtract net debt)
        equity_value = enterprise_value - net_debt

        # Per Share Values
        intrinsic_value = equity_value / shares_outstanding
        intrinsic_with_margin = intrinsic_value * (1 - a.margin_of_safety)

        upside = ((intrinsic_value - current_price) / current_price) * 100

        return DCFResult(
            intrinsic_value_per_share=round(intrinsic_value, 2),
            intrinsic_value_with_margin=round(intrinsic_with_margin, 2),
            current_price=current_price,
            upside_percentage=round(upside, 2),
            is_undervalued=current_price < intrinsic_with_margin,
            projected_fcf=projected_fcf,
            terminal_value=terminal_value,
            assumptions=a
        )

    def auto_estimate_growth_rate(
        self,
        historical_fcf: list[float],
        historical_revenue: list[float]
    ) -> float:
        """
        Estimate future growth rate from historical data.
        Uses geometric mean of FCF and revenue growth, capped at 25%.
        """
        def geometric_growth(values: list[float]) -> float:
            if len(values) < 2 or values[0] <= 0:
                return 0.0
            return (values[-1] / values[0]) ** (1 / (len(values) - 1)) - 1

        fcf_growth = geometric_growth(historical_fcf[-10:])  # Last 10 years
        revenue_growth = geometric_growth(historical_revenue[-10:])

        # Use conservative estimate (lower of the two, or average if both positive)
        if fcf_growth > 0 and revenue_growth > 0:
            estimated = min(fcf_growth, revenue_growth)
        else:
            estimated = max(fcf_growth, revenue_growth, 0)

        # Cap at 25% - very high growth is unsustainable
        return min(estimated, 0.25)
```

### 6.2 ROIC Moat Analysis

```python
# backend/app/financial_models/moat_analysis.py

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from enum import Enum

class MoatRating(str, Enum):
    WIDE = "Wide"
    NARROW = "Narrow"
    NONE = "None"

@dataclass
class MoatMetrics:
    """10-year ROIC trend analysis."""
    roic_values: list[float]  # Last 10 years
    roic_average: float
    roic_trend: str  # "Improving", "Stable", "Declining"
    roic_consistency: float  # Standard deviation
    moat_rating: MoatRating
    competitive_advantage_period: int  # Years of above-cost-of-capital ROIC

class MoatAnalyzer:
    """
    Analyzes economic moat using ROIC trends.

    Warren Buffett: "The key to investing is determining the competitive
    advantage of any given company and, above all, the durability of that advantage."
    """

    COST_OF_CAPITAL = 0.10  # Assume 10% as hurdle rate
    WIDE_MOAT_THRESHOLD = 0.15  # 15% ROIC = wide moat
    NARROW_MOAT_THRESHOLD = 0.10  # 10% ROIC = narrow moat

    def calculate_roic(
        self,
        net_operating_profit_after_tax: float,
        invested_capital: float
    ) -> float:
        """
        ROIC = NOPAT / Invested Capital

        Where:
        - NOPAT = Operating Income * (1 - Tax Rate)
        - Invested Capital = Total Equity + Total Debt - Cash
        """
        if invested_capital <= 0:
            return 0.0
        return net_operating_profit_after_tax / invested_capital

    def analyze_moat(
        self,
        operating_income_history: list[float],
        tax_rates: list[float],
        equity_history: list[float],
        debt_history: list[float],
        cash_history: list[float]
    ) -> MoatMetrics:
        """
        Analyze 10-year ROIC trend to determine moat strength.
        """
        roic_values = []

        for i in range(len(operating_income_history)):
            nopat = operating_income_history[i] * (1 - tax_rates[i])
            invested_capital = equity_history[i] + debt_history[i] - cash_history[i]
            roic = self.calculate_roic(nopat, invested_capital)
            roic_values.append(roic)

        roic_array = np.array(roic_values)

        # Calculate metrics
        roic_avg = np.mean(roic_array)
        roic_std = np.std(roic_array)

        # Determine trend using linear regression slope
        years = np.arange(len(roic_array))
        slope = np.polyfit(years, roic_array, 1)[0]

        if slope > 0.005:
            trend = "Improving"
        elif slope < -0.005:
            trend = "Declining"
        else:
            trend = "Stable"

        # Count years with ROIC above cost of capital
        years_above_hurdle = sum(1 for r in roic_values if r > self.COST_OF_CAPITAL)

        # Determine moat rating
        if roic_avg >= self.WIDE_MOAT_THRESHOLD and years_above_hurdle >= 8:
            moat = MoatRating.WIDE
        elif roic_avg >= self.NARROW_MOAT_THRESHOLD and years_above_hurdle >= 6:
            moat = MoatRating.NARROW
        else:
            moat = MoatRating.NONE

        return MoatMetrics(
            roic_values=[round(r * 100, 2) for r in roic_values],  # As percentages
            roic_average=round(roic_avg * 100, 2),
            roic_trend=trend,
            roic_consistency=round(roic_std * 100, 2),
            moat_rating=moat,
            competitive_advantage_period=years_above_hurdle
        )
```

### 6.3 Financial Health Scores

```python
# backend/app/financial_models/financial_health.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class AltmanZScoreResult:
    """Altman Z-Score for bankruptcy prediction."""
    z_score: float
    rating: str  # "Safe", "Grey Zone", "Distress"
    components: dict  # Individual X1-X5 values

@dataclass
class PiotroskiFScoreResult:
    """Piotroski F-Score for financial strength."""
    f_score: int  # 0-9
    rating: str  # "Strong", "Moderate", "Weak"
    criteria: dict[str, bool]  # Individual pass/fail for 9 criteria

class FinancialHealthAnalyzer:
    """
    Implements Altman Z-Score and Piotroski F-Score.
    """

    # === ALTMAN Z-SCORE ===
    def calculate_altman_z(
        self,
        working_capital: float,
        retained_earnings: float,
        ebit: float,
        market_cap: float,
        total_liabilities: float,
        revenue: float,
        total_assets: float
    ) -> AltmanZScoreResult:
        """
        Altman Z-Score Formula (for public manufacturing companies):
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5

        Where:
        X1 = Working Capital / Total Assets
        X2 = Retained Earnings / Total Assets
        X3 = EBIT / Total Assets
        X4 = Market Cap / Total Liabilities
        X5 = Revenue / Total Assets
        """
        if total_assets <= 0:
            return AltmanZScoreResult(z_score=0, rating="Unknown", components={})

        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_cap / total_liabilities if total_liabilities > 0 else 0
        x5 = revenue / total_assets

        z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (1.0 * x5)

        # Interpretation
        if z_score > 2.99:
            rating = "Safe"
        elif z_score >= 1.81:
            rating = "Grey Zone"
        else:
            rating = "Distress"

        return AltmanZScoreResult(
            z_score=round(z_score, 2),
            rating=rating,
            components={
                "X1_Working_Capital_Ratio": round(x1, 4),
                "X2_Retained_Earnings_Ratio": round(x2, 4),
                "X3_EBIT_Ratio": round(x3, 4),
                "X4_Market_To_Debt": round(x4, 4),
                "X5_Asset_Turnover": round(x5, 4)
            }
        )

    # === PIOTROSKI F-SCORE ===
    def calculate_piotroski_f(
        self,
        # Current year data
        net_income: float,
        operating_cash_flow: float,
        roa: float,
        total_assets: float,
        long_term_debt: float,
        current_ratio: float,
        shares_outstanding: int,
        gross_margin: float,
        asset_turnover: float,
        # Previous year data for comparison
        prev_roa: float,
        prev_long_term_debt: float,
        prev_current_ratio: float,
        prev_shares_outstanding: int,
        prev_gross_margin: float,
        prev_asset_turnover: float
    ) -> PiotroskiFScoreResult:
        """
        Piotroski F-Score: 9 binary criteria for financial strength.

        Profitability (4 points):
        1. Positive Net Income
        2. Positive Operating Cash Flow
        3. ROA improving
        4. OCF > Net Income (quality of earnings)

        Leverage/Liquidity (3 points):
        5. Long-term debt decreasing
        6. Current ratio improving
        7. No new share issuance

        Operating Efficiency (2 points):
        8. Gross margin improving
        9. Asset turnover improving
        """
        criteria = {}

        # Profitability
        criteria["positive_net_income"] = net_income > 0
        criteria["positive_ocf"] = operating_cash_flow > 0
        criteria["roa_improving"] = roa > prev_roa
        criteria["ocf_exceeds_net_income"] = operating_cash_flow > net_income

        # Leverage & Liquidity
        criteria["debt_decreasing"] = long_term_debt < prev_long_term_debt
        criteria["current_ratio_improving"] = current_ratio > prev_current_ratio
        criteria["no_dilution"] = shares_outstanding <= prev_shares_outstanding

        # Operating Efficiency
        criteria["gross_margin_improving"] = gross_margin > prev_gross_margin
        criteria["asset_turnover_improving"] = asset_turnover > prev_asset_turnover

        f_score = sum(1 for passed in criteria.values() if passed)

        if f_score >= 7:
            rating = "Strong"
        elif f_score >= 4:
            rating = "Moderate"
        else:
            rating = "Weak"

        return PiotroskiFScoreResult(
            f_score=f_score,
            rating=rating,
            criteria=criteria
        )
```

### 6.4 Graham Number & Lynch Fair Value

```python
# backend/app/financial_models/classic_valuations.py

from dataclasses import dataclass
import math

@dataclass
class GrahamNumberResult:
    graham_number: float
    current_price: float
    margin_of_safety: float
    is_undervalued: bool

@dataclass
class LynchFairValueResult:
    fair_value: float
    peg_ratio: float
    current_price: float
    rating: str  # "Undervalued", "Fair", "Overvalued"

class ClassicValuations:
    """
    Classic valuation methods from Benjamin Graham and Peter Lynch.
    """

    def graham_number(
        self,
        eps: float,
        book_value_per_share: float,
        current_price: float
    ) -> GrahamNumberResult:
        """
        Graham Number = sqrt(22.5 * EPS * BVPS)

        This represents the maximum price a defensive investor
        should pay for a stock (P/E of 15 and P/B of 1.5).
        """
        if eps <= 0 or book_value_per_share <= 0:
            return GrahamNumberResult(
                graham_number=0,
                current_price=current_price,
                margin_of_safety=0,
                is_undervalued=False
            )

        graham = math.sqrt(22.5 * eps * book_value_per_share)
        margin = ((graham - current_price) / graham) * 100 if graham > 0 else 0

        return GrahamNumberResult(
            graham_number=round(graham, 2),
            current_price=current_price,
            margin_of_safety=round(margin, 2),
            is_undervalued=current_price < graham
        )

    def lynch_fair_value(
        self,
        eps: float,
        eps_growth_rate: float,  # As decimal (0.15 = 15%)
        dividend_yield: float,   # As decimal (0.02 = 2%)
        current_price: float
    ) -> LynchFairValueResult:
        """
        Peter Lynch Fair Value using PEG Ratio.

        PEG = P/E / Growth Rate
        Fair Value = EPS * Growth Rate (as whole number)

        Lynch: "The P/E ratio of any company that's fairly priced
        will equal its growth rate."
        """
        if eps <= 0 or eps_growth_rate <= 0:
            return LynchFairValueResult(
                fair_value=0,
                peg_ratio=0,
                current_price=current_price,
                rating="Cannot Calculate"
            )

        pe_ratio = current_price / eps
        growth_rate_pct = eps_growth_rate * 100  # Convert to percentage

        # Adjusted PEG includes dividend yield
        adjusted_growth = growth_rate_pct + (dividend_yield * 100)
        peg = pe_ratio / adjusted_growth if adjusted_growth > 0 else float('inf')

        # Fair value assumes PEG of 1
        fair_value = eps * adjusted_growth

        # Rating based on PEG
        if peg < 1:
            rating = "Undervalued"
        elif peg <= 1.5:
            rating = "Fair"
        else:
            rating = "Overvalued"

        return LynchFairValueResult(
            fair_value=round(fair_value, 2),
            peg_ratio=round(peg, 2),
            current_price=current_price,
            rating=rating
        )
```

---

## 7. Buffett AI Integration

### 7.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Analysis Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│  1. Data Aggregation Layer                                  │
│     └─> Collect 10-year financials into structured JSON     │
│                                                             │
│  2. Context Builder                                         │
│     └─> Add market context, sector comparisons, macro data  │
│                                                             │
│  3. Prompt Engineering Layer                                │
│     └─> Apply Buffett persona system prompt                 │
│     └─> Format user query with financial data               │
│                                                             │
│  4. Gemini Pro API Call                                     │
│     └─> Structured output with JSON mode                    │
│                                                             │
│  5. Response Parser                                         │
│     └─> Extract verdict, pros, cons, analysis               │
│     └─> Validate response structure                         │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Input Data Structure

```python
# backend/app/ai/data_aggregator.py

from pydantic import BaseModel
from typing import Optional

class FinancialSummary(BaseModel):
    """10-year financial summary for AI analysis."""

    ticker: str
    company_name: str
    market: str
    sector: str
    currency: str

    # Revenue & Profitability Trends (10 years)
    revenue_history: list[dict]  # [{year: 2014, value: 100M}, ...]
    net_income_history: list[dict]
    free_cash_flow_history: list[dict]

    # Margins (10 years)
    gross_margin_history: list[dict]
    operating_margin_history: list[dict]
    net_margin_history: list[dict]

    # Balance Sheet Strength
    debt_to_equity_history: list[dict]
    current_ratio_history: list[dict]
    interest_coverage_history: list[dict]

    # Returns
    roic_history: list[dict]
    roe_history: list[dict]

    # Valuation Metrics (current)
    current_price: float
    pe_ratio: float
    pb_ratio: float
    ps_ratio: float
    ev_ebitda: float

    # Our Calculated Values
    dcf_intrinsic_value: float
    graham_number: float
    lynch_fair_value: float
    altman_z_score: float
    piotroski_f_score: int
    moat_rating: str

class AggregatorService:
    """Aggregates all financial data for AI input."""

    async def build_summary(self, ticker: str) -> FinancialSummary:
        """
        Compile comprehensive 10-year summary for AI analysis.
        """
        # Fetch from database (pre-loaded data)
        company = await self.get_company(ticker)
        income_stmts = await self.get_income_statements(ticker, years=10)
        balance_sheets = await self.get_balance_sheets(ticker, years=10)
        cash_flows = await self.get_cash_flows(ticker, years=10)
        valuations = await self.get_latest_valuations(ticker)

        return FinancialSummary(
            ticker=ticker,
            company_name=company.name,
            market=company.market,
            sector=company.sector,
            currency=company.currency,

            revenue_history=[
                {"year": s.fiscal_year, "value": s.revenue}
                for s in income_stmts
            ],
            net_income_history=[
                {"year": s.fiscal_year, "value": s.net_income}
                for s in income_stmts
            ],
            free_cash_flow_history=[
                {"year": c.fiscal_year, "value": c.free_cash_flow}
                for c in cash_flows
            ],

            # ... build all other fields ...

            dcf_intrinsic_value=valuations.dcf_value,
            graham_number=valuations.graham_number,
            lynch_fair_value=valuations.lynch_fair_value,
            altman_z_score=valuations.altman_z,
            piotroski_f_score=valuations.piotroski_f,
            moat_rating=valuations.moat_rating
        )
```

### 7.3 System Prompt Strategy

```python
# backend/app/ai/prompts.py

BUFFETT_SYSTEM_PROMPT = """
You are Warren Buffett, the legendary value investor and CEO of Berkshire Hathaway.
You are analyzing a stock for a potential investment. Apply your investment philosophy rigorously:

## Your Core Principles:
1. **Circle of Competence**: Only invest in businesses you understand. If this company is outside your expertise, say so.
2. **Economic Moat**: Look for durable competitive advantages - brands, patents, network effects, switching costs.
3. **Quality Management**: Assess management integrity and capital allocation skills from the numbers.
4. **Margin of Safety**: Never pay full price. Always demand a discount to intrinsic value.
5. **Long-term Thinking**: You're buying a business, not renting a stock. Think in decades.

## Your Analysis Framework:
- **Is this a wonderful business?** (ROIC > 15% consistently, growing free cash flow)
- **Do I understand it?** (Predictable earnings, clear business model)
- **Is management trustworthy?** (Consistent capital allocation, shareholder-friendly)
- **Is the price right?** (Significant margin of safety to intrinsic value)

## Your Tone:
- Be skeptical. Most stocks don't deserve investment.
- Use folksy wisdom and Omaha common sense.
- Cite specific numbers from the data provided.
- Be direct about risks and concerns.
- If you wouldn't invest, say so clearly.

## Famous Buffett Quotes to Remember:
- "Rule No. 1: Never lose money. Rule No. 2: Never forget Rule No. 1."
- "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price."
- "Price is what you pay; value is what you get."
- "Be fearful when others are greedy, and greedy when others are fearful."
"""

ANALYSIS_USER_PROMPT_TEMPLATE = """
Analyze {company_name} ({ticker}) for potential investment.

## Financial Data (Last 10 Years):

### Revenue & Profitability:
{revenue_table}

### Free Cash Flow:
{fcf_table}

### Return on Invested Capital (ROIC):
{roic_table}

### Debt & Financial Health:
- Current Debt-to-Equity: {debt_to_equity}
- Altman Z-Score: {altman_z} ({altman_rating})
- Piotroski F-Score: {piotroski_f}/9 ({piotroski_rating})

### Valuation:
- Current Price: {current_price}
- P/E Ratio: {pe_ratio}
- DCF Intrinsic Value: {dcf_value}
- Graham Number: {graham_number}
- Margin of Safety: {margin_of_safety}%

### Moat Analysis:
- 10-Year Average ROIC: {roic_avg}%
- ROIC Trend: {roic_trend}
- Moat Rating: {moat_rating}

---

Based on your investment philosophy, provide your analysis in the following JSON structure:
{{
    "verdict": "BUY" | "HOLD" | "SELL",
    "confidence": <0-100>,
    "summary": "<1-2 sentence summary in Buffett's voice>",
    "pros": ["<strength 1>", "<strength 2>", ...],
    "cons": ["<concern 1>", "<concern 2>", ...],
    "detailed_analysis": "<3-4 paragraph deep analysis>",
    "key_metrics_cited": ["<metric: value>", ...],
    "would_buffett_buy": true | false,
    "price_to_consider": <price at which you'd buy, or null>
}}
"""
```

### 7.4 Gemini API Integration

```python
# backend/app/ai/gemini_client.py

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from pydantic import BaseModel
from typing import Optional
import json

class AIAnalysisResult(BaseModel):
    """Structured AI analysis output."""
    verdict: str
    confidence: int
    summary: str
    pros: list[str]
    cons: list[str]
    detailed_analysis: str
    key_metrics_cited: list[str]
    would_buffett_buy: bool
    price_to_consider: Optional[float]

class GeminiAnalyzer:
    """Wrapper for Google Gemini Pro API."""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=GenerationConfig(
                temperature=0.7,  # Balanced creativity
                top_p=0.95,
                top_k=40,
                max_output_tokens=4096,
                response_mime_type="application/json"  # Force JSON output
            )
        )

    async def analyze_stock(
        self,
        summary: FinancialSummary,
        system_prompt: str,
        user_prompt: str
    ) -> AIAnalysisResult:
        """
        Send financial summary to Gemini for analysis.
        """
        # Build conversation
        chat = self.model.start_chat(history=[])

        # Set system context
        chat.send_message(system_prompt)

        # Send analysis request
        response = await chat.send_message_async(user_prompt)

        # Parse JSON response
        try:
            result_dict = json.loads(response.text)
            return AIAnalysisResult(**result_dict)
        except json.JSONDecodeError:
            # Fallback: attempt to extract structured data
            return self._fallback_parse(response.text)

    def _fallback_parse(self, text: str) -> AIAnalysisResult:
        """
        Attempt to parse unstructured response.
        """
        # Use regex or another LLM call to extract structure
        # This is a safety net for when JSON mode fails
        return AIAnalysisResult(
            verdict="HOLD",
            confidence=50,
            summary="Analysis could not be fully parsed.",
            pros=[],
            cons=[],
            detailed_analysis=text,
            key_metrics_cited=[],
            would_buffett_buy=False,
            price_to_consider=None
        )
```

### 7.5 Output Rendering for UI

```typescript
// frontend/src/types/ai-analysis.ts

export interface AIAnalysis {
  verdict: 'BUY' | 'HOLD' | 'SELL';
  confidence: number;
  summary: string;
  pros: string[];
  cons: string[];
  detailedAnalysis: string;
  keyMetricsCited: string[];
  wouldBuffettBuy: boolean;
  priceToConsider: number | null;
  analyzedAt: string;
}

// Color coding for verdicts
export const VERDICT_COLORS = {
  BUY: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-500' },
  HOLD: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-500' },
  SELL: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-500' },
};
```

---

## 8. API Design

### 8.1 RESTful Endpoints

```yaml
# OpenAPI Specification Summary

/api/v1/companies:
  GET:
    summary: List all tracked companies
    params: market (US|SET), sector, page, limit

/api/v1/companies/{ticker}:
  GET:
    summary: Get company profile and basic info

/api/v1/companies/{ticker}/financials:
  GET:
    summary: Get 30-year financial history
    params: statement_type (income|balance|cashflow), years

/api/v1/companies/{ticker}/valuations:
  GET:
    summary: Get calculated valuations (DCF, Graham, Lynch)

/api/v1/companies/{ticker}/health:
  GET:
    summary: Get financial health scores (Z-Score, F-Score)

/api/v1/companies/{ticker}/moat:
  GET:
    summary: Get moat analysis with ROIC trends

/api/v1/companies/{ticker}/ai-analysis:
  GET:
    summary: Get latest Buffett AI analysis
  POST:
    summary: Trigger new AI analysis (regenerate)

/api/v1/companies/{ticker}/prices:
  GET:
    summary: Historical stock prices
    params: start_date, end_date, interval (daily|weekly|monthly)

/api/v1/search:
  GET:
    summary: Search companies by name or ticker
    params: q, market
```

### 8.2 Response Models

```python
# backend/app/schemas/responses.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CompanyResponse(BaseModel):
    ticker: str
    name: str
    market: str
    sector: str
    industry: str
    currency: str
    description: Optional[str]

class ValuationResponse(BaseModel):
    ticker: str
    calculated_at: datetime
    current_price: float
    dcf_value: float
    dcf_upside_pct: float
    graham_number: float
    graham_margin_pct: float
    lynch_fair_value: float
    peg_ratio: float
    overall_rating: str  # "Undervalued", "Fair", "Overvalued"

class HealthScoreResponse(BaseModel):
    ticker: str
    altman_z_score: float
    altman_rating: str
    piotroski_f_score: int
    piotroski_rating: str
    overall_health: str  # "Strong", "Moderate", "Weak"
```

---

## 9. Frontend Architecture

### 9.1 Page Structure

```
/                           # Home - Market overview, trending stocks
/search                     # Search results page
/stock/[ticker]             # Main stock analysis page
  ├── Overview tab          # Key metrics, AI verdict, price chart
  ├── Financials tab        # 30-year Income, Balance, Cash Flow tables
  ├── Valuation tab         # DCF calculator, Graham, Lynch
  ├── Health tab            # Z-Score, F-Score breakdown
  └── AI Analysis tab       # Full Buffett AI report
/watchlist                  # User's saved stocks
/compare                    # Side-by-side comparison tool
```

### 9.2 Key Components

```typescript
// Component hierarchy for stock page

<StockPage ticker={ticker}>
  <StockHeader />           // Name, price, change, market
  <QuickMetrics />          // P/E, P/B, Market Cap, 52-week range
  <AIVerdictBanner />       // BUY/HOLD/SELL with confidence

  <TabContainer>
    <OverviewTab>
      <PriceChart />        // Recharts line chart with DCF overlay
      <KeyStatistics />     // 2-column key metrics
      <MoatIndicator />     // Visual moat strength gauge
    </OverviewTab>

    <FinancialsTab>
      <StatementSelector /> // Income | Balance | Cash Flow toggle
      <FinancialTable />    // 30-year scrollable table
      <TrendCharts />       // Revenue, earnings growth charts
    </FinancialsTab>

    <ValuationTab>
      <DCFCalculator />     // Interactive DCF with adjustable inputs
      <GrahamNumber />      // Visual vs current price
      <LynchFairValue />    // PEG breakdown
      <ValuationSummary />  // Combined verdict
    </ValuationTab>

    <HealthTab>
      <AltmanZScore />      // Score breakdown with components
      <PiotroskiFScore />   // 9-criteria checklist
      <DebtAnalysis />      // Leverage trend charts
    </HealthTab>

    <AIAnalysisTab>
      <BuffettVerdict />    // Full AI report
      <ProsConsList />      // Expandable pros/cons
      <DetailedAnalysis />  // Full markdown analysis
    </AIAnalysisTab>
  </TabContainer>
</StockPage>
```

### 9.3 State Management

```typescript
// Using Zustand for global state

// stores/stockStore.ts
interface StockStore {
  currentTicker: string | null;
  financials: FinancialData | null;
  valuations: ValuationData | null;
  aiAnalysis: AIAnalysis | null;
  isLoading: boolean;

  setTicker: (ticker: string) => void;
  fetchFinancials: (ticker: string) => Promise<void>;
  fetchValuations: (ticker: string) => Promise<void>;
  fetchAIAnalysis: (ticker: string) => Promise<void>;
}

// Using React Query for API data
// hooks/useStockData.ts
export function useFinancials(ticker: string) {
  return useQuery({
    queryKey: ['financials', ticker],
    queryFn: () => api.getFinancials(ticker),
    staleTime: 1000 * 60 * 60, // 1 hour (data doesn't change often)
  });
}
```

---

## 10. Implementation Roadmap

### Phase 1: Environment & Database Schema

**Objective:** Set up development environment and core infrastructure.

**Tasks:**
1. Initialize project structure
   ```
   ai-stock-analysis/
   ├── backend/
   │   ├── app/
   │   │   ├── __init__.py
   │   │   ├── main.py
   │   │   ├── config.py
   │   │   ├── models/
   │   │   ├── schemas/
   │   │   ├── services/
   │   │   ├── api/
   │   │   ├── data_providers/
   │   │   └── financial_models/
   │   ├── tests/
   │   ├── alembic/
   │   ├── requirements.txt
   │   └── Dockerfile
   ├── frontend/
   │   ├── src/
   │   │   ├── app/
   │   │   ├── components/
   │   │   ├── hooks/
   │   │   ├── stores/
   │   │   ├── types/
   │   │   └── lib/
   │   ├── package.json
   │   └── Dockerfile
   ├── docker-compose.yml
   ├── .env.example
   └── PROJECT_BLUEPRINT.md
   ```

2. Configure Docker Compose with PostgreSQL and Redis

3. Create SQLAlchemy models and run Alembic migrations

4. Set up FastAPI application skeleton with health checks

5. Initialize Next.js 14 with TypeScript and Tailwind

**Deliverables:**
- Working Docker environment (`docker-compose up` runs all services)
- Empty database with all tables created
- Basic FastAPI `/health` endpoint
- Next.js app with Tailwind configured

---

### Phase 2: Data Ingestion Engine

**Objective:** Build the data pipeline from external APIs to database.

**Tasks:**
1. Implement `AbstractDataProvider` base class

2. Create EOD Historical Data provider implementation
   - Income statement fetching
   - Balance sheet fetching
   - Cash flow fetching
   - Stock price history

3. Implement `TickerResolver` for US/Thai market handling

4. Build `DataCacheService` with "fetch-once-store-forever" logic

5. Create background job for bulk data loading

6. Implement data refresh scheduler for current year data

**Deliverables:**
- Working data ingestion for 5 test tickers (AAPL, MSFT, GOOGL, PTT.BK, CPALL.BK)
- 30 years of historical data loaded
- API cost tracking in `data_fetch_logs`

---

### Phase 3: Financial Math Engine

**Objective:** Implement all valuation and analysis calculations.

**Tasks:**
1. Build `DCFCalculator` with auto growth rate estimation

2. Implement `MoatAnalyzer` with ROIC trend analysis

3. Create `FinancialHealthAnalyzer` (Z-Score, F-Score)

4. Build `ClassicValuations` (Graham Number, Lynch Fair Value)

5. Create `ValuationOrchestrator` to run all models and cache results

6. Write comprehensive unit tests for all calculations

**Deliverables:**
- All valuation models producing accurate results
- Cached valuations in database
- Test coverage > 80% for financial models

---

### Phase 4: API & Frontend Dashboard

**Objective:** Build the user-facing application.

**Tasks:**
1. Implement all REST API endpoints

2. Build frontend page structure and routing

3. Create stock search and company list components

4. Build financial data tables with 30-year scrolling

5. Implement valuation display components

6. Create interactive charts with Recharts
   - Price vs DCF value
   - Revenue/earnings trends
   - ROIC over time

7. Implement responsive design for mobile

**Deliverables:**
- Fully functional web app (without AI)
- All financial data visible
- Interactive DCF calculator

---

### Phase 5: AI Integration

**Objective:** Add the Buffett AI analysis feature.

**Tasks:**
1. Set up Google Gemini Pro API connection

2. Build `AggregatorService` for AI input data

3. Create and test system prompt engineering

4. Implement `GeminiAnalyzer` with JSON output parsing

5. Build AI analysis API endpoint with caching

6. Create frontend AI analysis display components
   - Verdict banner
   - Pros/cons cards
   - Detailed analysis markdown renderer

7. Add "Regenerate Analysis" functionality

**Deliverables:**
- Working AI analysis for all tracked stocks
- Responsive AI verdict display
- Analysis caching (avoid repeated API calls)

---

## Appendix A: Environment Variables

```bash
# .env.example

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/valueinvestai
REDIS_URL=redis://localhost:6379/0

# External APIs
EOD_API_KEY=your_eod_api_key
FMP_API_KEY=your_fmp_api_key_optional

# Google AI
GEMINI_API_KEY=your_gemini_api_key

# Application
APP_ENV=development
DEBUG=true
SECRET_KEY=your_secret_key_here

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Appendix B: Testing Strategy

```python
# Unit tests for financial models
# tests/test_dcf.py

import pytest
from app.financial_models.dcf import DCFCalculator, DCFAssumptions

class TestDCFCalculator:
    def test_basic_dcf_calculation(self):
        calc = DCFCalculator()
        result = calc.calculate(
            current_fcf=1_000_000_000,  # $1B FCF
            shares_outstanding=1_000_000_000,  # 1B shares
            current_price=100,
            net_debt=5_000_000_000  # $5B net debt
        )

        assert result.intrinsic_value_per_share > 0
        assert result.is_undervalued in [True, False]

    def test_negative_fcf_handling(self):
        calc = DCFCalculator()
        result = calc.calculate(
            current_fcf=-500_000_000,  # Negative FCF
            shares_outstanding=1_000_000_000,
            current_price=50,
            net_debt=0
        )

        # Should handle gracefully
        assert result.intrinsic_value_per_share <= 0
```

---

*Document Version: 1.0*
*Created: January 2026*
*Author: ValueInvestAI Architecture Team*
