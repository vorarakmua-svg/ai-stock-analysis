"""Tests for transform + validate."""

import pytest

from ingestion.transform import build_stock_data
from ingestion.validate import ValidationFailed, validate_stock_data


def _snapshot(price=150.0):
    return {
        "market_data": {"current_price": price, "market_cap": 1_000_000_000.0, "beta": 1.1},
        "company_info": {"name": "Apple Inc.", "sector": "Technology", "industry": "CE"},
        "shareholders": {"shares_outstanding": 16_000_000_000.0},
    }


def test_build_stock_data_merges_sources():
    data = build_stock_data(
        ticker="aapl",
        cik="0000320193",
        company_name="Apple Inc.",
        collected_at="2024-01-01T00:00:00+00:00",
        sec_annual={"2023": {"fiscal_year": 2023, "Net Income": 200}},
        yf_snapshot=_snapshot(),
    )
    assert data["ticker"] == "AAPL"
    assert data["company_info"]["ticker"] == "AAPL"
    assert data["market_data"]["current_price"] == 150.0
    assert data["financials_annual"]["2023"]["Net Income"] == 200
    assert "SEC EDGAR companyfacts" in data["data_sources"]
    assert data["warnings"] == []


def test_build_stock_data_warns_on_missing_data():
    data = build_stock_data(
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        collected_at="2024-01-01T00:00:00+00:00",
        sec_annual={},
        yf_snapshot={"market_data": {}, "company_info": {"name": "Apple"}, "shareholders": {}},
    )
    assert any("annual financials" in w for w in data["warnings"])
    assert any("current price" in w for w in data["warnings"])


def test_validate_accepts_good_data():
    data = build_stock_data(
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        collected_at="2024-01-01T00:00:00+00:00",
        sec_annual={"2023": {"fiscal_year": 2023}},
        yf_snapshot=_snapshot(),
    )
    validated = validate_stock_data(data)
    assert validated.ticker == "AAPL"


def test_validate_rejects_missing_required_fields():
    with pytest.raises(ValidationFailed):
        validate_stock_data({"ticker": "AAPL"})  # missing cik, company_name, etc.
