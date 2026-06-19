"""
Factories for building valid StandardizedValuationInput objects in tests.

The model has ~50 required fields; hand-building one per test is noisy, so these
factories provide a realistic, internally-consistent baseline (loosely modeled on
a large-cap tech company) that individual tests override field-by-field.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.models.flexible_input import FlexibleValuationInput
from app.models.valuation_input import HistoricalFinancials, StandardizedValuationInput


def make_historical(fiscal_year: int, **overrides: Any) -> HistoricalFinancials:
    """Build one year of historical financials with sensible defaults."""
    base: dict[str, Any] = {
        "fiscal_year": fiscal_year,
        "revenue": 300_000_000_000.0,
        "gross_profit": 130_000_000_000.0,
        "operating_income": 90_000_000_000.0,
        "net_income": 80_000_000_000.0,
        "free_cash_flow": 75_000_000_000.0,
        "eps": 5.0,
        "depreciation_amortization": 11_000_000_000.0,
        "capital_expenditures": 10_000_000_000.0,
        "total_assets": 350_000_000_000.0,
        "total_liabilities": 280_000_000_000.0,
        "shareholders_equity": 70_000_000_000.0,
        "total_debt": 100_000_000_000.0,
        "cash_and_equivalents": 30_000_000_000.0,
    }
    base.update(overrides)
    return HistoricalFinancials(**base)


def make_historical_series(
    years: int = 10,
    end_year: int = 2024,
    start_eps: float = 3.0,
    end_eps: float = 6.0,
    positive: bool = True,
) -> list[HistoricalFinancials]:
    """
    Build a list of `years` HistoricalFinancials, oldest..newest, with EPS
    interpolated from start_eps (oldest) to end_eps (newest).
    """
    series: list[HistoricalFinancials] = []
    span = max(years - 1, 1)
    for i in range(years):
        year = end_year - (years - 1 - i)
        eps = start_eps + (end_eps - start_eps) * (i / span)
        net_income = 80_000_000_000.0 if positive else -5_000_000_000.0
        series.append(make_historical(year, eps=eps, net_income=net_income))
    return series


def make_input(**overrides: Any) -> StandardizedValuationInput:
    """
    Build a valid StandardizedValuationInput with a realistic, consistent
    baseline. Pass keyword overrides to exercise specific code paths.

    Special key: `historical_financials` may be passed directly; otherwise a
    10-year positive series is generated.
    """
    base: dict[str, Any] = {
        # Metadata
        "ticker": "TEST",
        "company_name": "Test Corporation",
        "sector": "Technology",
        "industry": "Software",
        "extraction_timestamp": datetime(2024, 1, 1, tzinfo=UTC),
        "data_confidence_score": 0.9,
        # Market position
        "current_price": 150.0,
        "shares_outstanding": 16_000_000_000.0,
        "market_cap": 2_400_000_000_000.0,
        "enterprise_value": 2_470_000_000_000.0,
        # Income statement (TTM)
        "ttm_revenue": 300_000_000_000.0,
        "ttm_cost_of_revenue": 170_000_000_000.0,
        "ttm_gross_profit": 130_000_000_000.0,
        "ttm_operating_expenses": 40_000_000_000.0,
        "ttm_operating_income": 90_000_000_000.0,
        "ttm_interest_expense": 3_000_000_000.0,
        "ttm_pretax_income": 95_000_000_000.0,
        "ttm_tax_expense": 15_000_000_000.0,
        "ttm_net_income": 80_000_000_000.0,
        "ttm_ebitda": 101_000_000_000.0,
        "ttm_eps": 5.0,
        # Cash flow (TTM)
        "ttm_operating_cash_flow": 95_000_000_000.0,
        "ttm_capital_expenditures": 10_000_000_000.0,
        "ttm_free_cash_flow": 85_000_000_000.0,
        "ttm_depreciation_amortization": 11_000_000_000.0,
        "ttm_stock_based_compensation": 8_000_000_000.0,
        "ttm_dividends_paid": 15_000_000_000.0,
        "ttm_share_repurchases": 70_000_000_000.0,
        # Balance sheet
        "cash_and_equivalents": 30_000_000_000.0,
        "short_term_investments": 30_000_000_000.0,
        "total_cash": 60_000_000_000.0,
        "accounts_receivable": 25_000_000_000.0,
        "inventory": 5_000_000_000.0,
        "total_current_assets": 120_000_000_000.0,
        "property_plant_equipment": 45_000_000_000.0,
        "goodwill": 0.0,
        "intangible_assets": 0.0,
        "total_assets": 350_000_000_000.0,
        "accounts_payable": 50_000_000_000.0,
        "short_term_debt": 15_000_000_000.0,
        "total_current_liabilities": 130_000_000_000.0,
        "long_term_debt": 85_000_000_000.0,
        "total_debt": 100_000_000_000.0,
        "total_liabilities": 280_000_000_000.0,
        "shareholders_equity": 70_000_000_000.0,
        "retained_earnings": 5_000_000_000.0,
        # Calculated position metrics
        "net_debt": 40_000_000_000.0,
        "working_capital": -10_000_000_000.0,
        "invested_capital": 110_000_000_000.0,
        # Profitability
        "gross_margin": 0.4333,
        "operating_margin": 0.30,
        "net_margin": 0.2667,
        "ebitda_margin": 0.3367,
        "roe": 1.142,
        "roa": 0.2286,
        "roic": 0.30,
        # Efficiency
        "asset_turnover": 0.857,
        # Leverage
        "debt_to_equity": 1.428,
        "debt_to_ebitda": 0.99,
        "interest_coverage": 30.0,
        # Liquidity
        "current_ratio": 0.923,
        "quick_ratio": 0.88,
        "cash_ratio": 0.46,
        # Multiples
        "pe_ratio": 30.0,
        "price_to_book": 34.0,
        # Growth
        "revenue_growth_5y_cagr": 0.10,
        "earnings_growth_10y_cagr": 0.12,
        # Risk
        "beta": 1.2,
        "risk_free_rate": 0.04,
        "equity_risk_premium": 0.05,
        # Dividends
        "dividend_per_share": 0.96,
        "dividend_yield": 0.0064,
    }

    historical = overrides.pop("historical_financials", None)
    base.update(overrides)
    if historical is None:
        historical = make_historical_series(10)
    base["historical_financials"] = historical

    return StandardizedValuationInput(**base)


def make_flexible_input(**overrides: Any) -> FlexibleValuationInput:
    """
    Build a reasonably complete FlexibleValuationInput for adapter/orchestration
    tests. Nested sections are passed as dicts; Pydantic builds the sub-models.
    Top-level overrides replace whole sections.
    """
    data: dict[str, Any] = {
        "ticker": "TEST",
        "company_name": "Test Corporation",
        "extraction_timestamp": datetime(2024, 1, 1, tzinfo=UTC),
        "data_confidence_score": 0.85,
        "metadata": {"sector": "Technology", "industry": "Software"},
        "market_position": {
            "current_price": 150.0,
            "shares_outstanding": 16_000_000_000.0,
            "market_cap": 2_400_000_000_000.0,
        },
        "ttm_income_statement": {
            "revenue": 300_000_000_000.0,
            "gross_profit": 130_000_000_000.0,
            "operating_income": 90_000_000_000.0,
            "net_income": 80_000_000_000.0,
            "ebitda": 101_000_000_000.0,
            "eps": 5.0,
        },
        "ttm_cash_flow": {
            "operating_cash_flow": 95_000_000_000.0,
            "capital_expenditures": 10_000_000_000.0,
        },
        "balance_sheet": {
            "total_cash": 60_000_000_000.0,
            "total_debt": 100_000_000_000.0,
            "total_assets": 350_000_000_000.0,
            "total_liabilities": 280_000_000_000.0,
            "shareholders_equity": 70_000_000_000.0,
            "total_current_assets": 120_000_000_000.0,
            "total_current_liabilities": 130_000_000_000.0,
        },
        "profitability_ratios": {"operating_margin": 0.30, "roic": 0.30},
        "leverage_ratios": {"interest_coverage": 30.0},
        "valuation_multiples": {"pe_ratio": 30.0, "price_to_book": 34.0},
        "growth_rates": {"revenue_growth_5y_cagr": 0.10},
        "risk_parameters": {"beta": 1.2, "risk_free_rate": 0.04},
        "dividends": {"dividend_yield": 0.0064},
        "historical_financials": [
            {"fiscal_year": y, "revenue": 300_000_000_000.0, "net_income": 80e9, "eps": 5.0}
            for y in range(2015, 2025)
        ],
    }
    data.update(overrides)
    return FlexibleValuationInput(**data)
