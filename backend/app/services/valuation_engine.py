"""
Valuation engine for DCF and Graham calculations.

This module implements the ValuationEngine class that performs all
financial valuation calculations using pure Python/NumPy. This is
a critical architectural component - NO AI calls are made here.

Architecture Notes:
- All calculations are deterministic and reproducible
- Uses StandardizedValuationInput from AI extraction as input
- Outputs ValuationResult with complete valuation analysis
- Caches results with 24-hour TTL (VALUATION_CACHE_TTL)

Valuation Methodologies:
1. DCF (Discounted Cash Flow) - FCFF approach with 3 scenarios
2. Graham Number - sqrt(22.5 * EPS * BVPS)
3. Graham Defensive Screen - 7 criteria for defensive investors
4. Composite - 60% DCF + 40% Graham Number weighted average
"""

import hashlib
import logging
import math
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from diskcache import Cache

from app.config import get_settings
from app.models.valuation_input import StandardizedValuationInput
from app.models.flexible_input import FlexibleValuationInput
from app.models.valuation_output import (
    DCFScenario,
    DCFValuation,
    GrahamDefensiveCriteria,
    GrahamNumber,
    ValuationResult,
    ValuationVerdict,
)
from app.services.ai_extractor import AIExtractor, get_ai_extractor

# Type alias for either input type
ValuationInput = FlexibleValuationInput | StandardizedValuationInput

logger = logging.getLogger(__name__)


class FlexibleInputAdapter:
    """
    Adapter to provide unified interface for FlexibleValuationInput.

    Maps flexible input fields to the interface expected by valuation calculations.
    Provides sensible defaults when data is missing.
    """

    def __init__(self, data: FlexibleValuationInput):
        self.data = data

    # === Metadata ===
    @property
    def ticker(self) -> str:
        return self.data.ticker

    @property
    def company_name(self) -> str:
        return self.data.company_name

    @property
    def extraction_timestamp(self):
        return self.data.extraction_timestamp

    @property
    def data_confidence_score(self) -> float:
        return self.data.data_confidence_score

    @property
    def sector(self) -> str:
        return self.data.metadata.sector or "Unknown"

    @property
    def industry(self) -> str:
        return self.data.metadata.industry or "Unknown"

    # === Market Position ===
    @property
    def current_price(self) -> float:
        price = self.data.market_position.current_price
        # Return actual price or 0.0 for missing data - callers must handle 0 case
        return price if price and price > 0 else 0.0

    @property
    def shares_outstanding(self) -> float:
        # Try direct value first
        if self.data.market_position.shares_outstanding:
            return self.data.market_position.shares_outstanding
        # Calculate from market_cap / price
        if self.data.market_position.market_cap and self.current_price > 0:
            return self.data.market_position.market_cap / self.current_price
        # Last resort - this should rarely happen
        return 1_000_000  # 1 million shares as minimum fallback

    @property
    def market_cap(self) -> float:
        if self.data.market_position.market_cap:
            return self.data.market_position.market_cap
        return self.current_price * self.shares_outstanding

    @property
    def enterprise_value(self) -> float:
        if self.data.market_position.enterprise_value:
            return self.data.market_position.enterprise_value
        return self.market_cap + self.total_debt - self.total_cash

    # === Income Statement ===
    @property
    def ttm_revenue(self) -> float:
        return self.data.ttm_income_statement.revenue or 0.0

    @property
    def ttm_cost_of_revenue(self) -> float:
        """Get cost of revenue, calculating from margins if needed."""
        if self.data.ttm_income_statement.cost_of_revenue:
            return self.data.ttm_income_statement.cost_of_revenue
        # Calculate from gross_profit if available
        if self.ttm_gross_profit > 0 and self.ttm_revenue > 0:
            return self.ttm_revenue - self.ttm_gross_profit
        # Calculate from gross_margin if available
        gross_margin = self.data.profitability_ratios.gross_margin
        if gross_margin is not None and self.ttm_revenue > 0:
            return self.ttm_revenue * (1 - gross_margin)
        return 0.0

    @property
    def ttm_gross_profit(self) -> float:
        """Get gross profit, calculating from margins if needed."""
        if self.data.ttm_income_statement.gross_profit:
            return self.data.ttm_income_statement.gross_profit
        # Calculate from gross_margin if available
        gross_margin = self.data.profitability_ratios.gross_margin
        if gross_margin is not None and self.ttm_revenue > 0:
            return self.ttm_revenue * gross_margin
        # Calculate from revenue and cost_of_revenue
        if self.data.ttm_income_statement.cost_of_revenue and self.ttm_revenue > 0:
            return self.ttm_revenue - self.data.ttm_income_statement.cost_of_revenue
        return 0.0

    @property
    def ttm_operating_expenses(self) -> float:
        """Get operating expenses, calculating from other fields if needed."""
        if self.data.ttm_income_statement.operating_expenses:
            return self.data.ttm_income_statement.operating_expenses
        # Calculate: Operating Expenses = Gross Profit - Operating Income
        if self.ttm_gross_profit > 0 and self.ttm_operating_income > 0:
            return self.ttm_gross_profit - self.ttm_operating_income
        return 0.0

    @property
    def ttm_operating_income(self) -> float:
        return self.data.ttm_income_statement.operating_income or 0.0

    @property
    def ttm_net_income(self) -> float:
        return self.data.ttm_income_statement.net_income or 0.0

    @property
    def ttm_ebitda(self) -> float:
        return self.data.ttm_income_statement.ebitda or 0.0

    @property
    def ttm_eps(self) -> float:
        return self.data.ttm_income_statement.eps or 0.0

    @property
    def ttm_interest_expense(self) -> Optional[float]:
        return self.data.ttm_income_statement.interest_expense

    # === Cash Flow ===
    @property
    def ttm_operating_cash_flow(self) -> float:
        return self.data.ttm_cash_flow.operating_cash_flow or 0.0

    @property
    def ttm_free_cash_flow(self) -> float:
        if self.data.ttm_cash_flow.free_cash_flow:
            return self.data.ttm_cash_flow.free_cash_flow
        # Calculate if possible
        ocf = self.data.ttm_cash_flow.operating_cash_flow or 0
        capex = abs(self.data.ttm_cash_flow.capital_expenditures or 0)
        return ocf - capex if ocf else 0.0

    # === Balance Sheet ===
    @property
    def total_cash(self) -> float:
        return self.data.balance_sheet.total_cash or 0.0

    @property
    def total_debt(self) -> float:
        return self.data.balance_sheet.total_debt or 0.0

    @property
    def total_assets(self) -> float:
        return self.data.balance_sheet.total_assets or 0.0

    @property
    def total_liabilities(self) -> float:
        return self.data.balance_sheet.total_liabilities or 0.0

    @property
    def shareholders_equity(self) -> float:
        if self.data.balance_sheet.shareholders_equity:
            return self.data.balance_sheet.shareholders_equity
        return self.total_assets - self.total_liabilities

    @property
    def total_current_assets(self) -> float:
        return self.data.balance_sheet.total_current_assets or 0.0

    @property
    def total_current_liabilities(self) -> float:
        return self.data.balance_sheet.total_current_liabilities or 0.0

    # === Calculated Metrics ===
    @property
    def net_debt(self) -> float:
        if self.data.calculated_metrics.net_debt is not None:
            return self.data.calculated_metrics.net_debt
        return self.total_debt - self.total_cash

    @property
    def working_capital(self) -> float:
        if self.data.calculated_metrics.working_capital is not None:
            return self.data.calculated_metrics.working_capital
        return self.total_current_assets - self.total_current_liabilities

    @property
    def invested_capital(self) -> float:
        if self.data.calculated_metrics.invested_capital is not None:
            return self.data.calculated_metrics.invested_capital
        return self.shareholders_equity + self.total_debt - self.total_cash

    # === Profitability Ratios ===
    @property
    def gross_margin(self) -> float:
        if self.data.profitability_ratios.gross_margin is not None:
            return self.data.profitability_ratios.gross_margin
        if self.ttm_revenue > 0 and self.ttm_gross_profit > 0:
            return self.ttm_gross_profit / self.ttm_revenue
        return 0.0

    @property
    def operating_margin(self) -> float:
        if self.data.profitability_ratios.operating_margin is not None:
            return self.data.profitability_ratios.operating_margin
        if self.ttm_revenue > 0:
            return self.ttm_operating_income / self.ttm_revenue
        return 0.0

    @property
    def net_margin(self) -> float:
        return self.data.profitability_ratios.net_margin or 0.0

    @property
    def roe(self) -> float:
        return self.data.profitability_ratios.roe or 0.0

    @property
    def roa(self) -> float:
        return self.data.profitability_ratios.roa or 0.0

    @property
    def roic(self) -> float:
        return self.data.profitability_ratios.roic or 0.10  # Default 10%

    # === Leverage Ratios ===
    @property
    def debt_to_equity(self) -> float:
        if self.data.leverage_ratios.debt_to_equity is not None:
            return self.data.leverage_ratios.debt_to_equity
        if self.shareholders_equity > 0:
            return self.total_debt / self.shareholders_equity
        return 0.0

    @property
    def interest_coverage(self) -> Optional[float]:
        return self.data.leverage_ratios.interest_coverage

    # === Liquidity Ratios ===
    @property
    def current_ratio(self) -> float:
        if self.data.liquidity_ratios.current_ratio is not None:
            return self.data.liquidity_ratios.current_ratio
        if self.total_current_liabilities > 0:
            return self.total_current_assets / self.total_current_liabilities
        return 0.0

    # === Valuation Multiples ===
    @property
    def pe_ratio(self) -> Optional[float]:
        return self.data.valuation_multiples.pe_ratio

    @property
    def forward_pe(self) -> Optional[float]:
        return self.data.valuation_multiples.forward_pe

    @property
    def ev_to_ebitda(self) -> Optional[float]:
        return self.data.valuation_multiples.ev_to_ebitda

    @property
    def price_to_book(self) -> Optional[float]:
        return self.data.valuation_multiples.price_to_book

    @property
    def fcf_yield(self) -> Optional[float]:
        return self.data.valuation_multiples.fcf_yield

    @property
    def dividend_yield(self) -> Optional[float]:
        return self.data.dividends.dividend_yield

    # === Growth Rates ===
    @property
    def revenue_growth_5y_cagr(self) -> Optional[float]:
        # Try to get from growth_rates, or calculate from historical
        if self.data.growth_rates.revenue_growth_5y_cagr is not None:
            return self.data.growth_rates.revenue_growth_5y_cagr
        # Try to calculate from historical data
        if len(self.data.historical_financials) >= 5:
            hist = self.data.historical_financials
            old_rev = hist[-5].revenue if hist[-5].revenue else None
            new_rev = hist[0].revenue if hist[0].revenue else None
            if old_rev and new_rev and old_rev > 0:
                return (new_rev / old_rev) ** (1/5) - 1
        # Fall back to 1Y growth or default
        return self.data.growth_rates.revenue_growth_1y or 0.05

    @property
    def revenue_growth_10y_cagr(self) -> Optional[float]:
        return self.data.growth_rates.revenue_growth_10y_cagr

    @property
    def earnings_growth_5y_cagr(self) -> Optional[float]:
        return self.data.growth_rates.earnings_growth_5y_cagr

    @property
    def earnings_growth_10y_cagr(self) -> Optional[float]:
        return None  # Calculate from historical if needed

    # === Risk Parameters ===
    @property
    def beta(self) -> Optional[float]:
        return self.data.risk_parameters.beta

    @property
    def risk_free_rate(self) -> float:
        return self.data.risk_parameters.risk_free_rate

    @property
    def equity_risk_premium(self) -> float:
        return 0.05  # Default 5%

    # === Historical Data ===
    @property
    def historical_financials(self):
        return self.data.historical_financials

    # === Data Quality ===
    @property
    def missing_fields(self) -> List[str]:
        """Get list of truly missing fields (excluding those we can calculate)."""
        reported_missing = self.data.data_quality.fields_missing

        # Fields we can calculate from other data
        calculable_fields = set()

        # Check if we can calculate income statement fields
        if self.ttm_gross_profit > 0:
            calculable_fields.add("gross_profit")
        if self.ttm_cost_of_revenue > 0:
            calculable_fields.add("cost_of_revenue")
        if self.ttm_operating_expenses > 0:
            calculable_fields.add("operating_expenses")
        if self.ttm_ebitda > 0 or (self.ttm_operating_income > 0):
            calculable_fields.add("ebitda")

        # Filter out calculable fields from missing list
        truly_missing = [
            f for f in reported_missing
            if f.lower().replace("_", "") not in {cf.lower().replace("_", "") for cf in calculable_fields}
        ]

        return truly_missing

    @property
    def estimated_fields(self) -> List[str]:
        """Get list of estimated fields, including calculated income statement fields."""
        estimated = list(self.data.data_quality.fields_estimated)

        # Add fields we calculated from margins
        if not self.data.ttm_income_statement.gross_profit and self.ttm_gross_profit > 0:
            estimated.append("gross_profit (calculated from gross_margin)")
        if not self.data.ttm_income_statement.cost_of_revenue and self.ttm_cost_of_revenue > 0:
            estimated.append("cost_of_revenue (calculated)")
        if not self.data.ttm_income_statement.operating_expenses and self.ttm_operating_expenses > 0:
            estimated.append("operating_expenses (calculated)")

        return estimated

    @property
    def data_anomalies(self) -> List[str]:
        return self.data.data_quality.data_anomalies


class ValuationError(Exception):
    """Base exception for valuation calculation errors."""

    pass


class InsufficientDataError(ValuationError):
    """Exception raised when input data is insufficient for valuation."""

    pass


class ValuationCache:
    """
    Persistent cache for valuation results.

    Uses diskcache for local file-based caching with 24-hour TTL.
    Cache keys incorporate ticker and extraction timestamp to ensure
    cache invalidation when source data changes.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize the valuation cache.

        Args:
            cache_dir: Optional custom cache directory. If not provided,
                      uses settings.cache_dir_resolved / "valuations"
        """
        settings = get_settings()
        self.ttl = settings.VALUATION_CACHE_TTL

        if cache_dir is None:
            cache_dir = settings.cache_dir_resolved / "valuations"

        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = Cache(str(cache_dir))

        logger.info(
            "ValuationCache initialized at %s with TTL=%d seconds",
            cache_dir,
            self.ttl,
        )

    def _get_cache_key(self, ticker: str, extraction_timestamp: str) -> str:
        """Generate cache key from ticker and extraction timestamp."""
        ticker = ticker.upper().strip()
        hash_str = hashlib.md5(extraction_timestamp.encode()).hexdigest()[:8]
        return f"valuation_{ticker}_{hash_str}"

    def get(
        self,
        ticker: str,
        extraction_timestamp: str,
    ) -> Optional[ValuationResult]:
        """
        Retrieve cached valuation for a ticker.

        Args:
            ticker: Stock ticker symbol
            extraction_timestamp: ISO timestamp from extraction

        Returns:
            ValuationResult if found and valid, None otherwise.
        """
        cache_key = self._get_cache_key(ticker, extraction_timestamp)

        try:
            cached_data = self.cache.get(cache_key)

            if cached_data is None:
                logger.debug("Valuation cache miss for %s", ticker)
                return None

            if isinstance(cached_data, dict):
                result = ValuationResult.model_validate(cached_data)
                logger.debug(
                    "Valuation cache hit for %s (timestamp: %s)",
                    ticker,
                    result.calculation_timestamp,
                )
                return result

            return None

        except Exception as e:
            logger.warning("Failed to retrieve cached valuation for %s: %s", ticker, e)
            return None

    def set(
        self,
        ticker: str,
        data: ValuationResult,
        extraction_timestamp: str,
    ) -> None:
        """
        Store valuation result in cache.

        Args:
            ticker: Stock ticker symbol
            data: ValuationResult to cache
            extraction_timestamp: ISO timestamp from extraction
        """
        cache_key = self._get_cache_key(ticker, extraction_timestamp)

        try:
            cache_data = data.model_dump(mode="json")
            self.cache.set(cache_key, cache_data, expire=self.ttl)
            logger.info(
                "Cached valuation for %s (TTL: %d seconds)",
                ticker,
                self.ttl,
            )
        except Exception as e:
            logger.error("Failed to cache valuation for %s: %s", ticker, e)

    def invalidate(self, ticker: str) -> int:
        """Invalidate all cached valuations for a ticker."""
        ticker = ticker.upper().strip()
        deleted_count = 0

        try:
            for key in list(self.cache):
                if isinstance(key, str) and key.startswith(f"valuation_{ticker}_"):
                    if self.cache.delete(key):
                        deleted_count += 1

            logger.info("Invalidated %d valuation cache entries for %s", deleted_count, ticker)
            return deleted_count

        except Exception as e:
            logger.error("Failed to invalidate valuations for %s: %s", ticker, e)
            return deleted_count


class ValuationEngine:
    """
    Pure Python valuation calculations engine.

    This class performs all financial valuation calculations using
    deterministic mathematical formulas. No AI/LLM calls are made here.

    Attributes:
        cache: ValuationCache for result caching
        tax_rate: US federal corporate tax rate (21%)

    Example:
        engine = ValuationEngine()
        result = await engine.calculate_valuation("AAPL")
    """

    # US federal corporate tax rate
    TAX_RATE = 0.21

    # Credit spread table based on interest coverage ratio
    # Maps interest coverage to credit spread (as decimal)
    CREDIT_SPREAD_TABLE = [
        (0, 0.05),      # IC <= 0: 5.0% spread (distressed)
        (1.5, 0.04),    # IC < 1.5: 4.0% spread (CCC)
        (3.0, 0.03),    # IC < 3.0: 3.0% spread (B)
        (5.0, 0.02),    # IC < 5.0: 2.0% spread (BB)
        (8.0, 0.015),   # IC < 8.0: 1.5% spread (BBB)
        (12.0, 0.01),   # IC < 12.0: 1.0% spread (A)
        (float("inf"), 0.007),  # IC >= 12.0: 0.7% spread (AA/AAA)
    ]

    # Graham Defensive Screen Thresholds (from "The Intelligent Investor")
    GRAHAM_MIN_REVENUE = 700_000_000  # $700M minimum revenue for adequate size
    GRAHAM_MIN_CURRENT_RATIO = 2.0    # Minimum current ratio for financial strength
    GRAHAM_MIN_POSITIVE_YEARS = 10    # Years of positive earnings required
    GRAHAM_MIN_DIVIDEND_YEARS = 20    # Years of dividends required
    GRAHAM_MIN_EPS_GROWTH_PCT = 33.0  # Minimum EPS growth over 10 years (33%)
    GRAHAM_MAX_PE_RATIO = 15.0        # Maximum P/E ratio for moderate valuation
    GRAHAM_MAX_PB_RATIO = 1.5         # Maximum P/B ratio
    GRAHAM_MAX_PE_PB_PRODUCT = 22.5   # Maximum P/E * P/B product
    GRAHAM_MIN_CRITERIA_PASS = 5      # Minimum criteria to pass defensive screen
    GRAHAM_TOTAL_CRITERIA = 7         # Total number of criteria in defensive screen

    # Composite Valuation Weights
    COMPOSITE_DCF_WEIGHT = 0.60       # 60% weight for DCF in composite
    COMPOSITE_GRAHAM_WEIGHT = 0.40    # 40% weight for Graham Number in composite

    # Valuation Verdict Thresholds (as decimals)
    VERDICT_SIGNIFICANTLY_UNDERVALUED = 0.40   # > 40% upside
    VERDICT_UNDERVALUED = 0.15                 # > 15% upside
    VERDICT_FAIRLY_VALUED_UPPER = 0.15         # Upper bound for fairly valued
    VERDICT_FAIRLY_VALUED_LOWER = -0.15        # Lower bound for fairly valued
    VERDICT_OVERVALUED = -0.40                 # >= -40% upside (i.e., <= 40% downside)

    def __init__(
        self,
        cache: Optional[ValuationCache] = None,
        ai_extractor: Optional[AIExtractor] = None,
    ) -> None:
        """
        Initialize the valuation engine.

        Args:
            cache: Optional ValuationCache instance. If not provided,
                  creates a new default cache.
            ai_extractor: Optional AIExtractor for getting input data.
                         If not provided, uses singleton instance.
        """
        self.cache = cache or ValuationCache()
        self._ai_extractor = ai_extractor

        logger.info("ValuationEngine initialized")

    @property
    def ai_extractor(self) -> AIExtractor:
        """Lazy-load AI extractor to avoid circular imports."""
        if self._ai_extractor is None:
            self._ai_extractor = get_ai_extractor()
        return self._ai_extractor

    def _get_credit_spread(self, interest_coverage: Optional[float]) -> float:
        """
        Determine credit spread based on interest coverage ratio.

        Uses a tiered system based on typical credit rating spreads:
        - IC <= 0: 5.0% (distressed)
        - IC < 1.5: 4.0% (CCC rating)
        - IC < 3.0: 3.0% (B rating)
        - IC < 5.0: 2.0% (BB rating)
        - IC < 8.0: 1.5% (BBB rating)
        - IC < 12.0: 1.0% (A rating)
        - IC >= 12.0: 0.7% (AA/AAA rating)

        Args:
            interest_coverage: EBIT / Interest Expense ratio

        Returns:
            Credit spread as decimal (e.g., 0.03 for 3%)
        """
        if interest_coverage is None or interest_coverage <= 0:
            return 0.05  # Distressed

        for threshold, spread in self.CREDIT_SPREAD_TABLE:
            if interest_coverage < threshold:
                return spread

        return 0.007  # Default to best rating

    def calculate_wacc(
        self,
        input_data: StandardizedValuationInput,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Weighted Average Cost of Capital (WACC).

        WACC = (E/V * Cost of Equity) + (D/V * Cost of Debt * (1 - Tax))

        Where:
        - Cost of Equity = Rf + Beta * ERP (CAPM)
        - Cost of Debt = Rf + Credit Spread
        - E = Market Cap (equity value)
        - D = Total Debt
        - V = E + D (total capital)

        Args:
            input_data: StandardizedValuationInput with required metrics

        Returns:
            Tuple of (WACC as decimal, dict with all components)

        Example:
            wacc, components = engine.calculate_wacc(input_data)
            # wacc = 0.085 (8.5%)
            # components = {"cost_of_equity": 0.095, "wacc": 0.085, ...}
        """
        # Cost of Equity using CAPM
        beta = input_data.beta if input_data.beta is not None else 1.0
        cost_of_equity = (
            input_data.risk_free_rate + beta * input_data.equity_risk_premium
        )

        # Cost of Debt
        credit_spread = self._get_credit_spread(input_data.interest_coverage)
        cost_of_debt_pretax = input_data.risk_free_rate + credit_spread
        cost_of_debt_aftertax = cost_of_debt_pretax * (1 - self.TAX_RATE)

        # Capital structure weights
        # Guard against negative or zero values
        market_cap = max(input_data.market_cap, 0.0)
        total_debt = max(input_data.total_debt, 0.0)
        total_capital = market_cap + total_debt

        if total_capital <= 0:
            # Fallback: 100% equity
            equity_weight = 1.0
            debt_weight = 0.0
        else:
            equity_weight = market_cap / total_capital
            debt_weight = total_debt / total_capital

        # WACC calculation
        wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt_aftertax)

        components = {
            "risk_free_rate": input_data.risk_free_rate,
            "beta": beta,
            "equity_risk_premium": input_data.equity_risk_premium,
            "cost_of_equity": cost_of_equity,
            "credit_spread": credit_spread,
            "cost_of_debt_pretax": cost_of_debt_pretax,
            "cost_of_debt_aftertax": cost_of_debt_aftertax,
            "equity_weight": equity_weight,
            "debt_weight": debt_weight,
            "wacc": wacc,
        }

        logger.debug(
            "WACC calculated for %s: %.2f%% (CoE: %.2f%%, CoD: %.2f%%)",
            input_data.ticker,
            wacc * 100,
            cost_of_equity * 100,
            cost_of_debt_aftertax * 100,
        )

        return wacc, components

    def calculate_dcf_scenario(
        self,
        input_data: StandardizedValuationInput,
        scenario_name: str,
        growth_rate: float,
        terminal_growth: float,
        operating_margin: float,
        wacc: float,
        projection_years: int = 5,
    ) -> DCFScenario:
        """
        Calculate a single DCF scenario.

        Projects revenue, EBIT, NOPAT, and FCF for the explicit period,
        then calculates terminal value using Gordon Growth Model.

        Growth Decay: Year growth decays from initial rate toward terminal rate
        Year Growth = Initial Growth - (Initial - Terminal) * (year / 10)

        FCF Calculation:
        - Revenue(t) = Revenue(t-1) * (1 + Year Growth)
        - EBIT = Revenue * Operating Margin
        - NOPAT = EBIT * (1 - Tax Rate)
        - Reinvestment Rate = min(Year Growth / ROIC, 0.8)
        - FCF = NOPAT * (1 - Reinvestment Rate)

        Terminal Value:
        - Terminal FCF = FCF(last) * (1 + Terminal Growth)
        - Terminal Value = Terminal FCF / (WACC - Terminal Growth)
        - If WACC <= Terminal Growth, adjust Terminal Growth to WACC - 0.01

        Args:
            input_data: StandardizedValuationInput with base financials
            scenario_name: Name of scenario ("conservative", "base_case", "optimistic")
            growth_rate: Initial revenue growth rate
            terminal_growth: Terminal/perpetual growth rate
            operating_margin: Operating margin assumption
            wacc: Weighted average cost of capital
            projection_years: Number of years to project (default: 5)

        Returns:
            DCFScenario with complete projections and valuation
        """
        base_revenue = input_data.ttm_revenue
        # Handle None values for roic
        roic = input_data.roic if (input_data.roic is not None and input_data.roic > 0) else 0.10

        # Project financials
        projected_revenue: List[float] = []
        projected_ebit: List[float] = []
        projected_nopat: List[float] = []
        projected_fcf: List[float] = []

        current_revenue = base_revenue

        for year in range(1, projection_years + 1):
            # Growth decay: gradually move from initial growth to terminal growth
            # Over 10 years, growth fully converges to terminal rate
            year_growth = growth_rate - (growth_rate - terminal_growth) * (year / 10.0)

            current_revenue = current_revenue * (1 + year_growth)
            ebit = current_revenue * operating_margin
            nopat = ebit * (1 - self.TAX_RATE)

            # Reinvestment rate based on sustainable growth
            # Growth requires reinvestment; higher growth = higher reinvestment
            reinvestment_rate = min(year_growth / roic, 0.80) if roic > 0 else 0.50
            reinvestment_rate = max(reinvestment_rate, 0.0)  # No negative reinvestment

            fcf = nopat * (1 - reinvestment_rate)

            projected_revenue.append(current_revenue)
            projected_ebit.append(ebit)
            projected_nopat.append(nopat)
            projected_fcf.append(fcf)

        # Terminal value calculation using Gordon Growth Model
        # Ensure WACC > terminal growth to avoid infinite/negative values
        effective_terminal_growth = terminal_growth
        if wacc <= terminal_growth:
            effective_terminal_growth = wacc - 0.01
            logger.warning(
                "Terminal growth (%.2f%%) >= WACC (%.2f%%), adjusting to %.2f%%",
                terminal_growth * 100,
                wacc * 100,
                effective_terminal_growth * 100,
            )

        terminal_fcf = projected_fcf[-1] * (1 + effective_terminal_growth)
        terminal_value = terminal_fcf / (wacc - effective_terminal_growth)

        # Present value calculations
        pv_explicit = sum(
            fcf / ((1 + wacc) ** (i + 1))
            for i, fcf in enumerate(projected_fcf)
        )
        pv_terminal = terminal_value / ((1 + wacc) ** projection_years)

        # Enterprise value to equity value
        enterprise_value = pv_explicit + pv_terminal
        equity_value = enterprise_value - input_data.net_debt

        # Guard against division by zero for shares_outstanding
        if input_data.shares_outstanding <= 0:
            intrinsic_per_share = 0.0
        else:
            intrinsic_per_share = equity_value / input_data.shares_outstanding

        # Ensure non-negative intrinsic value
        intrinsic_per_share = max(intrinsic_per_share, 0.0)

        # Calculate upside/downside
        upside_pct = (
            (intrinsic_per_share - input_data.current_price) / input_data.current_price
            if input_data.current_price > 0
            else 0.0
        )

        return DCFScenario(
            scenario_name=scenario_name,
            revenue_growth_rate=growth_rate,
            operating_margin_assumption=operating_margin,
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
            current_price=input_data.current_price,
            upside_downside_pct=upside_pct,
        )

    def calculate_dcf(
        self,
        input_data: StandardizedValuationInput,
    ) -> DCFValuation:
        """
        Calculate complete DCF valuation with three scenarios.

        Scenarios:
        - Conservative: growth * 0.5 (min 2%), terminal 2%, margin * 0.85
        - Base Case: 5Y CAGR or 5%, terminal 2.5%, current margin
        - Optimistic: growth * 1.5 (max 25%), terminal 3%, margin * 1.15 (max 35%)

        Weighted Result: Conservative(25%) + Base(50%) + Optimistic(25%)

        Also calculates sensitivity to WACC and terminal growth (+/- 1%).

        Args:
            input_data: StandardizedValuationInput with required metrics

        Returns:
            DCFValuation with all scenarios and weighted result
        """
        # Calculate WACC first
        wacc, wacc_components = self.calculate_wacc(input_data)

        # Base growth from historical data
        base_growth = input_data.revenue_growth_5y_cagr or 0.05
        if base_growth < 0:
            base_growth = 0.03  # Minimum assumption for negative growth

        current_margin = input_data.operating_margin

        # Scenario parameters
        scenario_params = {
            "conservative": {
                "growth": max(0.02, base_growth * 0.5),
                "terminal": 0.02,
                "margin": current_margin * 0.85,
            },
            "base_case": {
                "growth": base_growth,
                "terminal": 0.025,
                "margin": current_margin,
            },
            "optimistic": {
                "growth": min(0.25, base_growth * 1.5),
                "terminal": 0.03,
                "margin": min(current_margin * 1.15, 0.35),
            },
        }

        # Calculate each scenario
        scenarios = {}
        for name, params in scenario_params.items():
            scenarios[name] = self.calculate_dcf_scenario(
                input_data=input_data,
                scenario_name=name,
                growth_rate=params["growth"],
                terminal_growth=params["terminal"],
                operating_margin=params["margin"],
                wacc=wacc,
            )

        # Probability-weighted intrinsic value
        weights = {
            "conservative": 0.25,
            "base_case": 0.50,
            "optimistic": 0.25,
        }
        weighted_iv = sum(
            scenarios[name].intrinsic_value_per_share * weight
            for name, weight in weights.items()
        )

        # Sensitivity analysis: WACC +/- 1%
        sensitivity_wacc = {
            "wacc_minus_1pct": self.calculate_dcf_scenario(
                input_data=input_data,
                scenario_name="sensitivity",
                growth_rate=scenario_params["base_case"]["growth"],
                terminal_growth=0.025,
                operating_margin=current_margin,
                wacc=wacc - 0.01,
            ).intrinsic_value_per_share,
            "wacc_plus_1pct": self.calculate_dcf_scenario(
                input_data=input_data,
                scenario_name="sensitivity",
                growth_rate=scenario_params["base_case"]["growth"],
                terminal_growth=0.025,
                operating_margin=current_margin,
                wacc=wacc + 0.01,
            ).intrinsic_value_per_share,
        }

        # Sensitivity analysis: Terminal growth +/- 1%
        sensitivity_growth = {
            "growth_minus_1pct": self.calculate_dcf_scenario(
                input_data=input_data,
                scenario_name="sensitivity",
                growth_rate=scenario_params["base_case"]["growth"],
                terminal_growth=0.015,  # 2.5% - 1%
                operating_margin=current_margin,
                wacc=wacc,
            ).intrinsic_value_per_share,
            "growth_plus_1pct": self.calculate_dcf_scenario(
                input_data=input_data,
                scenario_name="sensitivity",
                growth_rate=scenario_params["base_case"]["growth"],
                terminal_growth=0.035,  # 2.5% + 1%
                operating_margin=current_margin,
                wacc=wacc,
            ).intrinsic_value_per_share,
        }

        return DCFValuation(
            calculation_timestamp=datetime.now(timezone.utc),
            methodology="Discounted Cash Flow (FCFF)",
            risk_free_rate=wacc_components["risk_free_rate"],
            beta=wacc_components["beta"],
            equity_risk_premium=wacc_components["equity_risk_premium"],
            cost_of_equity=wacc_components["cost_of_equity"],
            cost_of_debt_pretax=wacc_components["cost_of_debt_pretax"],
            tax_rate=self.TAX_RATE,
            cost_of_debt_aftertax=wacc_components["cost_of_debt_aftertax"],
            debt_weight=wacc_components["debt_weight"],
            equity_weight=wacc_components["equity_weight"],
            wacc=wacc,
            conservative=scenarios["conservative"],
            base_case=scenarios["base_case"],
            optimistic=scenarios["optimistic"],
            scenario_weights=weights,
            weighted_intrinsic_value=weighted_iv,
            sensitivity_to_wacc=sensitivity_wacc,
            sensitivity_to_growth=sensitivity_growth,
        )

    def calculate_graham_number(
        self,
        input_data: StandardizedValuationInput,
    ) -> GrahamNumber:
        """
        Calculate Benjamin Graham's intrinsic value formula.

        Graham Number = sqrt(22.5 * EPS * BVPS)

        Where:
        - 22.5 = 15 (max P/E) * 1.5 (max P/B)
        - EPS = Trailing Twelve Months Earnings Per Share
        - BVPS = Book Value Per Share (Shareholders Equity / Shares)

        Returns 0 if EPS or BVPS is non-positive.

        Args:
            input_data: StandardizedValuationInput with EPS and equity data

        Returns:
            GrahamNumber with calculated value and upside percentage
        """
        eps = input_data.ttm_eps
        # Guard against division by zero for shares_outstanding
        if input_data.shares_outstanding > 0:
            bvps = input_data.shareholders_equity / input_data.shares_outstanding
        else:
            bvps = 0.0
            logger.warning(
                "Invalid shares_outstanding for %s: %s",
                input_data.ticker,
                input_data.shares_outstanding,
            )

        # Graham Number formula - only valid for positive EPS and BVPS
        if eps > 0 and bvps > 0:
            graham_number = math.sqrt(22.5 * eps * bvps)
        else:
            graham_number = 0.0
            logger.debug(
                "Graham Number is 0 for %s (EPS: %.2f, BVPS: %.2f)",
                input_data.ticker,
                eps,
                bvps,
            )

        # Calculate upside percentage
        if graham_number > 0 and input_data.current_price > 0:
            upside_pct = (graham_number - input_data.current_price) / input_data.current_price
        else:
            upside_pct = -1.0  # Indicates not applicable

        return GrahamNumber(
            methodology="Graham Number = sqrt(22.5 * EPS * BVPS)",
            eps_ttm=eps,
            book_value_per_share=bvps,
            graham_multiplier=22.5,
            graham_number=graham_number,
            current_price=input_data.current_price,
            upside_pct=upside_pct,
        )

    def calculate_graham_screen(
        self,
        input_data: StandardizedValuationInput,
    ) -> GrahamDefensiveCriteria:
        """
        Evaluate Graham's 7 defensive investor criteria.

        Criteria:
        1. Adequate Size: Revenue >= $700M
        2. Strong Financial Condition: Current Ratio >= 2.0
        3. Earnings Stability: 10 years positive earnings
        4. Dividend Record: Has dividend (relaxed from 20 years)
        5. Earnings Growth: EPS growth > 33% over 10 years
        6. Moderate P/E: P/E <= 15
        7. Moderate P/B: P/B <= 1.5 OR (P/E * P/B) < 22.5

        A stock passes the screen if it meets >= 5 criteria.

        Args:
            input_data: StandardizedValuationInput with all required metrics

        Returns:
            GrahamDefensiveCriteria with detailed results
        """
        # Criterion 1: Adequate Size ($700M revenue)
        revenue = input_data.ttm_revenue or 0
        adequate_size = revenue >= self.GRAHAM_MIN_REVENUE

        # Criterion 2: Strong Financial Condition (Current Ratio >= 2.0)
        current_ratio = input_data.current_ratio or 0
        strong_financial = current_ratio >= self.GRAHAM_MIN_CURRENT_RATIO

        # Criterion 3: Earnings Stability (10 years positive earnings)
        years_positive = sum(
            1 for h in input_data.historical_financials
            if h.net_income is not None and h.net_income > 0
        )
        earnings_stability = years_positive >= self.GRAHAM_MIN_POSITIVE_YEARS

        # Criterion 4: Dividend Record
        # Relaxed from Graham's 20 years to just having dividends
        has_dividends = (input_data.dividend_yield or 0) > 0
        years_dividends = self.GRAHAM_MIN_DIVIDEND_YEARS if has_dividends else 0
        dividend_record = has_dividends

        # Criterion 5: Earnings Growth (33% over 10 years)
        eps_10y_growth: Optional[float] = None
        if len(input_data.historical_financials) >= 10:
            old_eps = input_data.historical_financials[-1].eps
            new_eps = input_data.historical_financials[0].eps
            if old_eps is not None and new_eps is not None and old_eps > 0:
                eps_10y_growth = (new_eps - old_eps) / abs(old_eps)
        elif input_data.earnings_growth_10y_cagr is not None:
            # Use CAGR to estimate total growth: (1 + CAGR)^10 - 1
            eps_10y_growth = (1 + input_data.earnings_growth_10y_cagr) ** 10 - 1

        earnings_growth = eps_10y_growth is not None and eps_10y_growth >= (self.GRAHAM_MIN_EPS_GROWTH_PCT / 100)

        # Criterion 6: Moderate P/E (P/E <= 15)
        pe = input_data.pe_ratio
        moderate_pe = pe is not None and pe <= self.GRAHAM_MAX_PE_RATIO and pe > 0

        # Criterion 7: Moderate P/B (P/B <= 1.5 OR P/E * P/B < 22.5)
        pb = input_data.price_to_book
        moderate_pb = pb is not None and pb <= self.GRAHAM_MAX_PB_RATIO and pb > 0

        # Graham product test (P/E * P/B < 22.5)
        if pe is not None and pb is not None and pe > 0 and pb > 0:
            graham_product = pe * pb
            graham_product_passes = graham_product < self.GRAHAM_MAX_PE_PB_PRODUCT
        else:
            graham_product = None
            graham_product_passes = False

        # Count passed criteria
        # For criteria 6 and 7, count if either individual or combined passes
        passed_count = sum([
            adequate_size,
            strong_financial,
            earnings_stability,
            dividend_record,
            earnings_growth,
            moderate_pe or graham_product_passes,  # P/E or product test
            moderate_pb or graham_product_passes,  # P/B or product test
        ])

        passes_screen = passed_count >= self.GRAHAM_MIN_CRITERIA_PASS

        return GrahamDefensiveCriteria(
            adequate_size=adequate_size,
            revenue_minimum=float(self.GRAHAM_MIN_REVENUE),
            actual_revenue=input_data.ttm_revenue,
            strong_financial_condition=strong_financial,
            current_ratio_minimum=self.GRAHAM_MIN_CURRENT_RATIO,
            actual_current_ratio=input_data.current_ratio,
            earnings_stability=earnings_stability,
            years_positive_earnings=years_positive,
            required_years=self.GRAHAM_MIN_POSITIVE_YEARS,
            dividend_record=dividend_record,
            years_dividends_paid=years_dividends,
            required_dividend_years=self.GRAHAM_MIN_DIVIDEND_YEARS,
            earnings_growth=earnings_growth,
            eps_10y_growth=eps_10y_growth,
            required_growth=self.GRAHAM_MIN_EPS_GROWTH_PCT / 100,
            moderate_pe=moderate_pe,
            pe_maximum=self.GRAHAM_MAX_PE_RATIO,
            actual_pe=pe,
            moderate_pb=moderate_pb,
            pb_maximum=self.GRAHAM_MAX_PB_RATIO,
            actual_pb=pb,
            graham_product=graham_product,
            graham_product_passes=graham_product_passes,
            criteria_passed=passed_count,
            total_criteria=self.GRAHAM_TOTAL_CRITERIA,
            passes_screen=passes_screen,
        )

    def calculate_composite(
        self,
        dcf_weighted_value: float,
        graham_number: float,
    ) -> Tuple[float, str]:
        """
        Calculate composite intrinsic value from multiple methods.

        Weighting: 60% DCF + 40% Graham Number

        If Graham Number is 0 (not applicable), uses 100% DCF.

        Args:
            dcf_weighted_value: Probability-weighted DCF value
            graham_number: Graham Number value

        Returns:
            Tuple of (composite value, methodology string)
        """
        if graham_number > 0:
            composite = (dcf_weighted_value * self.COMPOSITE_DCF_WEIGHT +
                        graham_number * self.COMPOSITE_GRAHAM_WEIGHT)
            methodology = f"{int(self.COMPOSITE_DCF_WEIGHT * 100)}% DCF + {int(self.COMPOSITE_GRAHAM_WEIGHT * 100)}% Graham Number"
        else:
            composite = dcf_weighted_value
            methodology = "100% DCF (Graham Number not applicable)"

        return composite, methodology

    def determine_verdict(self, upside_pct: float) -> ValuationVerdict:
        """
        Determine valuation verdict based on upside percentage.

        Thresholds:
        - > 40%: SIGNIFICANTLY_UNDERVALUED
        - 15% to 40%: UNDERVALUED
        - -15% to 15%: FAIRLY_VALUED
        - -40% to -15%: OVERVALUED
        - < -40%: SIGNIFICANTLY_OVERVALUED

        Args:
            upside_pct: Percentage upside (as decimal, e.g., 0.25 for 25%)

        Returns:
            ValuationVerdict enum value
        """
        if upside_pct > self.VERDICT_SIGNIFICANTLY_UNDERVALUED:
            return ValuationVerdict.SIGNIFICANTLY_UNDERVALUED
        elif upside_pct > self.VERDICT_UNDERVALUED:
            return ValuationVerdict.UNDERVALUED
        elif upside_pct >= self.VERDICT_FAIRLY_VALUED_LOWER:
            return ValuationVerdict.FAIRLY_VALUED
        elif upside_pct >= self.VERDICT_OVERVALUED:
            return ValuationVerdict.OVERVALUED
        else:
            return ValuationVerdict.SIGNIFICANTLY_OVERVALUED

    def _calculate_confidence_score(
        self,
        input_data: StandardizedValuationInput,
        dcf_valuation: DCFValuation,
    ) -> float:
        """
        Calculate confidence score for the valuation.

        Based on:
        - Data quality score from AI extraction (50%)
        - Historical data completeness (25%)
        - Consistency of scenarios (25%)

        Args:
            input_data: Source data with quality indicators
            dcf_valuation: DCF results for scenario consistency check

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base score from data quality
        base_score = input_data.data_confidence_score

        # Historical data completeness (expect 10 years)
        years_available = len(input_data.historical_financials)
        history_score = min(years_available / 10.0, 1.0)

        # Scenario consistency (check if results are in reasonable range)
        conservative_iv = dcf_valuation.conservative.intrinsic_value_per_share
        optimistic_iv = dcf_valuation.optimistic.intrinsic_value_per_share

        if conservative_iv > 0 and optimistic_iv > 0:
            # Ratio of optimistic to conservative
            scenario_ratio = optimistic_iv / conservative_iv
            # Penalize if scenarios are too far apart (ratio > 5)
            if scenario_ratio <= 3:
                consistency_score = 1.0
            elif scenario_ratio <= 5:
                consistency_score = 0.8
            else:
                consistency_score = 0.5
        else:
            consistency_score = 0.5

        # Weighted average
        confidence = (
            base_score * 0.50 +
            history_score * 0.25 +
            consistency_score * 0.25
        )

        return min(max(confidence, 0.0), 1.0)

    def _generate_key_assumptions(
        self,
        input_data: StandardizedValuationInput,
        dcf_valuation: DCFValuation,
    ) -> Dict[str, str]:
        """Generate dictionary of key assumptions used in valuation."""
        return {
            "risk_free_rate": f"{dcf_valuation.risk_free_rate:.2%}",
            "equity_risk_premium": f"{dcf_valuation.equity_risk_premium:.2%}",
            "beta": f"{dcf_valuation.beta:.2f}",
            "wacc": f"{dcf_valuation.wacc:.2%}",
            "tax_rate": f"{self.TAX_RATE:.0%}",
            "base_case_growth": f"{dcf_valuation.base_case.revenue_growth_rate:.1%}",
            "terminal_growth": f"{dcf_valuation.base_case.terminal_growth_rate:.1%}",
            "operating_margin": f"{dcf_valuation.base_case.operating_margin_assumption:.1%}",
            "dcf_weight": "60%",
            "graham_weight": "40%",
            "projection_years": str(dcf_valuation.base_case.projection_years),
        }

    def _generate_risk_factors(
        self,
        input_data: StandardizedValuationInput,
        dcf_valuation: DCFValuation,
        graham_screen: GrahamDefensiveCriteria,
    ) -> List[str]:
        """Generate list of risk factors and warnings."""
        risks = []

        # Data quality warnings
        if input_data.data_anomalies:
            risks.extend(input_data.data_anomalies)

        # Financial health warnings
        debt_to_equity = input_data.debt_to_equity or 0
        if debt_to_equity > 2.0:
            risks.append(f"High leverage: Debt/Equity ratio of {debt_to_equity:.1f}x")

        current_ratio_val = input_data.current_ratio or 0
        if current_ratio_val > 0 and current_ratio_val < 1.0:
            risks.append(f"Liquidity concern: Current ratio of {current_ratio_val:.2f}")

        if input_data.interest_coverage is not None and input_data.interest_coverage < 3.0:
            risks.append(f"Low interest coverage: {input_data.interest_coverage:.1f}x")

        # Valuation warnings
        if dcf_valuation.base_case.revenue_growth_rate > 0.20:
            risks.append("Valuation assumes aggressive growth (>20% annually)")

        if dcf_valuation.wacc < 0.06:
            risks.append("Low discount rate may overstate intrinsic value")

        # Graham screen warnings
        if not graham_screen.passes_screen:
            risks.append(f"Fails Graham defensive screen ({graham_screen.criteria_passed}/7 criteria)")

        # Missing data warnings
        if input_data.missing_fields:
            risks.append(f"Missing data fields: {', '.join(input_data.missing_fields[:3])}")

        return risks

    async def calculate_valuation(
        self,
        ticker: str,
        force_refresh: bool = False,
        use_flexible: bool = True,
    ) -> ValuationResult:
        """
        Calculate complete valuation for a stock.

        This is the main entry point for valuations. It:
        1. Checks cache for existing valuation (unless force_refresh)
        2. Gets input data from AI extractor (flexible or standard)
        3. Runs all valuation calculations
        4. Computes composite value and verdict
        5. Caches and returns result

        Args:
            ticker: Stock ticker symbol
            force_refresh: If True, bypass cache and recalculate
            use_flexible: If True, use flexible extraction (default)

        Returns:
            ValuationResult with complete valuation analysis

        Raises:
            ValuationError: If calculation fails
            InsufficientDataError: If input data is missing required fields
        """
        ticker = ticker.upper().strip()
        logger.info(
            "Starting valuation for %s (force_refresh=%s, flexible=%s)",
            ticker,
            force_refresh,
            use_flexible,
        )

        # Get input from AI extractor
        if use_flexible:
            flexible_data = await self.ai_extractor.extract_flexible(
                ticker,
                force_refresh=force_refresh,
            )
            # Wrap in adapter for unified interface
            input_data = FlexibleInputAdapter(flexible_data)
        else:
            input_data = await self.ai_extractor.extract_valuation_input(
                ticker,
                force_refresh=force_refresh,
            )

        extraction_timestamp = input_data.extraction_timestamp.isoformat()

        # Check cache (unless force refresh)
        if not force_refresh:
            cached_result = self.cache.get(ticker, extraction_timestamp)
            if cached_result is not None:
                logger.info("Returning cached valuation for %s", ticker)
                return cached_result

        try:
            # Run all calculations
            dcf_valuation = self.calculate_dcf(input_data)
            graham_number = self.calculate_graham_number(input_data)
            graham_screen = self.calculate_graham_screen(input_data)

            # Calculate composite intrinsic value
            composite_value, composite_methodology = self.calculate_composite(
                dcf_valuation.weighted_intrinsic_value,
                graham_number.graham_number,
            )

            # Calculate upside and margin of safety
            if input_data.current_price > 0:
                upside_pct = (composite_value - input_data.current_price) / input_data.current_price
            else:
                upside_pct = 0.0

            # Margin of safety = upside / (1 + upside)
            # Use epsilon to prevent division by near-zero and numeric instability
            if upside_pct > -0.99:
                margin_of_safety = upside_pct / (1 + upside_pct)
            else:
                # Stock is nearly worthless (>99% downside)
                margin_of_safety = -1.0

            # Determine verdict
            verdict = self.determine_verdict(upside_pct)

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(input_data, dcf_valuation)

            # Generate assumptions and risks
            key_assumptions = self._generate_key_assumptions(input_data, dcf_valuation)
            risk_factors = self._generate_risk_factors(input_data, dcf_valuation, graham_screen)

            # Build result
            result = ValuationResult(
                ticker=input_data.ticker,
                company_name=input_data.company_name,
                calculation_timestamp=datetime.now(timezone.utc),
                current_price=input_data.current_price,
                market_cap=input_data.market_cap,
                enterprise_value=input_data.enterprise_value,
                shares_outstanding=input_data.shares_outstanding,
                dcf_valuation=dcf_valuation,
                graham_number=graham_number,
                graham_defensive_screen=graham_screen,
                valuation_methods_used=[
                    "DCF (FCFF)",
                    "Graham Number",
                    "Graham Defensive Screen",
                ],
                composite_intrinsic_value=composite_value,
                composite_methodology=composite_methodology,
                upside_downside_pct=upside_pct,
                margin_of_safety=margin_of_safety,
                verdict=verdict,
                confidence_score=confidence_score,
                key_assumptions=key_assumptions,
                risk_factors=risk_factors,
                data_quality_score=input_data.data_confidence_score,
            )

            # Cache the result
            self.cache.set(ticker, result, extraction_timestamp)

            logger.info(
                "Valuation complete for %s: $%.2f intrinsic value, %.1f%% upside, verdict=%s",
                ticker,
                composite_value,
                upside_pct * 100,
                verdict.value,
            )

            return result

        except Exception as e:
            logger.error("Valuation calculation failed for %s: %s", ticker, e)
            raise ValuationError(f"Failed to calculate valuation for {ticker}: {e}") from e


# Singleton instance for dependency injection
_engine_instance: Optional[ValuationEngine] = None
_engine_lock = threading.Lock()


def get_valuation_engine() -> ValuationEngine:
    """
    Get or create the singleton ValuationEngine instance.

    This function provides a FastAPI-compatible dependency.

    Returns:
        ValuationEngine: The singleton engine instance.

    Example:
        @router.get("/{ticker}/valuation")
        async def get_valuation(
            ticker: str,
            engine: ValuationEngine = Depends(get_valuation_engine)
        ):
            return await engine.calculate_valuation(ticker)
    """
    global _engine_instance
    if _engine_instance is None:
        with _engine_lock:
            # Double-check after acquiring lock
            if _engine_instance is None:
                _engine_instance = ValuationEngine()
    return _engine_instance
