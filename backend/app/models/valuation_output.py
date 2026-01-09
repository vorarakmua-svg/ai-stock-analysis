"""
Pydantic models for valuation output data.

This module defines the complete schema for valuation results including:
- DCF (Discounted Cash Flow) valuations with multiple scenarios
- Graham Number calculations
- Graham Defensive Screen criteria
- Composite valuation results with verdict

All mathematical calculations are performed in Python (valuation_engine.py),
NOT by AI. The AI layer only handles data extraction and normalization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ValuationVerdict(str, Enum):
    """
    Investment verdict based on upside/downside potential.

    Thresholds (based on margin of safety principles):
    - SIGNIFICANTLY_UNDERVALUED: >40% upside potential
    - UNDERVALUED: 15-40% upside potential
    - FAIRLY_VALUED: -15% to +15% (within normal valuation range)
    - OVERVALUED: 15-40% downside risk
    - SIGNIFICANTLY_OVERVALUED: >40% downside risk
    """

    SIGNIFICANTLY_UNDERVALUED = "significantly_undervalued"
    UNDERVALUED = "undervalued"
    FAIRLY_VALUED = "fairly_valued"
    OVERVALUED = "overvalued"
    SIGNIFICANTLY_OVERVALUED = "significantly_overvalued"


class DCFScenario(BaseModel):
    """
    Single DCF (Discounted Cash Flow) scenario calculation.

    Each scenario represents a different set of assumptions about
    future growth and profitability. Three scenarios are typically
    computed: conservative, base case, and optimistic.

    The DCF methodology follows CFA standards:
    - 5-year explicit forecast period
    - Terminal value using Gordon Growth Model
    - WACC as discount rate
    - FCFF (Free Cash Flow to Firm) approach
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # Scenario identification
    scenario_name: str = Field(
        ...,
        description="Scenario name: 'conservative', 'base_case', or 'optimistic'",
    )

    # Key assumptions
    revenue_growth_rate: float = Field(
        ...,
        description="Annual revenue growth rate assumption (as decimal)",
    )
    operating_margin_assumption: float = Field(
        ...,
        description="Operating margin assumption for projections (as decimal)",
    )
    terminal_growth_rate: float = Field(
        ...,
        description="Perpetual growth rate for terminal value (as decimal)",
    )
    wacc: float = Field(
        ...,
        description="Weighted Average Cost of Capital used for discounting",
    )

    # Projection details
    projection_years: int = Field(
        default=5,
        description="Number of years in explicit forecast period",
        ge=3,
        le=10,
    )
    projected_revenue: List[float] = Field(
        ...,
        description="Projected revenue for each forecast year",
    )
    projected_ebit: List[float] = Field(
        ...,
        description="Projected EBIT (Operating Income) for each forecast year",
    )
    projected_nopat: List[float] = Field(
        ...,
        description="Projected NOPAT (Net Operating Profit After Tax) for each year",
    )
    projected_fcf: List[float] = Field(
        ...,
        description="Projected Free Cash Flow for each forecast year",
    )

    # Terminal value calculations
    terminal_fcf: float = Field(
        ...,
        description="Terminal year FCF used for terminal value calculation",
    )
    terminal_value: float = Field(
        ...,
        description="Terminal value (perpetuity value of cash flows beyond forecast)",
    )

    # Present value calculations
    pv_explicit_period: float = Field(
        ...,
        description="Present value of explicit forecast period cash flows",
    )
    pv_terminal_value: float = Field(
        ...,
        description="Present value of terminal value",
    )

    # Valuation results
    enterprise_value: float = Field(
        ...,
        description="Enterprise Value (PV of explicit + PV of terminal)",
    )
    equity_value: float = Field(
        ...,
        description="Equity Value (EV - Net Debt)",
    )
    intrinsic_value_per_share: float = Field(
        ...,
        description="Intrinsic value per share (Equity Value / Shares Outstanding)",
    )

    # Comparison to market
    current_price: float = Field(
        ...,
        description="Current market price per share",
        gt=0,
    )
    upside_downside_pct: float = Field(
        ...,
        description="Percentage upside (+) or downside (-) from current price",
    )


class DCFValuation(BaseModel):
    """
    Complete DCF valuation analysis with three scenarios.

    This model contains:
    - Cost of capital calculations (WACC and components)
    - Three DCF scenarios with different assumptions
    - Probability-weighted intrinsic value
    - Sensitivity analysis results

    The WACC calculation follows CAPM (Capital Asset Pricing Model):
    - Cost of Equity = Risk-free Rate + Beta * Equity Risk Premium
    - Cost of Debt = Risk-free Rate + Credit Spread
    - WACC = (E/V * CoE) + (D/V * CoD * (1 - Tax Rate))
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # Metadata
    calculation_timestamp: datetime = Field(
        ...,
        description="Timestamp when valuation was calculated",
    )
    methodology: str = Field(
        default="Discounted Cash Flow (FCFF)",
        description="Valuation methodology used",
    )

    # Cost of equity (CAPM) components
    risk_free_rate: float = Field(
        ...,
        description="Risk-free rate (10-year Treasury yield)",
    )
    beta: float = Field(
        ...,
        description="Stock beta (5-year monthly vs S&P 500)",
    )
    equity_risk_premium: float = Field(
        ...,
        description="Equity risk premium (market risk premium)",
    )
    cost_of_equity: float = Field(
        ...,
        description="Cost of equity from CAPM: Rf + Beta * ERP",
    )

    # Cost of debt components
    cost_of_debt_pretax: float = Field(
        ...,
        description="Pre-tax cost of debt: Rf + Credit Spread",
    )
    tax_rate: float = Field(
        ...,
        description="Corporate tax rate (default: 21% US federal)",
    )
    cost_of_debt_aftertax: float = Field(
        ...,
        description="After-tax cost of debt: CoD * (1 - Tax Rate)",
    )

    # Capital structure weights
    debt_weight: float = Field(
        ...,
        description="Debt weight in capital structure (D/V)",
    )
    equity_weight: float = Field(
        ...,
        description="Equity weight in capital structure (E/V)",
    )
    wacc: float = Field(
        ...,
        description="Weighted Average Cost of Capital",
    )

    # Three scenarios
    conservative: DCFScenario = Field(
        ...,
        description="Conservative scenario with reduced growth assumptions",
    )
    base_case: DCFScenario = Field(
        ...,
        description="Base case scenario using historical growth trends",
    )
    optimistic: DCFScenario = Field(
        ...,
        description="Optimistic scenario with enhanced growth assumptions",
    )

    # Probability weighting
    scenario_weights: Dict[str, float] = Field(
        default={
            "conservative": 0.25,
            "base_case": 0.50,
            "optimistic": 0.25,
        },
        description="Probability weights for each scenario",
    )
    weighted_intrinsic_value: float = Field(
        ...,
        description="Probability-weighted intrinsic value per share",
    )

    # Sensitivity analysis
    sensitivity_to_wacc: Dict[str, float] = Field(
        ...,
        description="Intrinsic value sensitivity to WACC changes (+/- 1%)",
    )
    sensitivity_to_growth: Dict[str, float] = Field(
        ...,
        description="Intrinsic value sensitivity to terminal growth changes (+/- 1%)",
    )


class GrahamNumber(BaseModel):
    """
    Benjamin Graham's intrinsic value formula.

    The Graham Number is a conservative estimate of intrinsic value:
    Graham Number = sqrt(22.5 * EPS * BVPS)

    Where:
    - 22.5 = 15 (max P/E) * 1.5 (max P/B) - Graham's conservative limits
    - EPS = Trailing Twelve Months Earnings Per Share
    - BVPS = Book Value Per Share (Shareholders Equity / Shares)

    This formula only produces a value when both EPS and BVPS are positive,
    representing companies with real earnings and positive net worth.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    methodology: str = Field(
        default="Graham Number = sqrt(22.5 * EPS * BVPS)",
        description="Formula description",
    )

    # Input values
    eps_ttm: float = Field(
        ...,
        description="Trailing Twelve Months Earnings Per Share",
    )
    book_value_per_share: float = Field(
        ...,
        description="Book Value Per Share (Equity / Shares)",
    )
    graham_multiplier: float = Field(
        default=22.5,
        description="Graham's P/E * P/B limit (15 * 1.5 = 22.5)",
    )

    # Result
    graham_number: float = Field(
        ...,
        description="Calculated Graham Number (intrinsic value estimate)",
        ge=0,
    )
    current_price: float = Field(
        ...,
        description="Current market price per share",
        gt=0,
    )
    upside_pct: float = Field(
        ...,
        description="Percentage upside (+) or downside (-) to Graham Number",
    )


class GrahamDefensiveCriteria(BaseModel):
    """
    Benjamin Graham's 7 criteria for the defensive investor.

    From "The Intelligent Investor" - these criteria identify financially
    strong, stable companies trading at reasonable valuations. Originally
    designed for conservative, long-term investors seeking safety.

    A company passing 5 or more criteria is considered a defensive investment.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # Criterion 1: Adequate Size
    adequate_size: bool = Field(
        ...,
        description="Passes size criterion (revenue >= $700M)",
    )
    revenue_minimum: float = Field(
        default=700_000_000.0,
        description="Minimum revenue threshold for adequate size ($700M)",
    )
    actual_revenue: float = Field(
        ...,
        description="Company's actual TTM revenue",
    )

    # Criterion 2: Strong Financial Condition
    strong_financial_condition: bool = Field(
        ...,
        description="Passes financial condition (current ratio >= 2.0)",
    )
    current_ratio_minimum: float = Field(
        default=2.0,
        description="Minimum current ratio for strong finances",
    )
    actual_current_ratio: float = Field(
        ...,
        description="Company's actual current ratio",
    )

    # Criterion 3: Earnings Stability
    earnings_stability: bool = Field(
        ...,
        description="Passes earnings stability (10 years positive earnings)",
    )
    years_positive_earnings: int = Field(
        ...,
        description="Number of years with positive net income",
        ge=0,
    )
    required_years: int = Field(
        default=10,
        description="Required years of positive earnings",
    )

    # Criterion 4: Dividend Record
    dividend_record: bool = Field(
        ...,
        description="Passes dividend record (dividend paying)",
    )
    years_dividends_paid: int = Field(
        ...,
        description="Years of dividend payments",
        ge=0,
    )
    required_dividend_years: int = Field(
        default=20,
        description="Required years of dividend payments (Graham: 20 years)",
    )

    # Criterion 5: Earnings Growth
    earnings_growth: bool = Field(
        ...,
        description="Passes earnings growth (EPS growth > 33% over 10 years)",
    )
    eps_10y_growth: Optional[float] = Field(
        None,
        description="EPS growth over 10 years (as decimal)",
    )
    required_growth: float = Field(
        default=0.33,
        description="Required 10-year EPS growth (33%)",
    )

    # Criterion 6: Moderate P/E Ratio
    moderate_pe: bool = Field(
        ...,
        description="Passes P/E criterion (P/E <= 15)",
    )
    pe_maximum: float = Field(
        default=15.0,
        description="Maximum acceptable P/E ratio",
    )
    actual_pe: Optional[float] = Field(
        None,
        description="Company's actual P/E ratio",
    )

    # Criterion 7: Moderate Price-to-Book
    moderate_pb: bool = Field(
        ...,
        description="Passes P/B criterion (P/B <= 1.5)",
    )
    pb_maximum: float = Field(
        default=1.5,
        description="Maximum acceptable P/B ratio",
    )
    actual_pb: Optional[float] = Field(
        None,
        description="Company's actual P/B ratio",
    )

    # Combined P/E * P/B criterion (alternative to separate P/E and P/B tests)
    graham_product: Optional[float] = Field(
        None,
        description="P/E * P/B product (should be < 22.5)",
    )
    graham_product_passes: bool = Field(
        ...,
        description="Whether P/E * P/B < 22.5",
    )

    # Summary
    criteria_passed: int = Field(
        ...,
        description="Number of criteria passed (out of 7)",
        ge=0,
        le=7,
    )
    total_criteria: int = Field(
        default=7,
        description="Total number of criteria",
    )
    passes_screen: bool = Field(
        ...,
        description="Whether stock passes defensive screen (>= 5 criteria)",
    )


class ValuationResult(BaseModel):
    """
    Complete valuation output combining all valuation methods.

    This is the primary response model for the valuation API endpoint.
    It aggregates:
    - DCF valuation with multiple scenarios
    - Graham Number calculation
    - Graham Defensive Screen results
    - Composite intrinsic value (weighted average)
    - Final investment verdict

    The composite methodology weights DCF (60%) and Graham Number (40%)
    to balance growth-oriented DCF with conservative Graham approach.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # Identification
    ticker: str = Field(
        ...,
        description="Stock ticker symbol",
    )
    company_name: str = Field(
        ...,
        description="Company name",
    )
    calculation_timestamp: datetime = Field(
        ...,
        description="Timestamp when valuation was calculated",
    )

    # Current market data
    current_price: float = Field(
        ...,
        description="Current stock price per share",
        gt=0,
    )
    market_cap: float = Field(
        ...,
        description="Market capitalization",
        gt=0,
    )
    enterprise_value: float = Field(
        ...,
        description="Enterprise value (Market Cap + Net Debt)",
    )
    shares_outstanding: float = Field(
        ...,
        description="Total shares outstanding",
        gt=0,
    )

    # Valuation components
    dcf_valuation: DCFValuation = Field(
        ...,
        description="Complete DCF valuation analysis",
    )
    graham_number: GrahamNumber = Field(
        ...,
        description="Graham Number calculation",
    )
    graham_defensive_screen: GrahamDefensiveCriteria = Field(
        ...,
        description="Graham defensive investor criteria screening",
    )

    # Composite valuation
    valuation_methods_used: List[str] = Field(
        ...,
        description="List of valuation methods applied",
    )
    composite_intrinsic_value: float = Field(
        ...,
        description="Weighted average intrinsic value from all methods",
    )
    composite_methodology: str = Field(
        default="60% DCF + 40% Graham Number",
        description="Weighting methodology for composite value",
    )

    # Final assessment
    upside_downside_pct: float = Field(
        ...,
        description="Percentage upside (+) or downside (-) to composite value",
    )
    margin_of_safety: float = Field(
        ...,
        description="Margin of safety (upside / (1 + upside))",
    )
    verdict: ValuationVerdict = Field(
        ...,
        description="Investment verdict based on upside potential",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in valuation (based on data quality)",
    )

    # Assumptions and caveats
    key_assumptions: Dict[str, str] = Field(
        ...,
        description="Key assumptions used in valuation",
    )
    risk_factors: List[str] = Field(
        ...,
        description="Risk factors and data quality warnings",
    )
    data_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quality score of underlying data (from AI extraction)",
    )
