# PROJECT_BLUEPRINT.md
# Intelligent Investor Pro - Technical Specification

> A local-first stock analysis web application combining AI-powered data normalization with rigorous CFA-grade valuation methodologies.

---

## Table of Contents
1. [Project Directory Structure](#1-project-directory-structure)
2. [Tech Stack](#2-tech-stack)
3. [Data Schema](#3-data-schema)
4. [Hybrid Valuation Logic](#4-hybrid-valuation-logic)
5. [AI Prompt Strategy](#5-ai-prompt-strategy)
6. [Implementation Steps](#6-implementation-steps)

---

## 1. Project Directory Structure

```
ai-stock-analysis/
│
├── data/                                    # [EXISTING] Financial data storage
│   ├── cache/
│   │   └── company_tickers.json            # CIK to ticker mapping
│   └── output/
│       ├── csv/
│       │   ├── summary.csv                 # Screener data (51 columns, 10 stocks)
│       │   └── financial_history.csv       # Historical metrics
│       └── json/
│           ├── AAPL.json                   # Per-stock deep financials
│           ├── MSFT.json
│           ├── GOOGL.json
│           ├── AMZN.json
│           ├── NVDA.json
│           ├── META.json
│           ├── TSLA.json
│           ├── AVGO.json
│           ├── BRK-B.json
│           └── LLY.json
│
├── backend/                                 # [NEW] Python FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                         # FastAPI application entry
│   │   ├── config.py                       # Settings & environment config
│   │   ├── dependencies.py                 # Dependency injection
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py               # API version router
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── screener.py         # GET /stocks
│   │   │           ├── stock.py            # GET /stocks/{ticker}
│   │   │           ├── valuation.py        # GET /stocks/{ticker}/valuation
│   │   │           ├── analysis.py         # GET /stocks/{ticker}/ai-analysis
│   │   │           └── realtime.py         # GET /stocks/{ticker}/price
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── data_loader.py              # CSV/JSON file loaders
│   │   │   └── cache_manager.py            # File-based caching (diskcache)
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── stock.py                    # StockSummary Pydantic model
│   │   │   ├── financial_data.py           # Raw financial data models
│   │   │   ├── valuation_input.py          # StandardizedValuationInput
│   │   │   ├── valuation_output.py         # DCF/Graham result models
│   │   │   └── analysis.py                 # WarrenBuffettAnalysis model
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── stock_service.py            # Stock data business logic
│   │   │   ├── realtime_service.py         # yfinance integration
│   │   │   ├── ai_extractor.py             # Gemini data normalization
│   │   │   ├── valuation_engine.py         # DCF/Graham calculations
│   │   │   └── ai_analyst.py               # Warren Buffett memo generator
│   │   │
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── extraction_prompt.py        # Data extraction prompts
│   │       └── analysis_prompt.py          # Investment analysis prompts
│   │
│   ├── cache/                              # File-based cache storage
│   │   ├── extractions/                    # AI extraction results
│   │   ├── valuations/                     # Computed valuations
│   │   └── analyses/                       # AI analysis memos
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_valuation_engine.py
│   │   └── test_ai_extractor.py
│   │
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/                                # [NEW] Next.js React Frontend
│   ├── src/
│   │   ├── app/                            # Next.js App Router
│   │   │   ├── layout.tsx                  # Root layout
│   │   │   ├── page.tsx                    # Home/Screener page
│   │   │   ├── loading.tsx                 # Loading state
│   │   │   ├── error.tsx                   # Error boundary
│   │   │   └── stocks/
│   │   │       └── [ticker]/
│   │   │           ├── page.tsx            # Stock detail page
│   │   │           └── loading.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                         # Shadcn UI components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── badge.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   ├── accordion.tsx
│   │   │   │   └── skeleton.tsx
│   │   │   │
│   │   │   ├── screener/
│   │   │   │   ├── DataGrid.tsx            # AG Grid stock table
│   │   │   │   ├── FilterBar.tsx           # Numeric/dropdown filters
│   │   │   │   ├── SearchInput.tsx         # Ticker/name search
│   │   │   │   └── ColumnSelector.tsx      # Show/hide columns
│   │   │   │
│   │   │   ├── stock/
│   │   │   │   ├── PriceHeader.tsx         # Real-time price display
│   │   │   │   ├── PriceChart.tsx          # Historical candlestick
│   │   │   │   ├── CompanyInfo.tsx         # Company metadata
│   │   │   │   ├── FinancialTabs.tsx       # Income/Balance/Cash tabs
│   │   │   │   ├── ValuationCard.tsx       # DCF/Graham results
│   │   │   │   ├── AIAnalysis.tsx          # Buffett memo display
│   │   │   │   └── KeyMetrics.tsx          # Quick metrics grid
│   │   │   │
│   │   │   └── charts/
│   │   │       ├── CandlestickChart.tsx    # TradingView-style chart
│   │   │       ├── AreaChart.tsx           # Revenue/income trends
│   │   │       └── MetricsChart.tsx        # Multi-metric comparison
│   │   │
│   │   ├── hooks/
│   │   │   ├── useStocks.ts                # All stocks query
│   │   │   ├── useStock.ts                 # Single stock query
│   │   │   ├── useRealTimePrice.ts         # 30s polling price
│   │   │   ├── useValuation.ts             # Valuation data
│   │   │   └── useAIAnalysis.ts            # AI analysis query
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                      # Axios API client
│   │   │   ├── utils.ts                    # Utility functions
│   │   │   └── formatters.ts               # Currency/percent formatters
│   │   │
│   │   └── types/
│   │       ├── stock.ts                    # Stock TypeScript types
│   │       ├── valuation.ts                # Valuation types
│   │       └── analysis.ts                 # Analysis types
│   │
│   ├── public/
│   │   └── favicon.ico
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml                       # Local development orchestration
├── PROJECT_BLUEPRINT.md                     # This file
├── README.md                                # Project documentation
└── .gitignore
```

---

## 2. Tech Stack

### Backend (Python 3.11+)

```txt
# requirements.txt

# === Core Framework ===
fastapi==0.115.6                    # High-performance async API framework
uvicorn[standard]==0.34.0           # ASGI server
pydantic==2.10.4                    # Data validation & serialization
pydantic-settings==2.7.1            # Environment configuration

# === AI Integration ===
google-generativeai==0.8.4          # Gemini Pro API SDK

# === Financial Data ===
yfinance==0.2.51                    # Real-time stock prices
pandas==2.2.3                       # Data manipulation
numpy==2.2.1                        # Numerical calculations

# === Caching & Storage ===
diskcache==5.6.3                    # File-based persistent cache
aiofiles==24.1.0                    # Async file operations

# === HTTP & Serialization ===
httpx==0.28.1                       # Async HTTP client
orjson==3.10.13                     # Fast JSON serialization

# === Development & Testing ===
pytest==8.3.4                       # Testing framework
pytest-asyncio==0.25.2              # Async test support
pytest-cov==6.0.0                   # Coverage reporting
python-dotenv==1.0.1                # Environment variables
black==24.10.0                      # Code formatting
ruff==0.8.6                         # Linting
mypy==1.14.1                        # Type checking
```

### Frontend (Node.js 20+)

```json
{
  "dependencies": {
    "next": "15.1.3",
    "react": "19.0.0",
    "react-dom": "19.0.0",

    "@tanstack/react-query": "5.62.16",
    "@tanstack/react-table": "8.20.6",
    "ag-grid-react": "32.3.3",
    "ag-grid-community": "32.3.3",

    "recharts": "2.15.0",
    "lightweight-charts": "4.2.2",

    "tailwindcss": "3.4.17",
    "@radix-ui/react-dialog": "1.1.4",
    "@radix-ui/react-dropdown-menu": "2.1.4",
    "@radix-ui/react-tabs": "1.1.2",
    "@radix-ui/react-tooltip": "1.1.6",
    "@radix-ui/react-accordion": "1.2.2",

    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "tailwind-merge": "2.6.0",
    "lucide-react": "0.469.0",

    "date-fns": "4.1.0",
    "zod": "3.24.1",
    "axios": "1.7.9"
  },
  "devDependencies": {
    "typescript": "5.7.2",
    "@types/react": "19.0.2",
    "@types/node": "22.10.5",
    "eslint": "9.17.0",
    "prettier": "3.4.2"
  }
}
```

### Environment Configuration

```bash
# backend/.env.example

# Google AI
GOOGLE_API_KEY=your_gemini_api_key_here

# Application
APP_ENV=development
DEBUG=true
API_PREFIX=/api/v1

# Data Paths
DATA_DIR=../data
CSV_PATH=../data/output/csv/summary.csv
JSON_DIR=../data/output/json

# Cache Settings
CACHE_DIR=./cache
EXTRACTION_CACHE_TTL=604800    # 7 days in seconds
VALUATION_CACHE_TTL=86400      # 24 hours
ANALYSIS_CACHE_TTL=604800      # 7 days
PRICE_CACHE_TTL=30             # 30 seconds

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 3. Data Schema

### 3.1 StandardizedValuationInput (AI-Extracted)

This is the core schema that Gemini Pro must output. It normalizes messy JSON data into clean, validated inputs for valuation calculations.

```python
# backend/app/models/valuation_input.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class HistoricalFinancials(BaseModel):
    """Single year of financial data for trend analysis"""
    fiscal_year: int
    revenue: float
    gross_profit: float
    operating_income: float
    net_income: float
    free_cash_flow: float
    eps: float
    depreciation_amortization: float
    capital_expenditures: float
    total_assets: float
    total_liabilities: float
    shareholders_equity: float
    total_debt: float
    cash_and_equivalents: float


class StandardizedValuationInput(BaseModel):
    """
    AI-normalized valuation inputs for DCF/Graham formulas.
    Gemini extracts and standardizes from messy JSON data.

    TIME HORIZONS (CFA Standard):
    - Historical: 10 years (full economic cycle)
    - Projections: 5 years explicit + terminal value
    """

    # === Metadata ===
    ticker: str
    company_name: str
    sector: str
    industry: str
    extraction_timestamp: datetime
    data_confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="AI's confidence in data extraction quality"
    )

    # === Current Market Position ===
    current_price: float
    shares_outstanding: float
    market_cap: float
    enterprise_value: float

    # === Income Statement (TTM - Trailing Twelve Months) ===
    ttm_revenue: float
    ttm_cost_of_revenue: float
    ttm_gross_profit: float
    ttm_operating_expenses: float
    ttm_operating_income: float
    ttm_interest_expense: Optional[float] = None
    ttm_pretax_income: float
    ttm_tax_expense: float
    ttm_net_income: float
    ttm_ebitda: float
    ttm_eps: float

    # === Cash Flow Statement (TTM) ===
    ttm_operating_cash_flow: float
    ttm_capital_expenditures: float
    ttm_free_cash_flow: float
    ttm_depreciation_amortization: float
    ttm_stock_based_compensation: Optional[float] = None
    ttm_dividends_paid: Optional[float] = None
    ttm_share_repurchases: Optional[float] = None

    # === Balance Sheet (Latest Quarter) ===
    cash_and_equivalents: float
    short_term_investments: Optional[float] = None
    total_cash: float  # cash + short-term investments
    accounts_receivable: float
    inventory: Optional[float] = None
    total_current_assets: float

    property_plant_equipment: float
    goodwill: Optional[float] = None
    intangible_assets: Optional[float] = None
    total_assets: float

    accounts_payable: float
    short_term_debt: float
    total_current_liabilities: float
    long_term_debt: float
    total_debt: float
    total_liabilities: float

    shareholders_equity: float
    retained_earnings: float

    # === Calculated Position Metrics ===
    net_debt: float  # total_debt - total_cash
    working_capital: float  # current_assets - current_liabilities
    invested_capital: float  # equity + debt - cash

    # === Profitability Ratios ===
    gross_margin: float = Field(description="Gross Profit / Revenue")
    operating_margin: float = Field(description="Operating Income / Revenue")
    net_margin: float = Field(description="Net Income / Revenue")
    ebitda_margin: float = Field(description="EBITDA / Revenue")

    roe: float = Field(description="Return on Equity: Net Income / Shareholders Equity")
    roa: float = Field(description="Return on Assets: Net Income / Total Assets")
    roic: float = Field(description="Return on Invested Capital: NOPAT / Invested Capital")

    # === Efficiency Ratios ===
    asset_turnover: float = Field(description="Revenue / Total Assets")
    inventory_turnover: Optional[float] = Field(None, description="COGS / Average Inventory")
    receivables_turnover: Optional[float] = Field(None, description="Revenue / Avg Receivables")

    # === Leverage Ratios ===
    debt_to_equity: float
    debt_to_ebitda: Optional[float] = None
    interest_coverage: Optional[float] = Field(None, description="EBIT / Interest Expense")

    # === Liquidity Ratios ===
    current_ratio: float = Field(description="Current Assets / Current Liabilities")
    quick_ratio: float = Field(description="(Current Assets - Inventory) / Current Liabilities")
    cash_ratio: float = Field(description="Cash / Current Liabilities")

    # === Valuation Multiples (Current) ===
    pe_ratio: Optional[float] = Field(None, description="Price / EPS")
    forward_pe: Optional[float] = Field(None, description="Price / Forward EPS")
    peg_ratio: Optional[float] = Field(None, description="P/E / Growth Rate")
    price_to_book: Optional[float] = Field(None, description="Price / Book Value per Share")
    price_to_sales: Optional[float] = Field(None, description="Market Cap / Revenue")
    ev_to_ebitda: Optional[float] = Field(None, description="Enterprise Value / EBITDA")
    ev_to_revenue: Optional[float] = Field(None, description="Enterprise Value / Revenue")
    fcf_yield: Optional[float] = Field(None, description="FCF / Market Cap")
    earnings_yield: Optional[float] = Field(None, description="EPS / Price")

    # === Growth Rates (Calculated from Historical Data) ===
    revenue_growth_1y: Optional[float] = None
    revenue_growth_3y_cagr: Optional[float] = None
    revenue_growth_5y_cagr: Optional[float] = None
    revenue_growth_10y_cagr: Optional[float] = None

    earnings_growth_1y: Optional[float] = None
    earnings_growth_3y_cagr: Optional[float] = None
    earnings_growth_5y_cagr: Optional[float] = None
    earnings_growth_10y_cagr: Optional[float] = None

    fcf_growth_1y: Optional[float] = None
    fcf_growth_3y_cagr: Optional[float] = None
    fcf_growth_5y_cagr: Optional[float] = None

    # === Risk Parameters ===
    beta: Optional[float] = Field(None, description="5-year monthly beta vs S&P 500")
    risk_free_rate: float = Field(description="10-year Treasury yield")
    equity_risk_premium: float = Field(default=0.05, description="Market risk premium (default 5%)")

    # === Dividend Information ===
    dividend_per_share: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    dividend_growth_5y: Optional[float] = None
    years_of_dividend_growth: Optional[int] = None

    # === Historical Data (10 Years - CFA Standard) ===
    historical_financials: List[HistoricalFinancials] = Field(
        description="10 years of annual financial data, most recent first"
    )

    # === Data Quality Flags ===
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Fields that could not be extracted"
    )
    estimated_fields: List[str] = Field(
        default_factory=list,
        description="Fields that were estimated/calculated"
    )
    data_anomalies: List[str] = Field(
        default_factory=list,
        description="Data quality warnings"
    )
```

### 3.2 Valuation Output Schema

```python
# backend/app/models/valuation_output.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class ValuationVerdict(str, Enum):
    SIGNIFICANTLY_UNDERVALUED = "significantly_undervalued"  # >40% upside
    UNDERVALUED = "undervalued"                              # 15-40% upside
    FAIRLY_VALUED = "fairly_valued"                          # -15% to +15%
    OVERVALUED = "overvalued"                                # 15-40% downside
    SIGNIFICANTLY_OVERVALUED = "significantly_overvalued"    # >40% downside


class DCFScenario(BaseModel):
    """Single DCF scenario calculation"""
    scenario_name: str  # "conservative", "base", "optimistic"

    # Assumptions
    revenue_growth_rate: float
    operating_margin_assumption: float
    terminal_growth_rate: float
    wacc: float

    # Projections (5 or 10 years)
    projection_years: int
    projected_revenue: List[float]
    projected_ebit: List[float]
    projected_nopat: List[float]
    projected_fcf: List[float]

    # Terminal Value
    terminal_fcf: float
    terminal_value: float

    # Present Values
    pv_explicit_period: float
    pv_terminal_value: float

    # Valuation
    enterprise_value: float
    equity_value: float
    intrinsic_value_per_share: float

    # Comparison
    current_price: float
    upside_downside_pct: float


class DCFValuation(BaseModel):
    """Complete DCF analysis with three scenarios"""
    calculation_timestamp: datetime
    methodology: str = "Discounted Cash Flow (FCFF)"

    # Cost of Capital Calculation
    risk_free_rate: float
    beta: float
    equity_risk_premium: float
    cost_of_equity: float  # CAPM: Rf + Beta * ERP

    cost_of_debt_pretax: float
    tax_rate: float
    cost_of_debt_aftertax: float

    debt_weight: float
    equity_weight: float
    wacc: float

    # Three Scenarios
    conservative: DCFScenario
    base_case: DCFScenario
    optimistic: DCFScenario

    # Probability-Weighted Result
    scenario_weights: Dict[str, float] = {
        "conservative": 0.25,
        "base_case": 0.50,
        "optimistic": 0.25
    }
    weighted_intrinsic_value: float

    # Sensitivity
    sensitivity_to_wacc: Dict[str, float]  # +/- 1% WACC impact
    sensitivity_to_growth: Dict[str, float]  # +/- 1% terminal growth impact


class GrahamNumber(BaseModel):
    """Benjamin Graham's intrinsic value formula"""
    methodology: str = "Graham Number = sqrt(22.5 * EPS * BVPS)"

    eps_ttm: float
    book_value_per_share: float
    graham_multiplier: float = 22.5

    graham_number: float
    current_price: float
    upside_pct: float

    # Graham's earnings power value variant
    normalized_eps: Optional[float] = None
    earnings_power_value: Optional[float] = None


class GrahamDefensiveCriteria(BaseModel):
    """Graham's 7 criteria for the defensive investor"""

    # Criterion 1: Adequate Size
    adequate_size: bool
    revenue_minimum: float = 700_000_000  # $700M for industrial
    actual_revenue: float

    # Criterion 2: Strong Financial Condition
    strong_financial_condition: bool
    current_ratio_minimum: float = 2.0
    actual_current_ratio: float

    # Criterion 3: Earnings Stability (positive earnings 10 years)
    earnings_stability: bool
    years_positive_earnings: int
    required_years: int = 10

    # Criterion 4: Dividend Record (20 years of dividends)
    dividend_record: bool
    years_dividends_paid: int
    required_dividend_years: int = 20

    # Criterion 5: Earnings Growth (33% over 10 years = ~2.9% CAGR)
    earnings_growth: bool
    eps_10y_growth: Optional[float]
    required_growth: float = 0.33

    # Criterion 6: Moderate P/E Ratio
    moderate_pe: bool
    pe_maximum: float = 15.0
    actual_pe: Optional[float]

    # Criterion 7: Moderate Price-to-Book
    moderate_pb: bool
    pb_maximum: float = 1.5
    actual_pb: Optional[float]

    # Combined: P/E * P/B < 22.5
    graham_product: Optional[float]
    graham_product_passes: bool

    # Summary
    criteria_passed: int
    total_criteria: int = 7
    passes_screen: bool  # At least 5 of 7


class RelativeValuation(BaseModel):
    """Peer/sector comparison valuation"""
    peer_group: List[str]

    # Peer Averages
    peer_median_pe: float
    peer_median_ev_ebitda: float
    peer_median_ps: float
    peer_median_pb: float

    # Implied Values
    implied_value_from_pe: float
    implied_value_from_ev_ebitda: float
    implied_value_from_ps: float
    implied_value_from_pb: float

    # Composite
    composite_implied_value: float
    premium_discount_to_peers: float


class ValuationResult(BaseModel):
    """Complete valuation output combining all methods"""
    ticker: str
    company_name: str
    calculation_timestamp: datetime

    # Current Market Data
    current_price: float
    market_cap: float
    enterprise_value: float
    shares_outstanding: float

    # Valuation Methods
    dcf_valuation: DCFValuation
    graham_number: GrahamNumber
    graham_defensive_screen: GrahamDefensiveCriteria
    relative_valuation: Optional[RelativeValuation] = None

    # Composite Intrinsic Value
    valuation_methods_used: List[str]
    composite_intrinsic_value: float
    composite_methodology: str = "60% DCF + 40% Graham Number"

    # Final Assessment
    upside_downside_pct: float
    margin_of_safety: float
    verdict: ValuationVerdict
    confidence_score: float = Field(ge=0.0, le=1.0)

    # Assumptions & Caveats
    key_assumptions: Dict[str, str]
    risk_factors: List[str]
    data_quality_score: float = Field(ge=0.0, le=1.0)
```

### 3.3 AI Analysis Output Schema

```python
# backend/app/models/analysis.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class InvestmentRating(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MoatType(str, Enum):
    BRAND = "brand"
    NETWORK_EFFECTS = "network_effects"
    COST_ADVANTAGE = "cost_advantage"
    SWITCHING_COSTS = "switching_costs"
    EFFICIENT_SCALE = "efficient_scale"
    INTANGIBLE_ASSETS = "intangible_assets"
    NONE = "none"


class CompetitiveAdvantage(BaseModel):
    """Analysis of a single competitive moat"""
    moat_type: MoatType
    description: str
    durability: str  # "narrow", "wide", "eroding"
    evidence: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class RiskFactor(BaseModel):
    """Detailed risk assessment"""
    category: str  # "market", "regulatory", "competitive", "operational", "financial"
    title: str
    description: str
    severity: str  # "low", "medium", "high", "critical"
    probability: str  # "unlikely", "possible", "likely", "very_likely"
    mitigation: Optional[str] = None


class WarrenBuffettAnalysis(BaseModel):
    """
    AI-generated investment memo in Warren Buffett style.
    Combines quantitative valuation with qualitative business analysis.
    """

    # === Header ===
    ticker: str
    company_name: str
    analysis_date: datetime

    # === Executive Summary ===
    one_sentence_thesis: str = Field(
        description="One compelling sentence summarizing the investment case"
    )
    investment_thesis: str = Field(
        description="2-3 paragraph detailed investment thesis"
    )

    # === Business Quality Assessment ===

    # Circle of Competence
    business_understanding: str = Field(
        description="Can I understand this business in 10 minutes?"
    )
    business_simplicity_score: int = Field(
        ge=1, le=10,
        description="1=highly complex, 10=simple and predictable"
    )

    # Economic Moat
    competitive_advantages: List[CompetitiveAdvantage]
    moat_summary: str
    moat_durability: str  # "none", "narrow", "wide"

    # Management Quality
    management_assessment: str
    management_integrity_score: int = Field(ge=1, le=10)
    capital_allocation_skill: str
    owner_oriented: bool

    # Owner Earnings Power
    owner_earnings_analysis: str = Field(
        description="Analysis of true cash-generating ability"
    )
    earnings_predictability: str  # "highly_predictable", "predictable", "uncertain", "unpredictable"

    # === Financial Health ===
    balance_sheet_fortress: str
    debt_comfort_level: str
    cash_generation_power: str
    return_on_capital_trend: str

    # === Valuation Summary ===
    valuation_narrative: str
    intrinsic_value_range: str  # "$X to $Y"
    current_price_vs_value: str
    margin_of_safety_assessment: str

    # === Key Investment Considerations ===
    key_positives: List[str] = Field(
        min_length=3, max_length=7,
        description="Main reasons to buy"
    )
    key_concerns: List[str] = Field(
        min_length=2, max_length=5,
        description="Main risks and concerns"
    )
    key_risks: List[RiskFactor]
    potential_catalysts: List[str]

    # === Time Horizon ===
    ideal_holding_period: str  # "3-5 years", "5-10 years", "forever"
    patience_required_level: str

    # === Final Verdict ===
    investment_rating: InvestmentRating
    conviction_level: float = Field(
        ge=0.0, le=1.0,
        description="How confident in this rating"
    )
    risk_level: RiskLevel
    suitable_for: List[str]  # "value_investors", "dividend_seekers", "growth_investors"

    # === Closing Wisdom ===
    buffett_quote: str = Field(
        description="Relevant Warren Buffett quote for this situation"
    )
    final_thoughts: str

    # === Meta ===
    ai_model_used: str
    analysis_version: str = "1.0"
    tokens_consumed: int
    generation_time_seconds: float
```

---

## 4. Hybrid Valuation Logic

### 4.1 Architecture Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           HYBRID VALUATION PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: DATA LOADING                                                            │
│  ┌─────────────────┐                                                             │
│  │ {TICKER}.json   │ ──► Load 500-700KB raw JSON with all financial sections    │
│  │ (Local File)    │                                                             │
│  └─────────────────┘                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: INTELLIGENT TRUNCATION                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Extract ONLY these sections (reduce to ~15-20KB for API efficiency):     │    │
│  │ • company_info (name, sector, industry)                                  │    │
│  │ • market_data (price, market cap, beta)                                  │    │
│  │ • valuation (all ratios)                                                 │    │
│  │ • calculated_metrics (pre-computed metrics)                              │    │
│  │ • financials_annual (last 10 years)                                      │    │
│  │ • yahoo_financials.income_statement_quarterly (last 4 quarters for TTM)  │    │
│  │ • yahoo_financials.balance_sheet (latest)                                │    │
│  │ • yahoo_financials.cash_flow_statement_quarterly (last 4 quarters)       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: CACHE CHECK                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ cache_key = hash(ticker + collected_at + market_data_hash)               │    │
│  │                                                                          │    │
│  │ IF cache_hit AND source_data_unchanged:                                  │    │
│  │     RETURN cached_standardized_input                                     │    │
│  │ ELSE:                                                                    │    │
│  │     PROCEED to Gemini extraction                                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: AI EXTRACTION (Google Gemini Pro)                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ PROMPT:                                                                  │    │
│  │ "You are a CFA Level 3 analyst. Extract standardized valuation inputs   │    │
│  │  from this financial data. Handle naming variations (Revenue vs Sales). │    │
│  │  Return ONLY valid JSON matching StandardizedValuationInput schema."    │    │
│  │                                                                          │    │
│  │ INPUT: Truncated JSON (~15-20KB)                                        │    │
│  │ OUTPUT: StandardizedValuationInput (validated by Pydantic)              │    │
│  │                                                                          │    │
│  │ AI handles:                                                              │    │
│  │  ✓ Field name normalization ("Net Sales" → "revenue")                   │    │
│  │  ✓ TTM calculations from 4 quarters                                     │    │
│  │  ✓ CAGR calculations from historical data                               │    │
│  │  ✓ Missing field handling                                               │    │
│  │  ✓ Data quality assessment                                               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  AI DOES NOT: Calculate valuation formulas (DCF, Graham, WACC)                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: PYTHON VALUATION ENGINE (Pure Math - No AI)                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ INPUT: StandardizedValuationInput (clean, validated data)               │    │
│  │                                                                          │    │
│  │ CALCULATIONS:                                                            │    │
│  │                                                                          │    │
│  │ 1. WACC (Weighted Average Cost of Capital)                              │    │
│  │    ┌──────────────────────────────────────────────────────────────┐     │    │
│  │    │ Cost of Equity = Rf + β × ERP                                │     │    │
│  │    │              = risk_free_rate + beta × equity_risk_premium   │     │    │
│  │    │                                                              │     │    │
│  │    │ Cost of Debt = Rf + Credit Spread (based on interest coverage) │   │    │
│  │    │ After-tax CoD = Cost of Debt × (1 - Tax Rate)                │     │    │
│  │    │                                                              │     │    │
│  │    │ WACC = (E/V × CoE) + (D/V × After-tax CoD)                   │     │    │
│  │    └──────────────────────────────────────────────────────────────┘     │    │
│  │                                                                          │    │
│  │ 2. DCF VALUATION (3 Scenarios × 5-Year Projection)                      │    │
│  │    ┌──────────────────────────────────────────────────────────────┐     │    │
│  │    │ For year t = 1 to 5:                                         │     │    │
│  │    │   Revenue(t) = Revenue(t-1) × (1 + growth_rate)              │     │    │
│  │    │   NOPAT(t) = Revenue(t) × operating_margin × (1 - tax)       │     │    │
│  │    │   FCF(t) = NOPAT(t) + D&A - CapEx - ΔWC                      │     │    │
│  │    │   PV_FCF(t) = FCF(t) / (1 + WACC)^t                          │     │    │
│  │    │                                                              │     │    │
│  │    │ Terminal Value = FCF(5) × (1 + g) / (WACC - g)               │     │    │
│  │    │ PV_Terminal = Terminal Value / (1 + WACC)^5                  │     │    │
│  │    │                                                              │     │    │
│  │    │ Enterprise Value = Σ PV_FCF + PV_Terminal                    │     │    │
│  │    │ Equity Value = EV - Net Debt                                 │     │    │
│  │    │ Intrinsic Value per Share = Equity Value / Shares            │     │    │
│  │    └──────────────────────────────────────────────────────────────┘     │    │
│  │                                                                          │    │
│  │ 3. GRAHAM NUMBER                                                         │    │
│  │    ┌──────────────────────────────────────────────────────────────┐     │    │
│  │    │ Graham Number = √(22.5 × EPS × BVPS)                         │     │    │
│  │    │                                                              │     │    │
│  │    │ Where:                                                       │     │    │
│  │    │   EPS = TTM Earnings per Share                               │     │    │
│  │    │   BVPS = Shareholders Equity / Shares Outstanding            │     │    │
│  │    │   22.5 = Graham's P/E(15) × P/B(1.5) limit                   │     │    │
│  │    └──────────────────────────────────────────────────────────────┘     │    │
│  │                                                                          │    │
│  │ 4. GRAHAM DEFENSIVE SCREEN (7 Criteria)                                  │    │
│  │    ┌──────────────────────────────────────────────────────────────┐     │    │
│  │    │ □ Revenue > $700M (Adequate Size)                            │     │    │
│  │    │ □ Current Ratio > 2.0 (Strong Finances)                      │     │    │
│  │    │ □ 10 years positive earnings (Stability)                     │     │    │
│  │    │ □ 20 years dividends (Dividend Record)                       │     │    │
│  │    │ □ EPS growth > 33% over 10 years (Growth)                    │     │    │
│  │    │ □ P/E < 15 (Moderate P/E)                                    │     │    │
│  │    │ □ P/B < 1.5 OR P/E × P/B < 22.5                              │     │    │
│  │    └──────────────────────────────────────────────────────────────┘     │    │
│  │                                                                          │    │
│  │ 5. COMPOSITE INTRINSIC VALUE                                             │    │
│  │    ┌──────────────────────────────────────────────────────────────┐     │    │
│  │    │ Composite IV = (0.60 × DCF_Weighted) + (0.40 × Graham_Number)│     │    │
│  │    │                                                              │     │    │
│  │    │ Margin of Safety = (Intrinsic Value - Price) / Intrinsic Value │   │    │
│  │    │                                                              │     │    │
│  │    │ Verdict based on upside:                                     │     │    │
│  │    │   > 40%: SIGNIFICANTLY_UNDERVALUED                           │     │    │
│  │    │   15-40%: UNDERVALUED                                        │     │    │
│  │    │   -15% to 15%: FAIRLY_VALUED                                 │     │    │
│  │    │   -40% to -15%: OVERVALUED                                   │     │    │
│  │    │   < -40%: SIGNIFICANTLY_OVERVALUED                           │     │    │
│  │    └──────────────────────────────────────────────────────────────┘     │    │
│  │                                                                          │    │
│  │ OUTPUT: ValuationResult                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: AI ANALYSIS (Google Gemini Pro)                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ PROMPT:                                                                  │    │
│  │ "Act as Warren Buffett. You see {TICKER} with:                          │    │
│  │  - Intrinsic Value: $X vs Current Price: $Y                             │    │
│  │  - Margin of Safety: Z%                                                 │    │
│  │  - DCF scenarios: Conservative/Base/Optimistic                          │    │
│  │  - Graham Screen: Passed X/7 criteria                                   │    │
│  │  - Key metrics: ROE, ROIC, margins, growth rates                        │    │
│  │                                                                          │    │
│  │  Write a Warren Buffett-style investment memo."                         │    │
│  │                                                                          │    │
│  │ INPUT: ValuationResult + Company Description                            │    │
│  │ OUTPUT: WarrenBuffettAnalysis                                           │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STEP 7: CACHE & RETURN                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ Cache extraction result (7 days TTL)                                     │    │
│  │ Cache valuation result (24 hours TTL)                                    │    │
│  │ Cache AI analysis (7 days TTL)                                           │    │
│  │                                                                          │    │
│  │ Return: { valuation: ValuationResult, analysis: WarrenBuffettAnalysis } │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Valuation Engine Implementation

```python
# backend/app/services/valuation_engine.py

import math
from datetime import datetime
from typing import List, Dict
from app.models.valuation_input import StandardizedValuationInput
from app.models.valuation_output import (
    ValuationResult, DCFValuation, DCFScenario,
    GrahamNumber, GrahamDefensiveCriteria, ValuationVerdict
)


class ValuationEngine:
    """
    Pure Python valuation calculations.
    Takes clean AI-extracted data, outputs rigorous valuations.
    No AI calls in this class - math only.
    """

    def __init__(self, input_data: StandardizedValuationInput):
        self.data = input_data
        self.tax_rate = 0.21  # US federal corporate tax rate

    def calculate_cost_of_equity(self) -> float:
        """CAPM: Cost of Equity = Rf + Beta * ERP"""
        return (
            self.data.risk_free_rate +
            (self.data.beta or 1.0) * self.data.equity_risk_premium
        )

    def calculate_cost_of_debt(self) -> float:
        """Estimate cost of debt from interest coverage"""
        # Credit spread based on interest coverage ratio
        ic = self.data.interest_coverage
        if ic is None or ic <= 0:
            spread = 0.05  # Distressed
        elif ic < 1.5:
            spread = 0.04  # CCC rating
        elif ic < 3:
            spread = 0.03  # B rating
        elif ic < 5:
            spread = 0.02  # BB rating
        elif ic < 8:
            spread = 0.015  # BBB rating
        elif ic < 12:
            spread = 0.01  # A rating
        else:
            spread = 0.007  # AA/AAA rating

        return self.data.risk_free_rate + spread

    def calculate_wacc(self) -> Dict:
        """Calculate Weighted Average Cost of Capital"""
        cost_of_equity = self.calculate_cost_of_equity()
        cost_of_debt_pretax = self.calculate_cost_of_debt()
        cost_of_debt_aftertax = cost_of_debt_pretax * (1 - self.tax_rate)

        total_capital = self.data.market_cap + self.data.total_debt
        equity_weight = self.data.market_cap / total_capital if total_capital > 0 else 1.0
        debt_weight = self.data.total_debt / total_capital if total_capital > 0 else 0.0

        wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt_aftertax)

        return {
            "cost_of_equity": cost_of_equity,
            "cost_of_debt_pretax": cost_of_debt_pretax,
            "cost_of_debt_aftertax": cost_of_debt_aftertax,
            "equity_weight": equity_weight,
            "debt_weight": debt_weight,
            "wacc": wacc
        }

    def calculate_dcf_scenario(
        self,
        name: str,
        growth_rate: float,
        terminal_growth: float,
        margin_assumption: float,
        wacc: float,
        projection_years: int = 5
    ) -> DCFScenario:
        """Calculate single DCF scenario"""

        base_revenue = self.data.ttm_revenue
        base_fcf = self.data.ttm_free_cash_flow

        # Project financials
        projected_revenue = []
        projected_ebit = []
        projected_nopat = []
        projected_fcf = []

        current_revenue = base_revenue

        for year in range(1, projection_years + 1):
            # Growth decay toward terminal rate
            year_growth = growth_rate - (growth_rate - terminal_growth) * (year / (projection_years * 2))

            current_revenue *= (1 + year_growth)
            ebit = current_revenue * margin_assumption
            nopat = ebit * (1 - self.tax_rate)

            # FCF approximation: NOPAT adjusted for reinvestment
            reinvestment_rate = year_growth / (self.data.roic if self.data.roic > 0 else 0.10)
            fcf = nopat * (1 - min(reinvestment_rate, 0.8))

            projected_revenue.append(current_revenue)
            projected_ebit.append(ebit)
            projected_nopat.append(nopat)
            projected_fcf.append(fcf)

        # Terminal value (Gordon Growth Model)
        terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
        if wacc <= terminal_growth:
            terminal_growth = wacc - 0.01  # Safety adjustment
        terminal_value = terminal_fcf / (wacc - terminal_growth)

        # Present values
        pv_explicit = sum(
            fcf / ((1 + wacc) ** (i + 1))
            for i, fcf in enumerate(projected_fcf)
        )
        pv_terminal = terminal_value / ((1 + wacc) ** projection_years)

        # Enterprise to equity
        enterprise_value = pv_explicit + pv_terminal
        equity_value = enterprise_value - self.data.net_debt
        intrinsic_per_share = equity_value / self.data.shares_outstanding

        upside = (intrinsic_per_share - self.data.current_price) / self.data.current_price

        return DCFScenario(
            scenario_name=name,
            revenue_growth_rate=growth_rate,
            operating_margin_assumption=margin_assumption,
            terminal_growth_rate=terminal_growth,
            wacc=wacc,
            projection_years=projection_years,
            projected_revenue=projected_revenue,
            projected_ebit=projected_ebit,
            projected_nopat=projected_nopat,
            projected_fcf=projected_fcf,
            terminal_fcf=terminal_fcf,
            terminal_value=terminal_value,
            pv_explicit_period=pv_explicit,
            pv_terminal_value=pv_terminal,
            enterprise_value=enterprise_value,
            equity_value=equity_value,
            intrinsic_value_per_share=intrinsic_per_share,
            current_price=self.data.current_price,
            upside_downside_pct=upside
        )

    def calculate_dcf(self) -> DCFValuation:
        """Calculate complete DCF with 3 scenarios"""
        wacc_components = self.calculate_wacc()
        wacc = wacc_components["wacc"]

        # Base growth from historical data
        base_growth = self.data.revenue_growth_5y_cagr or 0.05
        current_margin = self.data.operating_margin

        # Scenario parameters
        scenarios = {
            "conservative": {
                "growth": max(0.02, base_growth * 0.5),
                "terminal": 0.02,
                "margin": current_margin * 0.85
            },
            "base_case": {
                "growth": base_growth,
                "terminal": 0.025,
                "margin": current_margin
            },
            "optimistic": {
                "growth": min(0.25, base_growth * 1.5),
                "terminal": 0.03,
                "margin": min(current_margin * 1.15, 0.35)
            }
        }

        dcf_scenarios = {}
        for name, params in scenarios.items():
            dcf_scenarios[name] = self.calculate_dcf_scenario(
                name=name,
                growth_rate=params["growth"],
                terminal_growth=params["terminal"],
                margin_assumption=params["margin"],
                wacc=wacc
            )

        # Probability-weighted value
        weights = {"conservative": 0.25, "base_case": 0.50, "optimistic": 0.25}
        weighted_iv = sum(
            dcf_scenarios[name].intrinsic_value_per_share * weight
            for name, weight in weights.items()
        )

        # Sensitivity analysis
        sensitivity_wacc = {
            "wacc_minus_1pct": self.calculate_dcf_scenario(
                "sens", base_growth, 0.025, current_margin, wacc - 0.01
            ).intrinsic_value_per_share,
            "wacc_plus_1pct": self.calculate_dcf_scenario(
                "sens", base_growth, 0.025, current_margin, wacc + 0.01
            ).intrinsic_value_per_share
        }

        return DCFValuation(
            calculation_timestamp=datetime.utcnow(),
            risk_free_rate=self.data.risk_free_rate,
            beta=self.data.beta or 1.0,
            equity_risk_premium=self.data.equity_risk_premium,
            cost_of_equity=wacc_components["cost_of_equity"],
            cost_of_debt_pretax=wacc_components["cost_of_debt_pretax"],
            tax_rate=self.tax_rate,
            cost_of_debt_aftertax=wacc_components["cost_of_debt_aftertax"],
            debt_weight=wacc_components["debt_weight"],
            equity_weight=wacc_components["equity_weight"],
            wacc=wacc,
            conservative=dcf_scenarios["conservative"],
            base_case=dcf_scenarios["base_case"],
            optimistic=dcf_scenarios["optimistic"],
            scenario_weights=weights,
            weighted_intrinsic_value=weighted_iv,
            sensitivity_to_wacc=sensitivity_wacc,
            sensitivity_to_growth={}
        )

    def calculate_graham_number(self) -> GrahamNumber:
        """Benjamin Graham's intrinsic value formula"""
        eps = self.data.ttm_eps
        bvps = self.data.shareholders_equity / self.data.shares_outstanding

        # Graham Number = sqrt(22.5 * EPS * BVPS)
        if eps > 0 and bvps > 0:
            graham_number = math.sqrt(22.5 * eps * bvps)
        else:
            graham_number = 0

        upside = (
            (graham_number - self.data.current_price) / self.data.current_price
            if graham_number > 0 else -1.0
        )

        return GrahamNumber(
            eps_ttm=eps,
            book_value_per_share=bvps,
            graham_number=graham_number,
            current_price=self.data.current_price,
            upside_pct=upside
        )

    def calculate_graham_defensive_screen(self) -> GrahamDefensiveCriteria:
        """Graham's 7 criteria for defensive investors"""

        # Count years of positive earnings from historical data
        years_positive = sum(
            1 for h in self.data.historical_financials if h.net_income > 0
        )

        # Estimate dividend years (simplified)
        years_dividends = 20 if (self.data.dividend_yield or 0) > 0 else 0

        # EPS growth over 10 years
        if len(self.data.historical_financials) >= 10:
            old_eps = self.data.historical_financials[-1].eps
            new_eps = self.data.historical_financials[0].eps
            eps_growth = (new_eps - old_eps) / abs(old_eps) if old_eps != 0 else 0
        else:
            eps_growth = self.data.earnings_growth_10y_cagr

        pe = self.data.pe_ratio
        pb = self.data.price_to_book
        graham_product = (pe or 999) * (pb or 999) if pe and pb else None

        criteria = GrahamDefensiveCriteria(
            adequate_size=(self.data.ttm_revenue >= 700_000_000),
            actual_revenue=self.data.ttm_revenue,
            strong_financial_condition=(self.data.current_ratio >= 2.0),
            actual_current_ratio=self.data.current_ratio,
            earnings_stability=(years_positive >= 10),
            years_positive_earnings=years_positive,
            dividend_record=(years_dividends >= 20),
            years_dividends_paid=years_dividends,
            earnings_growth=(eps_growth is not None and eps_growth >= 0.33),
            eps_10y_growth=eps_growth,
            moderate_pe=(pe is not None and pe <= 15),
            actual_pe=pe,
            moderate_pb=(pb is not None and pb <= 1.5),
            actual_pb=pb,
            graham_product=graham_product,
            graham_product_passes=(graham_product is not None and graham_product < 22.5),
            criteria_passed=0,  # Will calculate below
            passes_screen=False
        )

        # Count passed criteria
        passed = sum([
            criteria.adequate_size,
            criteria.strong_financial_condition,
            criteria.earnings_stability,
            criteria.dividend_record,
            criteria.earnings_growth,
            criteria.moderate_pe or criteria.graham_product_passes,
            criteria.moderate_pb or criteria.graham_product_passes
        ])

        criteria.criteria_passed = passed
        criteria.passes_screen = (passed >= 5)

        return criteria

    def determine_verdict(self, upside_pct: float) -> ValuationVerdict:
        """Determine valuation verdict from upside percentage"""
        if upside_pct > 0.40:
            return ValuationVerdict.SIGNIFICANTLY_UNDERVALUED
        elif upside_pct > 0.15:
            return ValuationVerdict.UNDERVALUED
        elif upside_pct > -0.15:
            return ValuationVerdict.FAIRLY_VALUED
        elif upside_pct > -0.40:
            return ValuationVerdict.OVERVALUED
        else:
            return ValuationVerdict.SIGNIFICANTLY_OVERVALUED

    def run_valuation(self) -> ValuationResult:
        """Execute complete valuation analysis"""

        dcf = self.calculate_dcf()
        graham = self.calculate_graham_number()
        graham_screen = self.calculate_graham_defensive_screen()

        # Composite intrinsic value (60% DCF, 40% Graham)
        composite_iv = (
            dcf.weighted_intrinsic_value * 0.60 +
            graham.graham_number * 0.40
        )

        upside = (composite_iv - self.data.current_price) / self.data.current_price
        margin_of_safety = upside / (1 + upside) if upside > -1 else -1
        verdict = self.determine_verdict(upside)

        return ValuationResult(
            ticker=self.data.ticker,
            company_name=self.data.company_name,
            calculation_timestamp=datetime.utcnow(),
            current_price=self.data.current_price,
            market_cap=self.data.market_cap,
            enterprise_value=self.data.enterprise_value,
            shares_outstanding=self.data.shares_outstanding,
            dcf_valuation=dcf,
            graham_number=graham,
            graham_defensive_screen=graham_screen,
            valuation_methods_used=["DCF (FCFF)", "Graham Number", "Graham Defensive Screen"],
            composite_intrinsic_value=composite_iv,
            upside_downside_pct=upside,
            margin_of_safety=margin_of_safety,
            verdict=verdict,
            confidence_score=self.data.data_confidence_score,
            key_assumptions={
                "risk_free_rate": f"{self.data.risk_free_rate:.2%}",
                "equity_risk_premium": f"{self.data.equity_risk_premium:.2%}",
                "beta": f"{self.data.beta:.2f}" if self.data.beta else "1.00 (assumed)",
                "tax_rate": f"{self.tax_rate:.0%}",
                "terminal_growth": "2.5% (base case)",
                "dcf_weighting": "60%",
                "graham_weighting": "40%"
            },
            risk_factors=self.data.data_anomalies,
            data_quality_score=self.data.data_confidence_score
        )
```

---

## 5. AI Prompt Strategy

### 5.1 Data Extraction Prompt

```python
# backend/app/prompts/extraction_prompt.py

EXTRACTION_SYSTEM_PROMPT = """You are a CFA Level 3 Charterholder and expert financial data analyst specializing in equity valuation.

YOUR MISSION:
Extract and normalize financial data from messy JSON structures into a standardized format suitable for DCF and Graham valuation models.

CRITICAL REQUIREMENTS:

1. DATA INTEGRITY
   - All monetary values MUST be in USD
   - All ratios MUST be in decimal form (15% = 0.15, NOT 15)
   - All growth rates MUST be annualized CAGRs
   - If data is MISSING, set to null - NEVER fabricate values
   - If data is INCONSISTENT, flag it in data_anomalies

2. FIELD NAME NORMALIZATION
   Handle common variations:
   - "Revenue" = "Net Sales" = "Total Revenue" = "Sales"
   - "Net Income" = "Net Earnings" = "Profit"
   - "Operating Income" = "EBIT" = "Operating Profit"
   - "Free Cash Flow" = "FCF" = "Levered Free Cash Flow"
   - "Shareholders Equity" = "Stockholders Equity" = "Total Equity"

3. TTM CALCULATIONS
   For trailing twelve months metrics:
   - Sum last 4 quarters of income statement items
   - Use most recent balance sheet values
   - Average balance sheet items where ratios require it

4. GROWTH RATE CALCULATIONS
   CAGR Formula: ((End Value / Start Value) ^ (1/years)) - 1
   - 1Y Growth: Compare to prior year
   - 3Y CAGR: Compare to 3 years ago
   - 5Y CAGR: Compare to 5 years ago
   - 10Y CAGR: Compare to 10 years ago

5. DATA PRIORITY (when conflicts exist)
   1. financials_annual (SEC filings - most authoritative)
   2. yahoo_financials (comprehensive, validated)
   3. calculated_metrics (pre-computed, verify if possible)
   4. valuation section (Yahoo Finance API)
   5. market_data (real-time, may lag)

6. CONFIDENCE SCORING
   Score 0.0 to 1.0 based on:
   - Data completeness (all fields present)
   - Data consistency (no major discrepancies)
   - Source quality (SEC > Yahoo > calculated)
   - Recency (newer = higher confidence)

OUTPUT FORMAT:
Return a valid JSON object EXACTLY matching the StandardizedValuationInput schema.
NO markdown formatting. NO code blocks. JUST pure JSON.
"""

EXTRACTION_USER_PROMPT = """
Analyze the following financial data for {ticker} ({company_name}) and extract standardized valuation inputs.

=== CURRENT MARKET DATA ===
Price: ${current_price:.2f}
Market Cap: ${market_cap:,.0f}
Data Collection Time: {collected_at}

=== COMPANY INFORMATION ===
{company_info_json}

=== MARKET DATA ===
{market_data_json}

=== VALUATION METRICS ===
{valuation_json}

=== CALCULATED METRICS ===
{calculated_metrics_json}

=== ANNUAL FINANCIALS (Last 10 Years) ===
{financials_annual_json}

=== QUARTERLY INCOME STATEMENT (Last 4 Quarters for TTM) ===
{income_quarterly_json}

=== QUARTERLY BALANCE SHEET (Latest) ===
{balance_sheet_json}

=== QUARTERLY CASH FLOW (Last 4 Quarters for TTM) ===
{cashflow_quarterly_json}

=== END OF DATA ===

Extract and return a JSON object with ALL fields from StandardizedValuationInput.

Critical extraction points:
1. Calculate TTM metrics from quarterly data
2. Calculate 1Y, 3Y, 5Y, and 10Y CAGRs from annual data
3. Extract all 10 years of historical financials
4. Assess data quality and assign confidence score
5. Note any missing or estimated fields

Return ONLY valid JSON. No markdown. No explanation.
"""
```

### 5.2 Warren Buffett Analysis Prompt

```python
# backend/app/prompts/analysis_prompt.py

BUFFETT_SYSTEM_PROMPT = """You are Warren Buffett, the legendary value investor and CEO of Berkshire Hathaway.

You are analyzing a potential investment using your time-tested principles:

INVESTMENT PHILOSOPHY:
1. "Price is what you pay, value is what you get."
2. Only invest in businesses you understand (Circle of Competence)
3. Look for durable competitive advantages (Economic Moats)
4. Focus on owner earnings, not accounting earnings
5. Demand a margin of safety
6. "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price"
7. Management integrity and capital allocation are paramount
8. Think like a business owner, not a stock trader
9. Be fearful when others are greedy, greedy when others are fearful
10. Time horizon: "Our favorite holding period is forever"

MOAT TYPES YOU RECOGNIZE:
- Brand Power (Coca-Cola, Apple)
- Network Effects (Visa, American Express)
- Cost Advantages (GEICO, Costco)
- Switching Costs (Microsoft, Oracle)
- Efficient Scale (railroads, utilities)
- Intangible Assets (patents, licenses)

ANALYSIS STYLE:
- Write in first person as Warren Buffett
- Use folksy wisdom and Omaha common sense
- Be direct about concerns - you've seen bubbles before
- Reference past investments when relevant (See's Candies, Coca-Cola, Apple)
- Explain complex ideas simply - "Never invest in a business you cannot understand"
- Long-term perspective - ignore short-term noise

RED FLAGS YOU WATCH FOR:
- High debt levels ("Only when the tide goes out do you discover who's been swimming naked")
- Aggressive accounting
- Complex business models
- Serial acquirers destroying value
- Management not aligned with shareholders
- No sustainable competitive advantage

OUTPUT: Return a JSON object matching the WarrenBuffettAnalysis schema exactly.
"""

BUFFETT_USER_PROMPT = """
Analyze this investment opportunity as Warren Buffett would:

=== COMPANY: {ticker} - {company_name} ===
Sector: {sector}
Industry: {industry}

=== BUSINESS DESCRIPTION ===
{business_description}

=== QUANTITATIVE VALUATION RESULTS ===

Current Price: ${current_price:.2f}
Market Cap: ${market_cap:,.0f}
Enterprise Value: ${enterprise_value:,.0f}

DCF Intrinsic Value (Weighted): ${dcf_intrinsic_value:.2f}
  - Conservative Scenario: ${dcf_conservative:.2f} ({dcf_conservative_upside:+.1%})
  - Base Case Scenario: ${dcf_base:.2f} ({dcf_base_upside:+.1%})
  - Optimistic Scenario: ${dcf_optimistic:.2f} ({dcf_optimistic_upside:+.1%})

Graham Number: ${graham_number:.2f} ({graham_upside:+.1%})

Composite Intrinsic Value: ${composite_iv:.2f}
Overall Upside/Downside: {upside_pct:+.1%}
Margin of Safety: {margin_of_safety:.1%}

Valuation Verdict: {verdict}

=== KEY FINANCIAL METRICS ===

Profitability:
- Gross Margin: {gross_margin:.1%}
- Operating Margin: {operating_margin:.1%}
- Net Margin: {net_margin:.1%}
- ROE: {roe:.1%}
- ROIC: {roic:.1%}
- ROA: {roa:.1%}

Growth (Historical):
- Revenue 5Y CAGR: {revenue_cagr_5y:.1%}
- Revenue 10Y CAGR: {revenue_cagr_10y:.1%}
- Earnings 5Y CAGR: {earnings_cagr_5y:.1%}

Valuation Multiples:
- P/E Ratio: {pe_ratio:.1f}x
- Forward P/E: {forward_pe:.1f}x
- EV/EBITDA: {ev_ebitda:.1f}x
- P/B Ratio: {pb_ratio:.1f}x
- FCF Yield: {fcf_yield:.1%}

Financial Health:
- Debt/Equity: {debt_to_equity:.2f}x
- Interest Coverage: {interest_coverage:.1f}x
- Current Ratio: {current_ratio:.2f}
- Net Debt: ${net_debt:,.0f}

Other:
- Beta: {beta:.2f}
- Dividend Yield: {dividend_yield:.1%}

=== GRAHAM DEFENSIVE SCREEN ===
Passed {graham_passed}/7 criteria:
{graham_screen_details}

=== 10-YEAR FINANCIAL HISTORY ===
{financial_history_table}

=== END OF DATA ===

Provide your complete Warren Buffett-style investment analysis.
Consider the business quality, competitive position, management, valuation, and risks.
Be honest about what you don't know and where the uncertainties lie.

Return ONLY valid JSON matching the WarrenBuffettAnalysis schema. No markdown.
"""
```

---

## 6. Implementation Steps

### Phase 1: Foundation Setup
**Goal**: Basic working backend and frontend skeleton

#### Backend Tasks
```bash
# 1. Create project structure
mkdir -p backend/app/{api/v1/endpoints,core,models,services,prompts}
mkdir -p backend/{cache,tests}

# 2. Initialize Python project
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv

# 3. Create initial files
touch app/__init__.py app/main.py app/config.py
```

**Files to Create**:
- `backend/app/main.py` - FastAPI app with CORS
- `backend/app/config.py` - Pydantic Settings configuration
- `backend/app/core/data_loader.py` - CSV and JSON file readers
- `backend/app/models/stock.py` - StockSummary Pydantic model
- `backend/app/api/v1/endpoints/screener.py` - GET /stocks endpoint

#### Frontend Tasks
```bash
# 1. Create Next.js project
npx create-next-app@latest frontend --typescript --tailwind --eslint --app

# 2. Install dependencies
cd frontend
npm install @tanstack/react-query axios

# 3. Setup Shadcn UI
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card badge
```

**Files to Create**:
- `frontend/src/lib/api.ts` - Axios API client
- `frontend/src/hooks/useStocks.ts` - React Query hook
- `frontend/src/app/page.tsx` - Basic stock list

**Milestone**: Navigate from stock list to detail page showing raw data

---

### Phase 2: Screener Excellence
**Goal**: Production-quality data grid with all features

**Tasks**:
1. Install AG Grid: `npm install ag-grid-react ag-grid-community`
2. Create DataGrid component with all 51 columns
3. Implement column visibility toggle
4. Add multi-column sorting
5. Create FilterBar with numeric range filters
6. Add sector/industry dropdown filters
7. Implement ticker/name search
8. URL-based filter state persistence
9. Mobile-responsive design
10. Loading skeletons

**Key Files**:
- `frontend/src/components/screener/DataGrid.tsx`
- `frontend/src/components/screener/FilterBar.tsx`
- `frontend/src/components/screener/SearchInput.tsx`

**Milestone**: Fully functional screener matching Bloomberg Terminal UX

---

### Phase 3: Real-Time Data Integration
**Goal**: Live price updates and historical charts

**Backend Tasks**:
```bash
pip install yfinance
```
- Create `backend/app/services/realtime_service.py`
- Implement 30-second price cache
- Add `/stocks/{ticker}/price` endpoint

**Frontend Tasks**:
```bash
npm install lightweight-charts recharts
```
- Create `PriceHeader.tsx` with auto-refresh
- Create `CandlestickChart.tsx` with TradingView style
- Implement period selector (1M/3M/6M/1Y/5Y)

**Milestone**: Real-time price updates every 30 seconds with interactive charts

---

### Phase 4: AI Data Extraction
**Goal**: Gemini-powered data normalization

**Tasks**:
```bash
pip install google-generativeai
```

1. Create `backend/app/services/ai_extractor.py`
2. Implement JSON truncation (select key sections only)
3. Build extraction prompt with StandardizedValuationInput schema
4. Add Pydantic validation for AI responses
5. Implement extraction cache (7-day TTL)
6. Add error handling and retry logic
7. Create confidence scoring
8. Rate limiting for Gemini API
9. Unit tests with mock responses

**Key Files**:
- `backend/app/services/ai_extractor.py`
- `backend/app/prompts/extraction_prompt.py`
- `backend/app/core/cache_manager.py`

**Milestone**: Reliable extraction of standardized inputs from any stock JSON

---

### Phase 5: Valuation Engine
**Goal**: Complete DCF + Graham calculations

**Tasks**:
1. Create `backend/app/services/valuation_engine.py`
2. Implement WACC calculation with dynamic credit spreads
3. Build DCF three-scenario model
4. Calculate terminal value with Gordon Growth
5. Implement Graham Number formula
6. Create Graham Defensive Screen (7 criteria)
7. Build composite valuation logic
8. Add sensitivity analysis
9. Implement valuation cache (24-hour TTL)
10. Comprehensive test coverage

**Key Files**:
- `backend/app/services/valuation_engine.py`
- `backend/app/models/valuation_output.py`
- `backend/tests/test_valuation_engine.py`

**Milestone**: Accurate valuations matching manual CFA calculations

---

### Phase 6: AI Investment Analyst
**Goal**: Warren Buffett-style investment memos

**Tasks**:
1. Create `backend/app/services/ai_analyst.py`
2. Build analysis prompt with Buffett persona
3. Implement WarrenBuffettAnalysis schema
4. Extract moat assessment
5. Categorize risks
6. Generate rating and conviction scores
7. Implement analysis cache (7-day TTL)
8. Create `/stocks/{ticker}/analysis` endpoint
9. Build AIAnalysis UI component
10. Add loading states for long AI calls

**Key Files**:
- `backend/app/services/ai_analyst.py`
- `backend/app/prompts/analysis_prompt.py`
- `frontend/src/components/stock/AIAnalysis.tsx`

**Milestone**: Compelling, consistent investment memos for all 10 stocks

---

### Phase 7: Polish & Production
**Goal**: Production-ready application

**Tasks**:
1. Error boundaries for all pages
2. Custom 404/500 error pages
3. Loading skeletons for all components
4. Mobile responsiveness audit
5. Performance optimization (lazy loading, code splitting)
6. API response compression (gzip)
7. Security headers (CORS, CSP)
8. Rate limiting middleware
9. Docker Compose setup
10. Environment configuration
11. API documentation (OpenAPI/Swagger)
12. README and user guide
13. End-to-end testing

**Milestone**: Deployable application ready for demo

---

## Appendix: API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stocks` | List all stocks with filtering/sorting |
| GET | `/api/v1/stocks/{ticker}` | Get full stock details |
| GET | `/api/v1/stocks/{ticker}/price` | Get real-time price (30s cache) |
| GET | `/api/v1/stocks/{ticker}/valuation` | Get AI-powered valuation |
| GET | `/api/v1/stocks/{ticker}/analysis` | Get Warren Buffett analysis |
| POST | `/api/v1/stocks/{ticker}/valuation/refresh` | Force valuation refresh |

---

## Appendix: Data Files Reference

| File | Size | Purpose |
|------|------|---------|
| `data/output/csv/summary.csv` | 7.7 KB | Screener data (51 columns, 10 stocks) |
| `data/output/json/AAPL.json` | 564 KB | Apple financial data (reference) |
| `data/output/json/MSFT.json` | 736 KB | Microsoft financial data |
| `data/output/json/GOOGL.json` | 762 KB | Alphabet financial data |
| `data/output/json/NVDA.json` | 685 KB | NVIDIA financial data |
| `data/output/json/TSLA.json` | 595 KB | Tesla financial data (edge case: no dividends) |

---

*Document Version: 1.0*
*Generated: January 7, 2026*
*Architecture: Senior Principal Software Architect + CFA Level 3*
