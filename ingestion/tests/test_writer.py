"""Tests for atomic/idempotent writers."""

import json

from ingestion.writer import (
    build_summary_row,
    write_manifest,
    write_stock_json,
    write_summary_csv,
)


def _data(ticker="AAPL", collected_at="2024-01-01T00:00:00+00:00"):
    return {
        "ticker": ticker,
        "cik": "0000320193",
        "company_name": "Apple Inc.",
        "collected_at": collected_at,
        "company_info": {"sector": "Technology", "industry": "CE"},
        "market_data": {"current_price": 150.0, "market_cap": 1e9, "beta": 1.1},
        "financials_annual": {"2023": {"fiscal_year": 2023}},
    }


def test_write_then_unchanged_when_only_collected_at_differs(tmp_path):
    json_dir = tmp_path / "json"

    assert write_stock_json(_data(), json_dir) == "written"
    target = json_dir / "AAPL.json"
    original = json.loads(target.read_text())

    # Re-run with a different timestamp but identical content.
    assert (
        write_stock_json(_data(collected_at="2025-09-09T00:00:00+00:00"), json_dir) == "unchanged"
    )
    # File preserved (still the original timestamp).
    assert json.loads(target.read_text())["collected_at"] == original["collected_at"]


def test_write_rewrites_on_real_change(tmp_path):
    json_dir = tmp_path / "json"
    write_stock_json(_data(), json_dir)

    changed = _data()
    changed["market_data"]["current_price"] = 200.0
    assert write_stock_json(changed, json_dir) == "written"
    assert json.loads((json_dir / "AAPL.json").read_text())["market_data"]["current_price"] == 200.0


def test_no_tmp_file_left_behind(tmp_path):
    json_dir = tmp_path / "json"
    write_stock_json(_data(), json_dir)
    assert not list(json_dir.glob("*.tmp"))


def test_summary_csv_written_sorted(tmp_path):
    rows = [build_summary_row(_data("MSFT")), build_summary_row(_data("AAPL"))]
    csv_path = tmp_path / "csv" / "summary.csv"
    write_summary_csv(rows, csv_path)

    lines = csv_path.read_text().splitlines()
    assert lines[0].startswith("ticker,")
    # Sorted by ticker -> AAPL before MSFT.
    assert lines[1].startswith("AAPL,")
    assert lines[2].startswith("MSFT,")


def test_manifest_written(tmp_path):
    path = tmp_path / "_manifest.json"
    write_manifest(path, {"total": 1, "written": 1})
    assert json.loads(path.read_text())["written"] == 1
