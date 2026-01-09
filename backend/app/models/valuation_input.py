"""
Pydantic models for standardized valuation input data.

This module defines the StandardizedValuationInput schema that AI extracts
from raw JSON data. It normalizes messy financial data into clean, validated
inputs suitable for DCF and Graham valuation calculations.

The schema follows CFA standards:
- Historical: 10 years (full economic cycle)
- Projections: 5 years explicit + terminal value
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HistoricalFinancials(BaseModel):
    """
    Single year of financial data for trend analysis.

    Used to store 10 years of historical data for CAGR calculations
    and trend analysis per CFA standards.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    fiscal_year: int = Field(
        ...,
        description="Fiscal year (e.g., 2024)",
        ge=1900,
        le=2100,
    )
    revenue: float = Field(
        ...,
        description="Total revenue / Net sales for the year",
    )
    gross_profit: float = Field(
        ...,
        description="Gross profit (Revenue - COGS)",
    )
    operating_income: float = Field(
        ...,
        description="Operating income / EBIT",
    )
    net_income: float = Field(
        ...,
        description="Net income attributable to shareholders",
    )
    free_cash_flow: Optional[float] = Field(
        None,
        description="Free cash flow (OCF - CapEx)",
    )
    eps: float = Field(
        ...,
        description="Earnings per share (diluted)",
    )
    depreciation_amortization: float = Field(
        ...,
        description="Depreciation and amortization expense",
    )
    capital_expenditures: float = Field(
        ...,
        description="Capital expenditures (positive value)",
    )
    total_assets: float = Field(
        ...,
        description="Total assets at year end",
    )
    total_liabilities: float = Field(
        ...,
        description="Total liabilities at year end",
    )
    shareholders_equity: float = Field(
        ...,
        description="Total shareholders' equity at year end",
    )
    total_debt: float = Field(
        ...,
        description="Total debt (short-term + long-term)",
    )
    cash_and_equivalents: float = Field(
        ...,
        description="Cash and cash equivalents at year end",
    )


class StandardizedValuationInput(BaseModel):
    """
    AI-normalized valuation inputs for DCF/Graham formulas.

    Gemini extracts and standardizes from messy JSON data. This schema
    serves as the contract between the AI extraction layer and the
    Python valuation engine.

    TIME HORIZONS (CFA Standard):
    - Historical: 10 years (full economic cycle)
    - Projections: 5 years explicit + terminal value

    All monetary values are in USD.
    All ratios are in decimal form (e.g., 15% = 0.15).
    All growth rates are annualized CAGRs.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # === Metadata ===
    ticker: str = Field(
        ...,
        description="Stock ticker symbol",
        min_length=1,
        max_length=10,
    )
    company_name: str = Field(
        ...,
        description="Full company name",
        min_length=1,
    )
    sector: str = Field(
        ...,
        description="GICS sector classification",
    )
    industry: str = Field(
        ...,
        description="GICS industry classification",
    )
    extraction_timestamp: datetime = Field(
        ...,
        description="Timestamp when data was extracted",
    )
    data_confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI's confidence in data extraction quality (0.0-1.0)",
    )

    # === Current Market Position ===
    current_price: float = Field(
        ...,
        description="Current stock price per share",
        gt=0,
    )
    shares_outstanding: float = Field(
        ...,
        description="Total shares outstanding",
        gt=0,
    )
    market_cap: float = Field(
        ...,
        description="Market capitalization (price * shares)",
        gt=0,
    )
    enterprise_value: float = Field(
        ...,
        description="Enterprise value (market cap + debt - cash)",
    )

    # === Income Statement (TTM - Trailing Twelve Months) ===
    ttm_revenue: float = Field(
        ...,
        description="TTM total revenue / net sales",
    )
    ttm_cost_of_revenue: float = Field(
        ...,
        description="TTM cost of goods sold / cost of revenue",
    )
    ttm_gross_profit: float = Field(
        ...,
        description="TTM gross profit (revenue - COGS)",
    )
    ttm_operating_expenses: float = Field(
        ...,
        description="TTM operating expenses (SG&A + R&D + other)",
    )
    ttm_operating_income: float = Field(
        ...,
        description="TTM operating income / EBIT",
    )
    ttm_interest_expense: Optional[float] = Field(
        None,
        description="TTM interest expense (if applicable)",
    )
    ttm_pretax_income: float = Field(
        ...,
        description="TTM income before taxes",
    )
    ttm_tax_expense: float = Field(
        ...,
        description="TTM income tax expense",
    )
    ttm_net_income: float = Field(
        ...,
        description="TTM net income attributable to shareholders",
    )
    ttm_ebitda: float = Field(
        ...,
        description="TTM EBITDA",
    )
    ttm_eps: float = Field(
        ...,
        description="TTM diluted earnings per share",
    )

    # === Cash Flow Statement (TTM) ===
    ttm_operating_cash_flow: Optional[float] = Field(
        None,
        description="TTM cash flow from operations",
    )
    ttm_capital_expenditures: Optional[float] = Field(
        None,
        description="TTM capital expenditures (positive value)",
    )
    ttm_free_cash_flow: Optional[float] = Field(
        None,
        description="TTM free cash flow (OCF - CapEx)",
    )
    ttm_depreciation_amortization: float = Field(
        ...,
        description="TTM depreciation and amortization",
    )
    ttm_stock_based_compensation: Optional[float] = Field(
        None,
        description="TTM stock-based compensation expense",
    )
    ttm_dividends_paid: Optional[float] = Field(
        None,
        description="TTM dividends paid (positive value)",
    )
    ttm_share_repurchases: Optional[float] = Field(
        None,
        description="TTM share repurchases (positive value)",
    )

    # === Balance Sheet (Latest Quarter) ===
    cash_and_equivalents: float = Field(
        ...,
        description="Cash and cash equivalents",
        ge=0,
    )
    short_term_investments: Optional[float] = Field(
        None,
        description="Short-term / marketable securities",
        ge=0,
    )
    total_cash: float = Field(
        ...,
        description="Total cash (cash + short-term investments)",
        ge=0,
    )
    accounts_receivable: float = Field(
        ...,
        description="Accounts receivable, net",
        ge=0,
    )
    inventory: Optional[float] = Field(
        None,
        description="Inventory (if applicable for the industry)",
        ge=0,
    )
    total_current_assets: float = Field(
        ...,
        description="Total current assets",
        ge=0,
    )
    property_plant_equipment: float = Field(
        ...,
        description="Property, plant & equipment, net",
        ge=0,
    )
    goodwill: Optional[float] = Field(
        None,
        description="Goodwill from acquisitions",
        ge=0,
    )
    intangible_assets: Optional[float] = Field(
        None,
        description="Intangible assets, net",
        ge=0,
    )
    total_assets: float = Field(
        ...,
        description="Total assets",
        gt=0,
    )
    accounts_payable: float = Field(
        ...,
        description="Accounts payable",
        ge=0,
    )
    short_term_debt: float = Field(
        ...,
        description="Short-term debt / current portion of LT debt",
        ge=0,
    )
    total_current_liabilities: float = Field(
        ...,
        description="Total current liabilities",
        ge=0,
    )
    long_term_debt: float = Field(
        ...,
        description="Long-term debt (non-current)",
        ge=0,
    )
    total_debt: float = Field(
        ...,
        description="Total debt (short-term + long-term)",
        ge=0,
    )
    total_liabilities: float = Field(
        ...,
        description="Total liabilities",
        ge=0,
    )
    shareholders_equity: float = Field(
        ...,
        description="Total shareholders' equity",
    )
    retained_earnings: float = Field(
        ...,
        description="Retained earnings / accumulated deficit",
    )

    # === Calculated Position Metrics ===
    net_debt: float = Field(
        ...,
        description="Net debt (total_debt - total_cash)",
    )
    working_capital: float = Field(
        ...,
        description="Working capital (current_assets - current_liabilities)",
    )
    invested_capital: float = Field(
        ...,
        description="Invested capital (equity + debt - cash)",
    )

    # === Profitability Ratios ===
    gross_margin: float = Field(
        ...,
        description="Gross margin (Gross Profit / Revenue)",
    )
    operating_margin: float = Field(
        ...,
        description="Operating margin (Operating Income / Revenue)",
    )
    net_margin: float = Field(
        ...,
        description="Net margin (Net Income / Revenue)",
    )
    ebitda_margin: float = Field(
        ...,
        description="EBITDA margin (EBITDA / Revenue)",
    )
    roe: float = Field(
        ...,
        description="Return on Equity (Net Income / Shareholders Equity)",
    )
    roa: float = Field(
        ...,
        description="Return on Assets (Net Income / Total Assets)",
    )
    roic: Optional[float] = Field(
        None,
        description="Return on Invested Capital (NOPAT / Invested Capital)",
    )

    # === Efficiency Ratios ===
    asset_turnover: float = Field(
        ...,
        description="Asset turnover (Revenue / Total Assets)",
    )
    inventory_turnover: Optional[float] = Field(
        None,
        description="Inventory turnover (COGS / Average Inventory)",
    )
    receivables_turnover: Optional[float] = Field(
        None,
        description="Receivables turnover (Revenue / Avg Receivables)",
    )

    # === Leverage Ratios ===
    debt_to_equity: float = Field(
        ...,
        description="Debt-to-equity ratio (Total Debt / Equity)",
    )
    debt_to_ebitda: Optional[float] = Field(
        None,
        description="Debt-to-EBITDA ratio",
    )
    interest_coverage: Optional[float] = Field(
        None,
        description="Interest coverage ratio (EBIT / Interest Expense)",
    )

    # === Liquidity Ratios ===
    current_ratio: float = Field(
        ...,
        description="Current ratio (Current Assets / Current Liabilities)",
    )
    quick_ratio: float = Field(
        ...,
        description="Quick ratio ((Current Assets - Inventory) / Current Liabilities)",
    )
    cash_ratio: float = Field(
        ...,
        description="Cash ratio (Cash / Current Liabilities)",
    )

    # === Valuation Multiples (Current) ===
    pe_ratio: Optional[float] = Field(
        None,
        description="Price-to-Earnings ratio (Price / EPS)",
    )
    forward_pe: Optional[float] = Field(
        None,
        description="Forward P/E ratio (Price / Forward EPS)",
    )
    peg_ratio: Optional[float] = Field(
        None,
        description="PEG ratio (P/E / Earnings Growth Rate)",
    )
    price_to_book: Optional[float] = Field(
        None,
        description="Price-to-Book ratio (Price / Book Value per Share)",
    )
    price_to_sales: Optional[float] = Field(
        None,
        description="Price-to-Sales ratio (Market Cap / Revenue)",
    )
    ev_to_ebitda: Optional[float] = Field(
        None,
        description="EV/EBITDA multiple",
    )
    ev_to_revenue: Optional[float] = Field(
        None,
        description="EV/Revenue multiple",
    )
    fcf_yield: Optional[float] = Field(
        None,
        description="Free cash flow yield (FCF / Market Cap)",
    )
    earnings_yield: Optional[float] = Field(
        None,
        description="Earnings yield (EPS / Price)",
    )

    # === Growth Rates (Calculated from Historical Data) ===
    revenue_growth_1y: Optional[float] = Field(
        None,
        description="Revenue growth rate (1 year)",
    )
    revenue_growth_3y_cagr: Optional[float] = Field(
        None,
        description="Revenue CAGR (3 years)",
    )
    revenue_growth_5y_cagr: Optional[float] = Field(
        None,
        description="Revenue CAGR (5 years)",
    )
    revenue_growth_10y_cagr: Optional[float] = Field(
        None,
        description="Revenue CAGR (10 years)",
    )
    earnings_growth_1y: Optional[float] = Field(
        None,
        description="Net income growth rate (1 year)",
    )
    earnings_growth_3y_cagr: Optional[float] = Field(
        None,
        description="Net income CAGR (3 years)",
    )
    earnings_growth_5y_cagr: Optional[float] = Field(
        None,
        description="Net income CAGR (5 years)",
    )
    earnings_growth_10y_cagr: Optional[float] = Field(
        None,
        description="Net income CAGR (10 years)",
    )
    fcf_growth_1y: Optional[float] = Field(
        None,
        description="Free cash flow growth rate (1 year)",
    )
    fcf_growth_3y_cagr: Optional[float] = Field(
        None,
        description="Free cash flow CAGR (3 years)",
    )
    fcf_growth_5y_cagr: Optional[float] = Field(
        None,
        description="Free cash flow CAGR (5 years)",
    )

    # === Risk Parameters ===
    beta: Optional[float] = Field(
        None,
        description="5-year monthly beta vs S&P 500",
    )
    risk_free_rate: float = Field(
        ...,
        description="10-year Treasury yield (as decimal)",
        ge=0,
        le=0.20,  # Sanity check: max 20%
    )
    equity_risk_premium: float = Field(
        default=0.05,
        description="Market equity risk premium (default 5%)",
        ge=0.01,
        le=0.15,
    )

    # === Dividend Information ===
    dividend_per_share: Optional[float] = Field(
        None,
        description="Annual dividend per share",
        ge=0,
    )
    dividend_yield: Optional[float] = Field(
        None,
        description="Dividend yield (DPS / Price)",
        ge=0,
    )
    payout_ratio: Optional[float] = Field(
        None,
        description="Payout ratio (Dividends / Net Income)",
        ge=0,
    )
    dividend_growth_5y: Optional[float] = Field(
        None,
        description="5-year dividend growth CAGR",
    )
    years_of_dividend_growth: Optional[int] = Field(
        None,
        description="Consecutive years of dividend increases",
        ge=0,
    )

    # === Historical Data (10 Years - CFA Standard) ===
    historical_financials: List[HistoricalFinancials] = Field(
        ...,
        description="10 years of annual financial data, most recent first",
        min_length=1,
        max_length=15,
    )

    # === Data Quality Flags ===
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Fields that could not be extracted from source data",
    )
    estimated_fields: List[str] = Field(
        default_factory=list,
        description="Fields that were estimated or calculated by AI",
    )
    data_anomalies: List[str] = Field(
        default_factory=list,
        description="Data quality warnings and anomalies detected",
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Ensure ticker is uppercase and stripped."""
        return v.upper().strip()

    @field_validator("historical_financials")
    @classmethod
    def validate_historical_order(
        cls,
        v: List[HistoricalFinancials],
    ) -> List[HistoricalFinancials]:
        """Ensure historical data is sorted by fiscal year (most recent first)."""
        return sorted(v, key=lambda x: x.fiscal_year, reverse=True)
