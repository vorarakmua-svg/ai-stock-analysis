#!/usr/bin/env python3
"""
CLI Tool for Ingesting Financial Data.

Usage:
    python ingest_ticker.py --ticker AAPL --market US
    python ingest_ticker.py --ticker PTT --market SET
    python ingest_ticker.py --ticker AAPL --market US --years 10 --no-prices
    python ingest_ticker.py --ticker MSFT,GOOGL,AAPL --market US --bulk
    python ingest_ticker.py --ticker AAPL --market US --provider eod

Examples:
    # Ingest 30 years of Apple data (auto-selects provider)
    python ingest_ticker.py --ticker AAPL --market US

    # Ingest Thai stock PTT
    python ingest_ticker.py --ticker PTT --market SET

    # Ingest only 10 years without prices
    python ingest_ticker.py --ticker AAPL --market US --years 10 --no-prices

    # Force refresh existing data
    python ingest_ticker.py --ticker AAPL --market US --force

    # Use specific provider
    python ingest_ticker.py --ticker AAPL --market US --provider eod
    python ingest_ticker.py --ticker AAPL --market US --provider fmp

    # Bulk ingest multiple tickers
    python ingest_ticker.py --ticker AAPL,MSFT,GOOGL --market US --bulk
"""

import argparse
import asyncio
import logging
import sys
import os
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings
from app.database import async_session_maker
from app.data_providers.fmp import FMPDataProvider
from app.data_providers.eodhd import EODDataProvider
from app.data_providers.base import AbstractDataProvider
from app.services.ingestion import IngestionService, bulk_ingest
from app.services.ticker_resolver import TickerResolver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest financial data for stock tickers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--ticker", "-t",
        required=True,
        help="Stock ticker symbol(s). For bulk mode, use comma-separated values (e.g., AAPL,MSFT,GOOGL)"
    )

    parser.add_argument(
        "--market", "-m",
        required=True,
        choices=["US", "SET"],
        help="Market: US (NYSE/NASDAQ) or SET (Thai Stock Exchange)"
    )

    parser.add_argument(
        "--years", "-y",
        type=int,
        default=30,
        help="Number of years of history to fetch (default: 30)"
    )

    parser.add_argument(
        "--provider", "-p",
        choices=["fmp", "eod", "auto"],
        default="auto",
        help="Data provider: fmp (Financial Modeling Prep), eod (EOD Historical Data), or auto (default: auto)"
    )

    parser.add_argument(
        "--no-prices",
        action="store_true",
        help="Skip fetching stock prices (faster)"
    )

    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force refresh all data (ignore cache)"
    )

    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Enable bulk mode for multiple tickers"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between tickers in bulk mode (seconds, default: 1.0)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


def get_provider(provider_name: str) -> Optional[AbstractDataProvider]:
    """
    Get the data provider instance.

    Args:
        provider_name: 'fmp', 'eod', or 'auto'

    Returns:
        Provider instance or None if no valid key available
    """
    settings = get_settings()

    if provider_name == "fmp":
        if settings.fmp_api_key:
            return FMPDataProvider(api_key=settings.fmp_api_key)
        logger.error("FMP_API_KEY not set")
        return None

    elif provider_name == "eod":
        if settings.eod_api_key:
            return EODDataProvider(api_key=settings.eod_api_key)
        logger.error("EOD_API_KEY not set")
        return None

    else:  # auto
        # Try FMP first, then EOD
        if settings.fmp_api_key:
            logger.info("Auto-selected provider: FMP")
            return FMPDataProvider(api_key=settings.fmp_api_key)
        elif settings.eod_api_key:
            logger.info("Auto-selected provider: EOD")
            return EODDataProvider(api_key=settings.eod_api_key)
        else:
            logger.error("No API keys configured. Set FMP_API_KEY or EOD_API_KEY")
            return None


async def ingest_single_ticker(
    ticker: str,
    market: str,
    years: int,
    include_prices: bool,
    force_refresh: bool,
    provider_name: str = "auto",
) -> Dict:
    """Ingest a single ticker."""
    # Get provider
    provider = get_provider(provider_name)
    if not provider:
        return {"ticker": ticker, "errors": ["No API key configured"]}

    # Run ingestion
    async with async_session_maker() as session:
        service = IngestionService(session, provider)
        stats = await service.ingest_ticker(
            ticker=ticker,
            market=market,
            years=years,
            include_prices=include_prices,
            force_refresh=force_refresh,
        )
        return stats


async def ingest_multiple_tickers(
    tickers: List[str],
    market: str,
    years: int,
    include_prices: bool,
    force_refresh: bool,
    delay: float,
    provider_name: str = "auto",
) -> List[Dict]:
    """Ingest multiple tickers with rate limiting."""
    provider = get_provider(provider_name)
    if not provider:
        return [{"ticker": t, "errors": ["No API key configured"]} for t in tickers]

    results = []
    async with async_session_maker() as session:
        service = IngestionService(session, provider)

        for i, ticker in enumerate(tickers):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {i+1}/{len(tickers)}: {ticker}")
            logger.info(f"{'='*60}")

            stats = await service.ingest_ticker(
                ticker=ticker,
                market=market,
                years=years,
                include_prices=include_prices,
                force_refresh=force_refresh,
            )
            results.append(stats)

            # Print summary for this ticker
            print_ticker_summary(stats)

            # Rate limiting between tickers
            if i < len(tickers) - 1:
                logger.info(f"Waiting {delay} seconds before next ticker...")
                await asyncio.sleep(delay)

    return results


def print_ticker_summary(stats: Dict):
    """Print summary for a single ticker ingestion."""
    ticker = stats.get("ticker", "Unknown")
    market = stats.get("market", "Unknown")

    print(f"\n--- Summary for {ticker} ({market}) ---")

    if stats.get("company_created"):
        print("  [NEW] Company profile created")
    else:
        print("  [OK] Company profile exists")

    print(f"  Income Statements: +{stats.get('income_statements_added', 0)}")
    print(f"  Balance Sheets:    +{stats.get('balance_sheets_added', 0)}")
    print(f"  Cash Flows:        +{stats.get('cash_flows_added', 0)}")
    print(f"  Stock Prices:      +{stats.get('prices_added', 0)}")
    print(f"  API Calls:         {stats.get('api_calls', 0)}")

    errors = stats.get("errors", [])
    if errors:
        print(f"  Errors: {len(errors)}")
        for error in errors:
            print(f"    - {error}")


def print_bulk_summary(results: List[Dict]):
    """Print summary for bulk ingestion."""
    print("\n" + "="*60)
    print("BULK INGESTION SUMMARY")
    print("="*60)

    total_income = sum(r.get("income_statements_added", 0) for r in results)
    total_balance = sum(r.get("balance_sheets_added", 0) for r in results)
    total_cashflow = sum(r.get("cash_flows_added", 0) for r in results)
    total_prices = sum(r.get("prices_added", 0) for r in results)
    total_api_calls = sum(r.get("api_calls", 0) for r in results)
    total_errors = sum(len(r.get("errors", [])) for r in results)

    print(f"Tickers Processed:   {len(results)}")
    print(f"Total Income Stmts:  +{total_income}")
    print(f"Total Balance Sheets: +{total_balance}")
    print(f"Total Cash Flows:    +{total_cashflow}")
    print(f"Total Stock Prices:  +{total_prices}")
    print(f"Total API Calls:     {total_api_calls}")

    if total_errors > 0:
        print(f"\nErrors: {total_errors}")
        for result in results:
            errors = result.get("errors", [])
            if errors:
                print(f"  {result.get('ticker', 'Unknown')}:")
                for error in errors:
                    print(f"    - {error}")

    # List successful tickers
    successful = [r["ticker"] for r in results if not r.get("errors")]
    failed = [r["ticker"] for r in results if r.get("errors")]

    print(f"\nSuccessful: {len(successful)} tickers")
    if failed:
        print(f"Failed: {', '.join(failed)}")


async def main():
    """Main entry point."""
    args = parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
        # Reduce noise from httpx
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Parse tickers
    tickers = [t.strip().upper() for t in args.ticker.split(",")]

    # Validate tickers
    for ticker in tickers:
        is_valid, error_msg = TickerResolver.validate_ticker(ticker, args.market)
        if not is_valid:
            logger.error(f"Invalid ticker: {error_msg}")
            sys.exit(1)

    include_prices = not args.no_prices

    print(f"\nValueInvestAI Data Ingestion")
    print(f"{'='*40}")
    print(f"Tickers:  {', '.join(tickers)}")
    print(f"Market:   {args.market}")
    print(f"Provider: {args.provider}")
    print(f"Years:    {args.years}")
    print(f"Prices:   {'Yes' if include_prices else 'No'}")
    print(f"Force:    {'Yes' if args.force else 'No'}")
    print(f"{'='*40}\n")

    try:
        if len(tickers) == 1 and not args.bulk:
            # Single ticker mode
            stats = await ingest_single_ticker(
                ticker=tickers[0],
                market=args.market,
                years=args.years,
                include_prices=include_prices,
                force_refresh=args.force,
                provider_name=args.provider,
            )
            print_ticker_summary(stats)

            if stats.get("errors"):
                sys.exit(1)

        else:
            # Bulk mode
            results = await ingest_multiple_tickers(
                tickers=tickers,
                market=args.market,
                years=args.years,
                include_prices=include_prices,
                force_refresh=args.force,
                delay=args.delay,
                provider_name=args.provider,
            )
            print_bulk_summary(results)

            # Exit with error if any ticker failed
            if any(r.get("errors") for r in results):
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nIngestion cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal error during ingestion: {e}")
        sys.exit(1)

    print("\nIngestion complete!")


if __name__ == "__main__":
    asyncio.run(main())
