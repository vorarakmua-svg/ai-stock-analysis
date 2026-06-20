"""Tests for the SEC EDGAR client (User-Agent + rate-limit) and parser."""

import httpx
import pytest
import respx

from ingestion.sources.sec_edgar import SECEdgarClient, parse_annual_financials


@respx.mock
async def test_get_company_facts_sends_user_agent():
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    route = respx.get(url).mock(
        return_value=httpx.Response(200, json={"entityName": "Apple Inc.", "facts": {}})
    )
    client = SECEdgarClient("IIP test@example.com", max_requests_per_second=1000)

    facts = await client.get_company_facts("0000320193")

    assert facts["entityName"] == "Apple Inc."
    assert route.calls.last.request.headers["User-Agent"] == "IIP test@example.com"


def test_client_requires_user_agent():
    with pytest.raises(ValueError):
        SECEdgarClient("")


def _facts(**concepts):
    return {"facts": {"us-gaap": concepts}}


def test_parse_keeps_only_annual_10k_fy_values():
    facts = _facts(
        Assets={
            "units": {
                "USD": [
                    {"fy": 2023, "fp": "FY", "form": "10-K", "val": 1000},
                    {"fy": 2022, "fp": "FY", "form": "10-K", "val": 900},
                    {"fy": 2023, "fp": "Q3", "form": "10-Q", "val": 950},  # ignored
                ]
            }
        },
        NetIncomeLoss={"units": {"USD": [{"fy": 2023, "fp": "FY", "form": "10-K", "val": 200}]}},
        EarningsPerShareDiluted={
            "units": {"USD/shares": [{"fy": 2023, "fp": "FY", "form": "10-K", "val": 6.0}]}
        },
    )
    result = parse_annual_financials(facts)

    assert result["2023"]["Total Assets"] == 1000
    assert result["2023"]["Net Income"] == 200
    assert result["2023"]["EPS Diluted"] == 6.0
    assert result["2023"]["fiscal_year"] == 2023
    assert "2022" in result
    # Quarterly entry excluded -> only the FY value remains.
    assert result["2023"]["Total Assets"] == 1000


def test_parse_uses_concept_fallback():
    # Primary revenue concept absent; should fall back to "Revenues".
    facts = _facts(
        Revenues={"units": {"USD": [{"fy": 2023, "fp": "FY", "form": "10-K", "val": 500}]}},
    )
    result = parse_annual_financials(facts)
    assert result["2023"]["Total Revenue"] == 500


def test_parse_empty_when_no_gaap():
    assert parse_annual_financials({"facts": {}}) == {}
