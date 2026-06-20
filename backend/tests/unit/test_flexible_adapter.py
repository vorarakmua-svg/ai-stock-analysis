"""
Tests for FlexibleInputAdapter — the shape the engine actually consumes in
production (use_flexible=True). Focuses on the derivation/fallback logic that
fills gaps when the AI returns partial data.
"""

import pytest

from app.services.valuation_engine import FlexibleInputAdapter
from tests.fixtures.sample_inputs import make_flexible_input


def _adapter(**overrides):
    return FlexibleInputAdapter(make_flexible_input(**overrides))


def test_passthrough_fields():
    a = _adapter()
    assert a.ticker == "TEST"
    assert a.current_price == 150.0
    assert a.sector == "Technology"


def test_free_cash_flow_derived_from_ocf_minus_capex():
    a = _adapter(ttm_cash_flow={"operating_cash_flow": 95e9, "capital_expenditures": 10e9})
    assert a.ttm_free_cash_flow == pytest.approx(85e9)


def test_shares_outstanding_fallback_from_market_cap():
    a = _adapter(market_position={"current_price": 100.0, "market_cap": 1_000_000_000.0})
    # shares = market_cap / price = 1e9 / 100 = 1e7
    assert a.shares_outstanding == pytest.approx(10_000_000.0)


def test_shares_outstanding_last_resort_default():
    a = _adapter(market_position={"current_price": 100.0})
    assert a.shares_outstanding == 1_000_000


def test_market_cap_derived_from_price_times_shares():
    a = _adapter(market_position={"current_price": 10.0, "shares_outstanding": 2_000_000.0})
    assert a.market_cap == pytest.approx(20_000_000.0)


def test_enterprise_value_derived():
    a = _adapter()
    # EV = market_cap + total_debt - total_cash
    assert a.enterprise_value == pytest.approx(2_400e9 + 100e9 - 60e9)


def test_shareholders_equity_derived_from_assets_minus_liabilities():
    a = _adapter(
        balance_sheet={
            "total_assets": 350e9,
            "total_liabilities": 280e9,
            "total_cash": 60e9,
            "total_debt": 100e9,
        }
    )
    assert a.shareholders_equity == pytest.approx(70e9)


def test_net_debt_derived():
    a = _adapter()
    assert a.net_debt == pytest.approx(100e9 - 60e9)


def test_current_ratio_derived():
    a = _adapter()
    assert a.current_ratio == pytest.approx(120e9 / 130e9)


def test_debt_to_equity_derived():
    a = _adapter()
    assert a.debt_to_equity == pytest.approx(100e9 / 70e9)


def test_roic_defaults_to_ten_percent_when_missing():
    a = _adapter(profitability_ratios={"operating_margin": 0.3})
    assert a.roic == pytest.approx(0.10)


def test_equity_risk_premium_is_fixed_default():
    a = _adapter()
    assert a.equity_risk_premium == pytest.approx(0.05)


def test_revenue_growth_5y_cagr_passthrough_when_provided():
    a = _adapter(growth_rates={"revenue_growth_5y_cagr": 0.123})
    assert a.revenue_growth_5y_cagr == pytest.approx(0.123)


def test_revenue_growth_5y_cagr_falls_back_to_1y_then_default():
    # No 5y CAGR and short history -> use 1y growth if present...
    a = _adapter(growth_rates={"revenue_growth_1y": 0.07}, historical_financials=[])
    assert a.revenue_growth_5y_cagr == pytest.approx(0.07)
    # ...otherwise the 5% default.
    b = _adapter(growth_rates={}, historical_financials=[])
    assert b.revenue_growth_5y_cagr == pytest.approx(0.05)


def test_revenue_growth_5y_cagr_computed_from_history():
    # 6 entries span 5 years; oldest (2019) = 100, newest (2024) = 100 * 1.1^5.
    history = [
        {"fiscal_year": 2019, "revenue": 100.0},
        {"fiscal_year": 2020, "revenue": 110.0},
        {"fiscal_year": 2021, "revenue": 121.0},
        {"fiscal_year": 2022, "revenue": 133.1},
        {"fiscal_year": 2023, "revenue": 146.41},
        {"fiscal_year": 2024, "revenue": 161.051},
    ]
    a = _adapter(growth_rates={}, historical_financials=history)
    # (161.051/100)^(1/5) - 1 == 0.10
    assert a.revenue_growth_5y_cagr == pytest.approx(0.10, abs=1e-4)


def test_revenue_growth_5y_cagr_uses_actual_span_for_short_history():
    # 5 entries span only 4 years: (133.1/100)^(1/4) - 1.
    history = [
        {"fiscal_year": 2020, "revenue": 100.0},
        {"fiscal_year": 2021, "revenue": 110.0},
        {"fiscal_year": 2022, "revenue": 121.0},
        {"fiscal_year": 2023, "revenue": 127.0},
        {"fiscal_year": 2024, "revenue": 133.1},
    ]
    a = _adapter(growth_rates={}, historical_financials=history)
    assert a.revenue_growth_5y_cagr == pytest.approx((133.1 / 100) ** (1 / 4) - 1, abs=1e-4)
