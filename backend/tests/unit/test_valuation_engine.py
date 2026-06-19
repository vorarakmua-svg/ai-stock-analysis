"""
Unit tests for the deterministic valuation engine (the crown jewel).

These tests touch no AI and no network. Where a formula has a closed form
(WACC, Graham Number, credit spread, verdict, composite) the expected value is
hand-computed for true correctness. The full multi-year DCF is verified with a
frozen golden value (regression protection) plus structural invariants.
"""

import math

import pytest

from app.models.valuation_output import ValuationVerdict
from app.services.valuation_engine import ValuationEngine
from tests.fixtures.sample_inputs import make_historical, make_historical_series, make_input


# ---------------------------------------------------------------------------
# Credit spread table
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "coverage,expected",
    [
        (None, 0.05),
        (-1.0, 0.05),
        (0.0, 0.05),
        (1.0, 0.04),
        (1.49, 0.04),
        (1.5, 0.03),
        (2.9, 0.03),
        (3.0, 0.02),
        (4.9, 0.02),
        (5.0, 0.015),
        (7.9, 0.015),
        (8.0, 0.01),
        (11.9, 0.01),
        (12.0, 0.007),
        (100.0, 0.007),
    ],
)
def test_credit_spread_boundaries(engine: ValuationEngine, coverage, expected):
    assert engine._get_credit_spread(coverage) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# WACC
# ---------------------------------------------------------------------------
def test_wacc_matches_capm_formula(engine: ValuationEngine):
    inp = make_input()
    wacc, components = engine.calculate_wacc(inp)

    # Cost of equity = rf + beta * erp = 0.04 + 1.2 * 0.05 = 0.10
    assert components["cost_of_equity"] == pytest.approx(0.10)
    # interest_coverage=30 -> best tier spread 0.7%
    assert components["credit_spread"] == pytest.approx(0.007)
    # after-tax cost of debt = (0.04 + 0.007) * (1 - 0.21)
    assert components["cost_of_debt_aftertax"] == pytest.approx(0.047 * 0.79)
    # weights: E=2.4e12, D=0.1e12 -> 0.96 / 0.04
    assert components["equity_weight"] == pytest.approx(0.96)
    assert components["debt_weight"] == pytest.approx(0.04)
    # WACC = 0.96*0.10 + 0.04*0.03713
    assert wacc == pytest.approx(0.0974852)


def test_wacc_defaults_beta_to_one_when_missing(engine: ValuationEngine):
    inp = make_input(beta=None)
    _, components = engine.calculate_wacc(inp)
    # cost of equity = 0.04 + 1.0 * 0.05 = 0.09
    assert components["beta"] == pytest.approx(1.0)
    assert components["cost_of_equity"] == pytest.approx(0.09)


def test_wacc_falls_back_to_all_equity_when_no_capital(engine: ValuationEngine):
    # market_cap must be > 0 by the model, but total_debt can be 0 and the
    # guard clamps negatives; force the all-equity branch via market_cap clamp.
    inp = make_input(market_cap=1.0, total_debt=0.0)
    wacc, components = engine.calculate_wacc(inp)
    assert components["equity_weight"] == pytest.approx(1.0)
    assert components["debt_weight"] == pytest.approx(0.0)
    assert wacc == pytest.approx(components["cost_of_equity"])


# ---------------------------------------------------------------------------
# Graham Number
# ---------------------------------------------------------------------------
def test_graham_number_closed_form(engine: ValuationEngine):
    inp = make_input()
    result = engine.calculate_graham_number(inp)
    # bvps = equity / shares = 70e9 / 16e9 = 4.375
    assert result.book_value_per_share == pytest.approx(4.375)
    expected = math.sqrt(22.5 * 5.0 * 4.375)
    assert result.graham_number == pytest.approx(expected)
    assert result.graham_number == pytest.approx(22.185299, abs=1e-4)


def test_graham_number_zero_for_negative_eps(engine: ValuationEngine):
    inp = make_input(ttm_eps=-1.0)
    result = engine.calculate_graham_number(inp)
    assert result.graham_number == 0.0
    # Not applicable -> upside sentinel of -1.0
    assert result.upside_pct == pytest.approx(-1.0)


def test_graham_number_zero_for_negative_book_value(engine: ValuationEngine):
    inp = make_input(shareholders_equity=-10_000_000_000.0)
    result = engine.calculate_graham_number(inp)
    assert result.graham_number == 0.0


# ---------------------------------------------------------------------------
# Verdict thresholds
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "upside,expected",
    [
        (0.50, ValuationVerdict.SIGNIFICANTLY_UNDERVALUED),
        (0.41, ValuationVerdict.SIGNIFICANTLY_UNDERVALUED),
        (0.40, ValuationVerdict.UNDERVALUED),  # boundary: not strictly > 0.40
        (0.20, ValuationVerdict.UNDERVALUED),
        (0.15, ValuationVerdict.FAIRLY_VALUED),  # boundary: not strictly > 0.15
        (0.0, ValuationVerdict.FAIRLY_VALUED),
        (-0.15, ValuationVerdict.FAIRLY_VALUED),  # inclusive lower bound
        (-0.16, ValuationVerdict.OVERVALUED),
        (-0.40, ValuationVerdict.OVERVALUED),  # inclusive
        (-0.41, ValuationVerdict.SIGNIFICANTLY_OVERVALUED),
    ],
)
def test_determine_verdict(engine: ValuationEngine, upside, expected):
    assert engine.determine_verdict(upside) == expected


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------
def test_composite_weights_60_40(engine: ValuationEngine):
    composite, methodology = engine.calculate_composite(100.0, 50.0)
    assert composite == pytest.approx(0.60 * 100.0 + 0.40 * 50.0)
    assert "60% DCF" in methodology and "40% Graham" in methodology


def test_composite_falls_back_to_dcf_when_graham_zero(engine: ValuationEngine):
    composite, methodology = engine.calculate_composite(100.0, 0.0)
    assert composite == pytest.approx(100.0)
    assert "100% DCF" in methodology


# ---------------------------------------------------------------------------
# DCF — golden value + invariants + edge cases
# ---------------------------------------------------------------------------
def test_dcf_golden_value(engine: ValuationEngine):
    """Regression guard: frozen output for the baseline fixture."""
    inp = make_input()
    dcf = engine.calculate_dcf(inp)
    assert dcf.weighted_intrinsic_value == pytest.approx(58.952999, abs=1e-4)
    assert dcf.conservative.intrinsic_value_per_share == pytest.approx(45.240676, abs=1e-4)
    assert dcf.base_case.intrinsic_value_per_share == pytest.approx(58.664363, abs=1e-4)
    assert dcf.optimistic.intrinsic_value_per_share == pytest.approx(73.242593, abs=1e-4)


def test_dcf_weighted_iv_is_scenario_weighted_average(engine: ValuationEngine):
    inp = make_input()
    dcf = engine.calculate_dcf(inp)
    expected = (
        0.25 * dcf.conservative.intrinsic_value_per_share
        + 0.50 * dcf.base_case.intrinsic_value_per_share
        + 0.25 * dcf.optimistic.intrinsic_value_per_share
    )
    assert dcf.weighted_intrinsic_value == pytest.approx(expected)


def test_dcf_wacc_sensitivity_is_monotonic(engine: ValuationEngine):
    inp = make_input()
    dcf = engine.calculate_dcf(inp)
    # Lower discount rate -> higher value; higher rate -> lower value.
    assert (
        dcf.sensitivity_to_wacc["wacc_minus_1pct"]
        > dcf.base_case.intrinsic_value_per_share
        > dcf.sensitivity_to_wacc["wacc_plus_1pct"]
    )


def test_dcf_zero_shares_yields_zero_intrinsic(engine: ValuationEngine):
    # shares_outstanding > 0 enforced by the model; patch after construction to
    # exercise the divide-by-zero guard in the engine.
    inp = make_input()
    object.__setattr__(inp, "shares_outstanding", 0.0)
    scenario = engine.calculate_dcf_scenario(
        input_data=inp,
        scenario_name="base_case",
        growth_rate=0.10,
        terminal_growth=0.025,
        operating_margin=0.30,
        wacc=0.097,
    )
    assert scenario.intrinsic_value_per_share == 0.0


def test_dcf_adjusts_terminal_growth_when_exceeds_wacc(engine: ValuationEngine):
    """When WACC <= terminal growth, the engine clamps to wacc - 1% (no blow-up)."""
    inp = make_input()
    scenario = engine.calculate_dcf_scenario(
        input_data=inp,
        scenario_name="base_case",
        growth_rate=0.10,
        terminal_growth=0.05,
        operating_margin=0.30,
        wacc=0.04,  # below terminal growth
    )
    assert math.isfinite(scenario.terminal_value)
    assert scenario.intrinsic_value_per_share >= 0.0


def test_dcf_handles_negative_base_growth(engine: ValuationEngine):
    """Negative 5y CAGR is floored to a 3% assumption rather than shrinking."""
    inp = make_input(revenue_growth_5y_cagr=-0.10)
    dcf = engine.calculate_dcf(inp)
    # base_case growth assumption should be the 0.03 floor
    assert dcf.base_case.revenue_growth_rate == pytest.approx(0.03)
    assert dcf.weighted_intrinsic_value >= 0.0


# ---------------------------------------------------------------------------
# Graham defensive screen
# ---------------------------------------------------------------------------
def test_graham_screen_strong_company_passes(engine: ValuationEngine):
    # Make a company that clears most criteria: cheap valuation + dividends +
    # high current ratio + 10y positive earnings + EPS growth.
    inp = make_input(
        current_ratio=2.5,
        pe_ratio=12.0,
        price_to_book=1.2,
        dividend_yield=0.02,
        historical_financials=make_historical_series(10, start_eps=3.0, end_eps=6.0),
    )
    screen = engine.calculate_graham_screen(inp)
    assert screen.adequate_size is True  # revenue 300B >= 700M
    assert screen.strong_financial_condition is True
    assert screen.earnings_stability is True
    assert screen.dividend_record is True
    assert screen.passes_screen is True
    assert screen.criteria_passed >= 5


def test_graham_screen_expensive_company_fails(engine: ValuationEngine):
    inp = make_input(
        current_ratio=0.9,
        pe_ratio=30.0,
        price_to_book=34.0,
        dividend_yield=0.0,
        historical_financials=make_historical_series(10, positive=False),
    )
    screen = engine.calculate_graham_screen(inp)
    assert screen.passes_screen is False
    assert screen.criteria_passed < 5


def test_graham_screen_uses_cagr_when_history_short(engine: ValuationEngine):
    """With <10 years of history, EPS growth is estimated from the 10y CAGR."""
    inp = make_input(
        earnings_growth_10y_cagr=0.05,  # (1.05)^10 - 1 ~= 0.629 >= 0.33
        historical_financials=make_historical_series(5),
    )
    screen = engine.calculate_graham_screen(inp)
    assert screen.eps_10y_growth == pytest.approx((1.05) ** 10 - 1)
    assert screen.earnings_growth is True


def test_graham_screen_counts_only_positive_earnings_years(engine: ValuationEngine):
    history = make_historical_series(10)
    # Flip two years negative.
    history[0] = make_historical(history[0].fiscal_year, net_income=-1.0, eps=-1.0)
    history[1] = make_historical(history[1].fiscal_year, net_income=-1.0, eps=-1.0)
    inp = make_input(historical_financials=history)
    screen = engine.calculate_graham_screen(inp)
    assert screen.years_positive_earnings == 8
    assert screen.earnings_stability is False  # needs 10


# ---------------------------------------------------------------------------
# Confidence score
# ---------------------------------------------------------------------------
def test_confidence_score_full_data(engine: ValuationEngine):
    inp = make_input()  # confidence 0.9, 10y history, consistent scenarios
    dcf = engine.calculate_dcf(inp)
    score = engine._calculate_confidence_score(inp, dcf)
    # 0.9*0.5 + 1.0*0.25 + 1.0*0.25 = 0.95
    assert score == pytest.approx(0.95)


def test_confidence_score_penalizes_short_history(engine: ValuationEngine):
    full = make_input()
    short = make_input(historical_financials=make_historical_series(3))
    dcf_full = engine.calculate_dcf(full)
    dcf_short = engine.calculate_dcf(short)
    assert engine._calculate_confidence_score(
        short, dcf_short
    ) < engine._calculate_confidence_score(full, dcf_full)


def test_confidence_score_clamped_to_unit_interval(engine: ValuationEngine):
    inp = make_input(data_confidence_score=1.0)
    dcf = engine.calculate_dcf(inp)
    score = engine._calculate_confidence_score(inp, dcf)
    assert 0.0 <= score <= 1.0
