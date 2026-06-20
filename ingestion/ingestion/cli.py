"""Command-line entry point: ``python -m ingestion.cli refresh ...``."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from ingestion.config import IngestionConfig
from ingestion.pipeline import run_refresh
from ingestion.universe import DEFAULT_UNIVERSE


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ingestion", description="Stock data pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    refresh = sub.add_parser("refresh", help="Fetch + write per-stock data")
    group = refresh.add_mutually_exclusive_group()
    group.add_argument("--tickers", help="Comma-separated tickers (e.g. AAPL,MSFT)")
    group.add_argument("--all", action="store_true", help="Refresh the default universe")
    refresh.add_argument("--dry-run", action="store_true", help="Fetch + validate, don't write")
    refresh.add_argument("--log-level", default="INFO")
    return parser.parse_args(argv)


def _resolve_tickers(args: argparse.Namespace) -> list[str]:
    if args.all or not args.tickers:
        return list(DEFAULT_UNIVERSE)
    return [t.strip().upper() for t in args.tickers.split(",") if t.strip()]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(name)s: %(message)s")

    tickers = _resolve_tickers(args)
    config = IngestionConfig()
    manifest = asyncio.run(run_refresh(tickers, config=config, dry_run=args.dry_run))

    print(
        f"refresh complete: {manifest['written']} written, "
        f"{manifest['unchanged']} unchanged, {manifest['errors']} errors "
        f"(of {manifest['total']})"
    )
    for entry in manifest["entries"]:
        if entry["status"] == "error":
            print(f"  ERROR {entry['ticker']}: {entry.get('error')}", file=sys.stderr)

    # Non-zero exit if anything failed, so CI/cron surfaces it.
    return 1 if manifest["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
