"""End-to-end pipeline tests (SEC mocked via respx, yfinance injected)."""

import json

import httpx
import pytest
import respx

from ingestion.config import IngestionConfig
from ingestion.pipeline import run_refresh
from ingestion.universe import _load_cik_index, resolve_cik


@pytest.fixture
def cik_map(tmp_path):
    path = tmp_path / "company_tickers.json"
    path.write_text(json.dumps({"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple"}}))
    _load_cik_index.cache_clear()
    return path


@pytest.fixture
def config(tmp_path, cik_map):
    return IngestionConfig(
        sec_user_agent="IIP test@example.com",
        output_dir=tmp_path / "out",
        cik_map_path=cik_map,
        sec_max_requests_per_second=1000.0,
    )


def _fake_fetcher(ticker):
    return {
        "market_data": {"current_price": 150.0, "market_cap": 1e9, "beta": 1.1},
        "company_info": {"name": "Apple Inc.", "sector": "Technology", "industry": "CE"},
        "shareholders": {"shares_outstanding": 16e9},
    }


_FACTS = {
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "Assets": {"units": {"USD": [{"fy": 2023, "fp": "FY", "form": "10-K", "val": 1000}]}},
            "NetIncomeLoss": {
                "units": {"USD": [{"fy": 2023, "fp": "FY", "form": "10-K", "val": 200}]}
            },
        }
    },
}


def test_resolve_cik(cik_map):
    assert resolve_cik("aapl", cik_map) == "0000320193"
    with pytest.raises(KeyError):
        resolve_cik("ZZZZ", cik_map)


@respx.mock
async def test_run_refresh_writes_and_is_idempotent(config):
    respx.get("https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json").mock(
        return_value=httpx.Response(200, json=_FACTS)
    )

    manifest = await run_refresh(["AAPL"], config=config, market_fetcher=_fake_fetcher)
    assert manifest["written"] == 1
    assert manifest["errors"] == 0

    out_file = config.json_dir / "AAPL.json"
    assert out_file.exists()
    written = json.loads(out_file.read_text())
    assert written["financials_annual"]["2023"]["Net Income"] == 200
    assert config.csv_path.exists()
    assert config.manifest_path.exists()

    # Second run with identical source data -> unchanged (idempotent).
    manifest2 = await run_refresh(["AAPL"], config=config, market_fetcher=_fake_fetcher)
    assert manifest2["unchanged"] == 1
    assert manifest2["written"] == 0


@respx.mock
async def test_run_refresh_isolates_errors(config):
    # AAPL succeeds; ZZZZ has no CIK -> error, but the run completes.
    respx.get("https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json").mock(
        return_value=httpx.Response(200, json=_FACTS)
    )
    manifest = await run_refresh(["AAPL", "ZZZZ"], config=config, market_fetcher=_fake_fetcher)
    assert manifest["written"] == 1
    assert manifest["errors"] == 1
    statuses = {e["ticker"]: e["status"] for e in manifest["entries"]}
    assert statuses["ZZZZ"] == "error"


@respx.mock
async def test_dry_run_writes_nothing(config):
    respx.get("https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json").mock(
        return_value=httpx.Response(200, json=_FACTS)
    )
    manifest = await run_refresh(
        ["AAPL"], config=config, market_fetcher=_fake_fetcher, dry_run=True
    )
    assert manifest["entries"][0]["status"] == "dry_run"
    assert not config.json_dir.exists()
