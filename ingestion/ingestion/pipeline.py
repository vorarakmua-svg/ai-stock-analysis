"""Orchestration: fetch -> transform -> validate -> write, with a run manifest."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from ingestion.config import IngestionConfig
from ingestion.sources.sec_edgar import SECEdgarClient, parse_annual_financials
from ingestion.sources.yfinance_source import fetch_market_snapshot
from ingestion.transform import build_stock_data
from ingestion.universe import resolve_cik
from ingestion.validate import validate_stock_data
from ingestion.writer import (
    build_summary_row,
    write_manifest,
    write_stock_json,
    write_summary_csv,
)

logger = logging.getLogger(__name__)

# A market fetcher takes a ticker and returns a normalized snapshot dict.
MarketFetcher = Callable[[str], dict[str, Any]]


async def refresh_one(
    ticker: str,
    *,
    config: IngestionConfig,
    sec_client: SECEdgarClient,
    collected_at: str,
    market_fetcher: MarketFetcher,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Refresh a single ticker. Returns a manifest entry dict (never raises)."""
    ticker = ticker.upper().strip()
    entry: dict[str, Any] = {"ticker": ticker, "status": "error"}
    try:
        cik = resolve_cik(ticker, config.cik_map_path)
        facts = await sec_client.get_company_facts(cik)
        sec_annual = parse_annual_financials(facts)
        company_name = facts.get("entityName", "") or ticker

        # yfinance is blocking; keep the event loop free.
        yf_snapshot = await asyncio.to_thread(market_fetcher, ticker)

        data = build_stock_data(
            ticker=ticker,
            cik=cik,
            company_name=company_name,
            collected_at=collected_at,
            sec_annual=sec_annual,
            yf_snapshot=yf_snapshot,
        )
        validate_stock_data(data)  # raises ValidationFailed on contract breach

        if dry_run:
            entry["status"] = "dry_run"
        else:
            entry["status"] = write_stock_json(data, config.json_dir)

        entry["years"] = len(sec_annual)
        entry["warnings"] = data["warnings"]
        entry["_row"] = build_summary_row(data)
    except Exception as exc:  # noqa: BLE001 - per-ticker isolation
        logger.exception("Failed to refresh %s", ticker)
        entry["status"] = "error"
        entry["error"] = f"{type(exc).__name__}: {exc}"
    return entry


async def run_refresh(
    tickers: list[str],
    *,
    config: IngestionConfig | None = None,
    market_fetcher: MarketFetcher | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Refresh many tickers, write summary.csv + manifest, return the manifest."""
    config = config or IngestionConfig()
    market_fetcher = market_fetcher or fetch_market_snapshot
    collected_at = datetime.now(UTC).isoformat()

    sec_client = SECEdgarClient(
        config.require_sec_user_agent(),
        base_url=config.sec_base_url,
        max_requests_per_second=config.sec_max_requests_per_second,
        timeout=config.request_timeout_seconds,
    )

    entries: list[dict[str, Any]] = []
    for ticker in tickers:
        entries.append(
            await refresh_one(
                ticker,
                config=config,
                sec_client=sec_client,
                collected_at=collected_at,
                market_fetcher=market_fetcher,
                dry_run=dry_run,
            )
        )

    rows = [e.pop("_row") for e in entries if "_row" in e]
    if rows and not dry_run:
        write_summary_csv(rows, config.csv_path)

    manifest = {
        "run_at": collected_at,
        "dry_run": dry_run,
        "total": len(entries),
        "written": sum(1 for e in entries if e["status"] == "written"),
        "unchanged": sum(1 for e in entries if e["status"] == "unchanged"),
        "errors": sum(1 for e in entries if e["status"] == "error"),
        "entries": entries,
    }
    if not dry_run:
        write_manifest(config.manifest_path, manifest)
    return manifest
