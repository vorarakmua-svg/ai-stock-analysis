"""
Pydantic models for stock data schemas.

Maps the 51 columns from summary.csv to a typed Pydantic model
with proper field aliases for columns with special characters.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StockSummary(BaseModel):
    """
    Pydantic model representing a stock row from summary.csv.

    Maps all 51 columns with proper type hints and aliases for
    columns containing special characters (e.g., 52_week_high).

    Attributes:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        cik: SEC Central Index Key
        company_name: Full company name
        sector: Business sector
        industry: Specific industry within sector
        current_price: Current stock price in USD
        ... (see individual field definitions)
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,  # Allow both alias and field name
        extra="ignore",  # Ignore extra fields from CSV
    )

    # === Identifiers ===
    ticker: str = Field(..., description="Stock ticker symbol")
    cik: Optional[str] = Field(None, description="SEC Central Index Key")
    company_name: Optional[str] = Field(None, description="Full company name")

    @field_validator("cik", mode="before")
    @classmethod
    def parse_cik(cls, v: Any) -> Optional[str]:
        """Convert CIK to string, handling int values from CSV."""
        if v is None:
            return None
        return str(v)

    # === Classification ===
    sector: Optional[str] = Field(None, description="Business sector")
    industry: Optional[str] = Field(None, description="Industry within sector")
    country: Optional[str] = Field(None, description="Country of incorporation")

    # === Price & Market Data ===
    current_price: Optional[float] = Field(None, description="Current stock price (USD)")
    market_cap: Optional[float] = Field(None, description="Market capitalization (USD)")
    volume: Optional[float] = Field(None, description="Trading volume")
    float_shares: Optional[float] = Field(None, description="Floating shares")
    shares_outstanding: Optional[float] = Field(None, description="Total shares outstanding")

    # === Valuation Ratios ===
    pe_trailing: Optional[float] = Field(None, description="Trailing P/E ratio")
    pe_forward: Optional[float] = Field(None, description="Forward P/E ratio")
    peg_ratio: Optional[float] = Field(None, description="PEG ratio")
    price_to_book: Optional[float] = Field(None, description="Price to book ratio")

    # === Per Share Data ===
    eps_trailing: Optional[float] = Field(None, description="Trailing EPS")
    eps_forward: Optional[float] = Field(None, description="Forward EPS")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield (decimal)")

    # === Risk Metrics ===
    beta: Optional[float] = Field(None, description="Beta (5Y monthly)")
    annual_volatility: Optional[float] = Field(None, description="Annual volatility")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    risk_free_rate_10y: Optional[float] = Field(
        None, alias="risk_free_rate_10y", description="10-year risk-free rate"
    )

    # === 52-Week Range (using aliases for numeric prefix) ===
    fifty_two_week_high: Optional[float] = Field(
        None, alias="52_week_high", description="52-week high price"
    )
    fifty_two_week_low: Optional[float] = Field(
        None, alias="52_week_low", description="52-week low price"
    )

    # === Moving Averages ===
    ma_50: Optional[float] = Field(None, description="50-day moving average")
    ma_200: Optional[float] = Field(None, description="200-day moving average")

    # === Income Statement ===
    total_revenue: Optional[float] = Field(None, description="Total revenue (USD)")
    net_income: Optional[float] = Field(None, description="Net income (USD)")
    ebitda: Optional[float] = Field(None, description="EBITDA (USD)")

    # === Balance Sheet ===
    total_cash: Optional[float] = Field(None, description="Total cash (USD)")
    total_debt: Optional[float] = Field(None, description="Total debt (USD)")
    debt_to_equity: Optional[float] = Field(None, description="Debt to equity ratio")

    # === Profitability Ratios ===
    profit_margin: Optional[float] = Field(None, description="Profit margin (decimal)")
    operating_margin: Optional[float] = Field(None, description="Operating margin (decimal)")
    return_on_equity: Optional[float] = Field(None, description="Return on equity (decimal)")
    return_on_assets: Optional[float] = Field(None, description="Return on assets (decimal)")

    # === Growth ===
    revenue_growth: Optional[float] = Field(None, description="Revenue growth rate (decimal)")
    cagr_5y: Optional[float] = Field(None, description="5-year CAGR")
    total_return_5y: Optional[float] = Field(None, description="5-year total return")

    # === Calculated Metrics (calc_ prefix) ===
    calc_ebitda: Optional[float] = Field(None, description="Calculated EBITDA")
    calc_ev: Optional[float] = Field(None, description="Calculated Enterprise Value")
    calc_ev_to_ebitda: Optional[float] = Field(None, description="Calculated EV/EBITDA")
    calc_fcf: Optional[float] = Field(None, description="Calculated Free Cash Flow")
    calc_interest_coverage: Optional[float] = Field(None, description="Calculated Interest Coverage")
    calc_net_debt: Optional[float] = Field(None, description="Calculated Net Debt")
    calc_roic: Optional[float] = Field(None, description="Calculated ROIC")

    # === Cash Flow ===
    free_cash_flow: Optional[float] = Field(None, description="Free cash flow (USD)")

    # === Company Info ===
    employees: Optional[int] = Field(None, description="Number of employees")
    website: Optional[str] = Field(None, description="Company website URL")

    # === Ownership ===
    insider_percent: Optional[float] = Field(None, description="Insider ownership percentage")
    institutional_percent: Optional[float] = Field(None, description="Institutional ownership percentage")
    short_ratio: Optional[float] = Field(None, description="Short ratio")

    # === SEC Data ===
    sec_fiscal_year: Optional[int] = Field(None, description="SEC fiscal year")
    sec_net_income: Optional[float] = Field(None, description="SEC reported net income")
    sec_operating_cash_flow: Optional[float] = Field(None, description="SEC operating cash flow")
    sec_revenue: Optional[float] = Field(None, description="SEC reported revenue")
    sec_stockholders_equity: Optional[float] = Field(None, description="SEC stockholders equity")
    sec_total_assets: Optional[float] = Field(None, description="SEC total assets")
    sec_total_liabilities: Optional[float] = Field(None, description="SEC total liabilities")

    # === Metadata ===
    collected_at: Optional[str] = Field(None, description="Data collection timestamp")
    data_sources: Optional[str] = Field(None, description="Data source identifiers")
    treasury_yield_source: Optional[str] = Field(None, description="Treasury yield data source")
    error_count: Optional[int] = Field(None, description="Number of data collection errors")
    warning_count: Optional[int] = Field(None, description="Number of data collection warnings")

    @field_validator("employees", mode="before")
    @classmethod
    def parse_employees(cls, v: Any) -> Optional[int]:
        """Convert employees to int, handling None and float values."""
        if v is None:
            return None
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None

    @field_validator(
        "sec_fiscal_year", "error_count", "warning_count",
        mode="before"
    )
    @classmethod
    def parse_int_fields(cls, v: Any) -> Optional[int]:
        """Convert integer fields, handling None and float values."""
        if v is None:
            return None
        try:
            return int(float(v))
        except (ValueError, TypeError):
            return None

    def to_display_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary suitable for display/API response.

        Returns field names (not aliases) for consistent API output.
        """
        return self.model_dump(by_alias=False, exclude_none=False)


class StockListResponse(BaseModel):
    """Response model for list of stocks."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    stocks: List[StockSummary] = Field(..., description="List of stock summaries")
    total: int = Field(..., description="Total number of stocks")
    columns: List[str] = Field(..., description="Available column names")


class StockMetadataResponse(BaseModel):
    """Response model for stock metadata (filters/dropdowns)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    columns: List[str] = Field(..., description="All available column names")
    sectors: List[str] = Field(..., description="Unique sector values")
    industries: List[str] = Field(..., description="Unique industry values")
    tickers: List[str] = Field(..., description="All available tickers")


class StockDetailResponse(BaseModel):
    """Response model for full stock JSON data."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    ticker: str = Field(..., description="Stock ticker symbol")
    data: Dict[str, Any] = Field(..., description="Full stock financial data")
