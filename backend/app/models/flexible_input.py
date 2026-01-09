"""
Flexible valuation input model - accepts whatever AI can extract.

This model has most fields optional, allowing the system to work
with partial data. The valuation engine adapts based on what's available.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Metadata(BaseModel):
    """Company metadata."""
    model_config = ConfigDict(extra="allow")

    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"


class MarketPosition(BaseModel):
    """Current market position."""
    model_config = ConfigDict(extra="allow")

    current_price: float
    shares_outstanding: Optional[float] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None


class TTMIncomeStatement(BaseModel):
    """Trailing twelve months income statement."""
    model_config = ConfigDict(extra="allow")

    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None
    operating_income: Optional[float] = None
    interest_expense: Optional[float] = None
    pretax_income: Optional[float] = None
    tax_expense: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None
    eps: Optional[float] = None


class TTMCashFlow(BaseModel):
    """Trailing twelve months cash flow."""
    model_config = ConfigDict(extra="allow")

    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    free_cash_flow: Optional[float] = None
    depreciation_amortization: Optional[float] = None
    stock_based_compensation: Optional[float] = None
    dividends_paid: Optional[float] = None
    share_repurchases: Optional[float] = None


class BalanceSheet(BaseModel):
    """Latest balance sheet."""
    model_config = ConfigDict(extra="allow")

    cash_and_equivalents: Optional[float] = None
    short_term_investments: Optional[float] = None
    total_cash: Optional[float] = None
    accounts_receivable: Optional[float] = None
    inventory: Optional[float] = None
    total_current_assets: Optional[float] = None
    property_plant_equipment: Optional[float] = None
    goodwill: Optional[float] = None
    intangible_assets: Optional[float] = None
    total_assets: Optional[float] = None
    accounts_payable: Optional[float] = None
    short_term_debt: Optional[float] = None
    total_current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    total_debt: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None
    retained_earnings: Optional[float] = None


class CalculatedMetrics(BaseModel):
    """Calculated position metrics."""
    model_config = ConfigDict(extra="allow")

    net_debt: Optional[float] = None
    working_capital: Optional[float] = None
    invested_capital: Optional[float] = None


class ProfitabilityRatios(BaseModel):
    """Profitability ratios."""
    model_config = ConfigDict(extra="allow")

    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None


class EfficiencyRatios(BaseModel):
    """Efficiency ratios."""
    model_config = ConfigDict(extra="allow")

    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None


class LeverageRatios(BaseModel):
    """Leverage ratios."""
    model_config = ConfigDict(extra="allow")

    debt_to_equity: Optional[float] = None
    debt_to_ebitda: Optional[float] = None
    interest_coverage: Optional[float] = None


class LiquidityRatios(BaseModel):
    """Liquidity ratios."""
    model_config = ConfigDict(extra="allow")

    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None


class ValuationMultiples(BaseModel):
    """Valuation multiples."""
    model_config = ConfigDict(extra="allow")

    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    fcf_yield: Optional[float] = None
    earnings_yield: Optional[float] = None


class GrowthRates(BaseModel):
    """Growth rates."""
    model_config = ConfigDict(extra="allow")

    revenue_growth_1y: Optional[float] = None
    revenue_growth_3y_cagr: Optional[float] = None
    revenue_growth_5y_cagr: Optional[float] = None
    revenue_growth_10y_cagr: Optional[float] = None
    earnings_growth_1y: Optional[float] = None
    earnings_growth_5y_cagr: Optional[float] = None
    fcf_growth_1y: Optional[float] = None
    fcf_growth_5y_cagr: Optional[float] = None


class RiskParameters(BaseModel):
    """Risk parameters."""
    model_config = ConfigDict(extra="allow")

    beta: Optional[float] = None
    risk_free_rate: float = 0.045


class Dividends(BaseModel):
    """Dividend information."""
    model_config = ConfigDict(extra="allow")

    dividend_per_share: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    years_of_dividend_growth: Optional[int] = None


class HistoricalYear(BaseModel):
    """Single year of historical financials."""
    model_config = ConfigDict(extra="allow")

    fiscal_year: int
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    free_cash_flow: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    depreciation_amortization: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    shareholders_equity: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None


class DataQuality(BaseModel):
    """Data quality information."""
    model_config = ConfigDict(extra="allow")

    fields_found: List[str] = Field(default_factory=list)
    fields_missing: List[str] = Field(default_factory=list)
    fields_calculated: List[str] = Field(default_factory=list)
    fields_estimated: List[str] = Field(default_factory=list)
    data_anomalies: List[str] = Field(default_factory=list)
    confidence_notes: Optional[str] = None


class FlexibleValuationInput(BaseModel):
    """
    Flexible valuation input - accepts whatever AI can extract.

    Most fields are optional, allowing partial data extraction.
    The valuation engine adapts based on what's available.
    """
    model_config = ConfigDict(extra="allow")

    # Required fields
    ticker: str
    company_name: str
    extraction_timestamp: datetime
    data_confidence_score: float = Field(ge=0.0, le=1.0)

    # Optional sections - AI fills what it can
    metadata: Metadata = Field(default_factory=Metadata)
    market_position: MarketPosition
    ttm_income_statement: TTMIncomeStatement = Field(default_factory=TTMIncomeStatement)
    ttm_cash_flow: TTMCashFlow = Field(default_factory=TTMCashFlow)
    balance_sheet: BalanceSheet = Field(default_factory=BalanceSheet)
    calculated_metrics: CalculatedMetrics = Field(default_factory=CalculatedMetrics)
    profitability_ratios: ProfitabilityRatios = Field(default_factory=ProfitabilityRatios)
    efficiency_ratios: EfficiencyRatios = Field(default_factory=EfficiencyRatios)
    leverage_ratios: LeverageRatios = Field(default_factory=LeverageRatios)
    liquidity_ratios: LiquidityRatios = Field(default_factory=LiquidityRatios)
    valuation_multiples: ValuationMultiples = Field(default_factory=ValuationMultiples)
    growth_rates: GrowthRates = Field(default_factory=GrowthRates)
    risk_parameters: RiskParameters = Field(default_factory=RiskParameters)
    dividends: Dividends = Field(default_factory=Dividends)
    historical_financials: List[HistoricalYear] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("historical_financials")
    @classmethod
    def sort_historical(cls, v: List[HistoricalYear]) -> List[HistoricalYear]:
        return sorted(v, key=lambda x: x.fiscal_year, reverse=True)

    # === Convenience methods to access data ===

    @property
    def has_dcf_data(self) -> bool:
        """Check if we have minimum data for DCF valuation."""
        return (
            self.ttm_cash_flow.free_cash_flow is not None or
            (self.ttm_cash_flow.operating_cash_flow is not None and
             self.ttm_cash_flow.capital_expenditures is not None)
        )

    @property
    def has_graham_data(self) -> bool:
        """Check if we have minimum data for Graham Number."""
        return (
            self.ttm_income_statement.eps is not None and
            self.balance_sheet.shareholders_equity is not None and
            self.market_position.shares_outstanding is not None
        )

    @property
    def fcf(self) -> Optional[float]:
        """Get free cash flow (direct or calculated)."""
        if self.ttm_cash_flow.free_cash_flow is not None:
            return self.ttm_cash_flow.free_cash_flow
        if (self.ttm_cash_flow.operating_cash_flow is not None and
            self.ttm_cash_flow.capital_expenditures is not None):
            return self.ttm_cash_flow.operating_cash_flow - abs(self.ttm_cash_flow.capital_expenditures)
        return None

    @property
    def book_value_per_share(self) -> Optional[float]:
        """Calculate book value per share."""
        if (self.balance_sheet.shareholders_equity is not None and
            self.market_position.shares_outstanding is not None and
            self.market_position.shares_outstanding > 0):
            return self.balance_sheet.shareholders_equity / self.market_position.shares_outstanding
        return None

    def get_growth_rate(self, years: int = 5) -> Optional[float]:
        """Get revenue growth rate for specified years."""
        if years == 1:
            return self.growth_rates.revenue_growth_1y
        elif years == 3:
            return self.growth_rates.revenue_growth_3y_cagr
        elif years == 5:
            return self.growth_rates.revenue_growth_5y_cagr
        elif years == 10:
            return self.growth_rates.revenue_growth_10y_cagr
        return None
