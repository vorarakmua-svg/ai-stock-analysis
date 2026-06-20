"""
Flexible valuation input model - accepts whatever AI can extract.

This model has most fields optional, allowing the system to work
with partial data. The valuation engine adapts based on what's available.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Metadata(BaseModel):
    """Company metadata."""

    model_config = ConfigDict(extra="allow")

    sector: str | None = None
    industry: str | None = None
    currency: str = "USD"


class MarketPosition(BaseModel):
    """Current market position."""

    model_config = ConfigDict(extra="allow")

    current_price: float
    shares_outstanding: float | None = None
    market_cap: float | None = None
    enterprise_value: float | None = None


class TTMIncomeStatement(BaseModel):
    """Trailing twelve months income statement."""

    model_config = ConfigDict(extra="allow")

    revenue: float | None = None
    cost_of_revenue: float | None = None
    gross_profit: float | None = None
    operating_expenses: float | None = None
    operating_income: float | None = None
    interest_expense: float | None = None
    pretax_income: float | None = None
    tax_expense: float | None = None
    net_income: float | None = None
    ebitda: float | None = None
    eps: float | None = None


class TTMCashFlow(BaseModel):
    """Trailing twelve months cash flow."""

    model_config = ConfigDict(extra="allow")

    operating_cash_flow: float | None = None
    capital_expenditures: float | None = None
    free_cash_flow: float | None = None
    depreciation_amortization: float | None = None
    stock_based_compensation: float | None = None
    dividends_paid: float | None = None
    share_repurchases: float | None = None


class BalanceSheet(BaseModel):
    """Latest balance sheet."""

    model_config = ConfigDict(extra="allow")

    cash_and_equivalents: float | None = None
    short_term_investments: float | None = None
    total_cash: float | None = None
    accounts_receivable: float | None = None
    inventory: float | None = None
    total_current_assets: float | None = None
    property_plant_equipment: float | None = None
    goodwill: float | None = None
    intangible_assets: float | None = None
    total_assets: float | None = None
    accounts_payable: float | None = None
    short_term_debt: float | None = None
    total_current_liabilities: float | None = None
    long_term_debt: float | None = None
    total_debt: float | None = None
    total_liabilities: float | None = None
    shareholders_equity: float | None = None
    retained_earnings: float | None = None


class CalculatedMetrics(BaseModel):
    """Calculated position metrics."""

    model_config = ConfigDict(extra="allow")

    net_debt: float | None = None
    working_capital: float | None = None
    invested_capital: float | None = None


class ProfitabilityRatios(BaseModel):
    """Profitability ratios."""

    model_config = ConfigDict(extra="allow")

    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    ebitda_margin: float | None = None
    roe: float | None = None
    roa: float | None = None
    roic: float | None = None


class EfficiencyRatios(BaseModel):
    """Efficiency ratios."""

    model_config = ConfigDict(extra="allow")

    asset_turnover: float | None = None
    inventory_turnover: float | None = None
    receivables_turnover: float | None = None


class LeverageRatios(BaseModel):
    """Leverage ratios."""

    model_config = ConfigDict(extra="allow")

    debt_to_equity: float | None = None
    debt_to_ebitda: float | None = None
    interest_coverage: float | None = None


class LiquidityRatios(BaseModel):
    """Liquidity ratios."""

    model_config = ConfigDict(extra="allow")

    current_ratio: float | None = None
    quick_ratio: float | None = None
    cash_ratio: float | None = None


class ValuationMultiples(BaseModel):
    """Valuation multiples."""

    model_config = ConfigDict(extra="allow")

    pe_ratio: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    price_to_sales: float | None = None
    ev_to_ebitda: float | None = None
    ev_to_revenue: float | None = None
    fcf_yield: float | None = None
    earnings_yield: float | None = None


class GrowthRates(BaseModel):
    """Growth rates."""

    model_config = ConfigDict(extra="allow")

    revenue_growth_1y: float | None = None
    revenue_growth_3y_cagr: float | None = None
    revenue_growth_5y_cagr: float | None = None
    revenue_growth_10y_cagr: float | None = None
    earnings_growth_1y: float | None = None
    earnings_growth_5y_cagr: float | None = None
    fcf_growth_1y: float | None = None
    fcf_growth_5y_cagr: float | None = None


class RiskParameters(BaseModel):
    """Risk parameters."""

    model_config = ConfigDict(extra="allow")

    beta: float | None = None
    risk_free_rate: float = 0.045


class Dividends(BaseModel):
    """Dividend information."""

    model_config = ConfigDict(extra="allow")

    dividend_per_share: float | None = None
    dividend_yield: float | None = None
    payout_ratio: float | None = None
    years_of_dividend_growth: int | None = None


class HistoricalYear(BaseModel):
    """Single year of historical financials."""

    model_config = ConfigDict(extra="allow")

    fiscal_year: int
    revenue: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None
    net_income: float | None = None
    eps: float | None = None
    free_cash_flow: float | None = None
    operating_cash_flow: float | None = None
    capital_expenditures: float | None = None
    depreciation_amortization: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    shareholders_equity: float | None = None
    total_debt: float | None = None
    cash_and_equivalents: float | None = None


class DataQuality(BaseModel):
    """Data quality information."""

    model_config = ConfigDict(extra="allow")

    fields_found: list[str] = Field(default_factory=list)
    fields_missing: list[str] = Field(default_factory=list)
    fields_calculated: list[str] = Field(default_factory=list)
    fields_estimated: list[str] = Field(default_factory=list)
    data_anomalies: list[str] = Field(default_factory=list)
    confidence_notes: str | None = None


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
    historical_financials: list[HistoricalYear] = Field(default_factory=list)
    data_quality: DataQuality = Field(default_factory=DataQuality)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("historical_financials")
    @classmethod
    def sort_historical(cls, v: list[HistoricalYear]) -> list[HistoricalYear]:
        return sorted(v, key=lambda x: x.fiscal_year, reverse=True)

    # === Convenience methods to access data ===

    @property
    def has_dcf_data(self) -> bool:
        """Check if we have minimum data for DCF valuation."""
        return self.ttm_cash_flow.free_cash_flow is not None or (
            self.ttm_cash_flow.operating_cash_flow is not None
            and self.ttm_cash_flow.capital_expenditures is not None
        )

    @property
    def has_graham_data(self) -> bool:
        """Check if we have minimum data for Graham Number."""
        return (
            self.ttm_income_statement.eps is not None
            and self.balance_sheet.shareholders_equity is not None
            and self.market_position.shares_outstanding is not None
        )

    @property
    def fcf(self) -> float | None:
        """Get free cash flow (direct or calculated)."""
        if self.ttm_cash_flow.free_cash_flow is not None:
            return self.ttm_cash_flow.free_cash_flow
        if (
            self.ttm_cash_flow.operating_cash_flow is not None
            and self.ttm_cash_flow.capital_expenditures is not None
        ):
            return self.ttm_cash_flow.operating_cash_flow - abs(
                self.ttm_cash_flow.capital_expenditures
            )
        return None

    @property
    def book_value_per_share(self) -> float | None:
        """Calculate book value per share."""
        if (
            self.balance_sheet.shareholders_equity is not None
            and self.market_position.shares_outstanding is not None
            and self.market_position.shares_outstanding > 0
        ):
            return self.balance_sheet.shareholders_equity / self.market_position.shares_outstanding
        return None

    def get_growth_rate(self, years: int = 5) -> float | None:
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
