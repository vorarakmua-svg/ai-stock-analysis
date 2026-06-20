"""Merge SEC fundamentals + yfinance snapshot into the per-stock JSON shape."""

from __future__ import annotations

from typing import Any


def build_stock_data(
    *,
    ticker: str,
    cik: str,
    company_name: str,
    collected_at: str,
    sec_annual: dict[str, dict[str, Any]],
    yf_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the dict that will be validated and written to disk.

    ``collected_at`` is supplied by the caller (not generated here) so the output
    is deterministic for a given input — enabling idempotency checks.
    """
    ticker = ticker.upper().strip()
    yf_company = dict(yf_snapshot.get("company_info", {}))
    yf_company.setdefault("name", company_name)
    yf_company["ticker"] = ticker

    warnings: list[str] = []
    if not sec_annual:
        warnings.append("No annual financials parsed from SEC EDGAR")
    if not yf_snapshot.get("market_data", {}).get("current_price"):
        warnings.append("No current price from yfinance")

    return {
        "ticker": ticker,
        "cik": cik,
        "company_name": company_name or yf_company.get("name") or ticker,
        "collected_at": collected_at,
        "company_info": yf_company,
        "market_data": yf_snapshot.get("market_data", {}),
        "shareholders": yf_snapshot.get("shareholders", {}),
        "financials_annual": sec_annual,
        "data_sources": ["SEC EDGAR companyfacts", "yfinance"],
        "warnings": warnings,
    }
