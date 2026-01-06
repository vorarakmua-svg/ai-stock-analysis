"""
Data Ingestion Service.

Implements the "Fetch-Once-Store-Forever" pattern:
- Check database first before making API calls
- Historical data (>1 year old) is never re-fetched
- Current year data can be refreshed
- Tracks all API calls for cost monitoring

Usage:
    service = IngestionService(db_session, data_provider)
    await service.ingest_ticker("AAPL", "US")
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Set, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.data_providers.base import (
    AbstractDataProvider,
    CompanyProfileData,
    IncomeStatementData,
    BalanceSheetData,
    CashFlowData,
    StockPriceData,
)
from app.models import (
    Company,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    StockPrice,
    DataFetchLog,
)
from app.services.ticker_resolver import TickerResolver

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for ingesting financial data from external providers.

    Implements the "Fetch-Once-Store-Forever" caching strategy:
    - Historical fiscal years are fetched once and never updated
    - Only current/recent year data may be refreshed
    - All API calls are logged for cost tracking
    """

    def __init__(
        self,
        db: AsyncSession,
        provider: AbstractDataProvider,
    ):
        """
        Initialize the ingestion service.

        Args:
            db: SQLAlchemy async database session
            provider: Data provider implementation (FMP, EOD, etc.)
        """
        self.db = db
        self.provider = provider

    async def ingest_ticker(
        self,
        ticker: str,
        market: str,
        years: int = 30,
        include_prices: bool = True,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingest all financial data for a single ticker.

        This is the main entry point for data ingestion. It will:
        1. Create or update company profile
        2. Fetch and store income statements
        3. Fetch and store balance sheets
        4. Fetch and store cash flow statements
        5. Optionally fetch stock price history

        Args:
            ticker: Base ticker symbol (e.g., "AAPL", "PTT")
            market: Market identifier ("US" or "SET")
            years: Number of years of history to fetch
            include_prices: Whether to fetch stock prices
            force_refresh: If True, re-fetch all data regardless of cache

        Returns:
            Dict with ingestion statistics
        """
        stats = {
            "ticker": ticker,
            "market": market,
            "company_created": False,
            "income_statements_added": 0,
            "balance_sheets_added": 0,
            "cash_flows_added": 0,
            "prices_added": 0,
            "api_calls": 0,
            "errors": [],
        }

        try:
            # Resolve ticker to provider format
            ticker_info = TickerResolver.resolve(ticker, market)
            provider_ticker = TickerResolver.to_provider_format(
                ticker_info.base_ticker,
                self.provider.provider_name.lower(),
                market
            )

            logger.info(f"Starting ingestion for {ticker_info.internal_ticker} ({provider_ticker})")

            # Step 1: Get or create company
            company = await self._ensure_company(provider_ticker, ticker_info, stats)
            if not company:
                stats["errors"].append("Failed to create/fetch company profile")
                return stats

            # Step 2: Get existing fiscal years to avoid re-fetching
            existing_years = await self._get_existing_fiscal_years(company.id)

            # Step 3: Fetch and store financial statements
            await self._ingest_income_statements(
                company, provider_ticker, years, existing_years, force_refresh, stats
            )
            await self._ingest_balance_sheets(
                company, provider_ticker, years, existing_years, force_refresh, stats
            )
            await self._ingest_cash_flows(
                company, provider_ticker, years, existing_years, force_refresh, stats
            )

            # Step 4: Optionally fetch stock prices
            if include_prices:
                await self._ingest_stock_prices(company, provider_ticker, years, stats)

            # Commit all changes
            await self.db.commit()

            logger.info(
                f"Ingestion complete for {ticker_info.internal_ticker}: "
                f"{stats['income_statements_added']} income statements, "
                f"{stats['balance_sheets_added']} balance sheets, "
                f"{stats['cash_flows_added']} cash flows, "
                f"{stats['prices_added']} prices"
            )

        except Exception as e:
            logger.error(f"Error during ingestion for {ticker}: {e}")
            stats["errors"].append(str(e))
            await self.db.rollback()

        return stats

    async def _ensure_company(
        self,
        provider_ticker: str,
        ticker_info,
        stats: Dict,
    ) -> Optional[Company]:
        """Get existing company or create from API profile."""
        # Check if company exists
        result = await self.db.execute(
            select(Company).where(Company.ticker == ticker_info.internal_ticker)
        )
        company = result.scalar_one_or_none()

        if company:
            logger.debug(f"Found existing company: {company.ticker}")
            return company

        # Fetch profile from provider
        logger.info(f"Fetching company profile for {provider_ticker}")
        profile = await self.provider.get_company_profile(provider_ticker)
        stats["api_calls"] += 1

        if not profile:
            logger.error(f"Could not fetch profile for {provider_ticker}")
            return None

        # Log the API call
        await self._log_fetch(ticker_info.internal_ticker, "profile")

        # Create new company
        company = Company(
            ticker=ticker_info.internal_ticker,
            name=profile.name or ticker_info.base_ticker,
            market=ticker_info.market,
            sector=profile.sector,
            industry=profile.industry,
            currency=ticker_info.currency,
            description=profile.description,
        )
        self.db.add(company)
        await self.db.flush()  # Get the ID

        stats["company_created"] = True
        logger.info(f"Created company: {company.ticker} ({company.name})")

        return company

    async def _get_existing_fiscal_years(self, company_id: int) -> Dict[str, Set[int]]:
        """Get sets of fiscal years already in database for each statement type."""
        existing = {
            "income": set(),
            "balance": set(),
            "cashflow": set(),
        }

        # Income statements
        result = await self.db.execute(
            select(IncomeStatement.fiscal_year)
            .where(IncomeStatement.company_id == company_id)
            .where(IncomeStatement.fiscal_period == "FY")
        )
        existing["income"] = {row[0] for row in result.fetchall()}

        # Balance sheets
        result = await self.db.execute(
            select(BalanceSheet.fiscal_year)
            .where(BalanceSheet.company_id == company_id)
            .where(BalanceSheet.fiscal_period == "FY")
        )
        existing["balance"] = {row[0] for row in result.fetchall()}

        # Cash flows
        result = await self.db.execute(
            select(CashFlowStatement.fiscal_year)
            .where(CashFlowStatement.company_id == company_id)
            .where(CashFlowStatement.fiscal_period == "FY")
        )
        existing["cashflow"] = {row[0] for row in result.fetchall()}

        return existing

    async def _ingest_income_statements(
        self,
        company: Company,
        provider_ticker: str,
        years: int,
        existing_years: Dict[str, Set[int]],
        force_refresh: bool,
        stats: Dict,
    ):
        """Fetch and store income statements."""
        current_year = datetime.now().year
        existing = existing_years["income"]

        # Check what we need to fetch
        if not force_refresh and len(existing) >= years:
            logger.debug(f"Income statements already complete for {company.ticker}")
            return

        logger.info(f"Fetching income statements for {provider_ticker}")
        statements = await self.provider.get_income_statements(provider_ticker, years)
        stats["api_calls"] += 1
        await self._log_fetch(company.ticker, "income_statement")

        added = 0
        for stmt in statements:
            # Skip if we already have this year (unless force refresh)
            if not force_refresh and stmt.fiscal_year in existing:
                # Allow refresh of current year data
                if stmt.fiscal_year < current_year - 1:
                    continue

            income = IncomeStatement(
                company_id=company.id,
                fiscal_year=stmt.fiscal_year,
                fiscal_period=stmt.fiscal_period,
                revenue=stmt.revenue,
                cost_of_revenue=stmt.cost_of_revenue,
                gross_profit=stmt.gross_profit,
                operating_expenses=stmt.operating_expenses,
                operating_income=stmt.operating_income,
                interest_expense=stmt.interest_expense,
                pretax_income=stmt.pretax_income,
                income_tax=stmt.income_tax,
                net_income=stmt.net_income,
                eps_basic=stmt.eps_basic,
                eps_diluted=stmt.eps_diluted,
                shares_outstanding=stmt.shares_outstanding,
                is_estimated=stmt.is_estimated,
                data_source=stmt.data_source,
                fetched_at=datetime.utcnow(),
            )

            # Use upsert to handle existing records
            await self.db.merge(income)
            added += 1

        stats["income_statements_added"] = added
        logger.info(f"Added {added} income statements for {company.ticker}")

    async def _ingest_balance_sheets(
        self,
        company: Company,
        provider_ticker: str,
        years: int,
        existing_years: Dict[str, Set[int]],
        force_refresh: bool,
        stats: Dict,
    ):
        """Fetch and store balance sheets."""
        current_year = datetime.now().year
        existing = existing_years["balance"]

        if not force_refresh and len(existing) >= years:
            logger.debug(f"Balance sheets already complete for {company.ticker}")
            return

        logger.info(f"Fetching balance sheets for {provider_ticker}")
        sheets = await self.provider.get_balance_sheets(provider_ticker, years)
        stats["api_calls"] += 1
        await self._log_fetch(company.ticker, "balance_sheet")

        added = 0
        for sheet in sheets:
            if not force_refresh and sheet.fiscal_year in existing:
                if sheet.fiscal_year < current_year - 1:
                    continue

            balance = BalanceSheet(
                company_id=company.id,
                fiscal_year=sheet.fiscal_year,
                fiscal_period=sheet.fiscal_period,
                cash_and_equivalents=sheet.cash_and_equivalents,
                short_term_investments=sheet.short_term_investments,
                accounts_receivable=sheet.accounts_receivable,
                inventory=sheet.inventory,
                total_current_assets=sheet.total_current_assets,
                property_plant_equipment=sheet.property_plant_equipment,
                goodwill=sheet.goodwill,
                intangible_assets=sheet.intangible_assets,
                total_assets=sheet.total_assets,
                accounts_payable=sheet.accounts_payable,
                short_term_debt=sheet.short_term_debt,
                total_current_liabilities=sheet.total_current_liabilities,
                long_term_debt=sheet.long_term_debt,
                total_liabilities=sheet.total_liabilities,
                retained_earnings=sheet.retained_earnings,
                total_equity=sheet.total_equity,
                data_source=sheet.data_source,
                fetched_at=datetime.utcnow(),
            )

            await self.db.merge(balance)
            added += 1

        stats["balance_sheets_added"] = added
        logger.info(f"Added {added} balance sheets for {company.ticker}")

    async def _ingest_cash_flows(
        self,
        company: Company,
        provider_ticker: str,
        years: int,
        existing_years: Dict[str, Set[int]],
        force_refresh: bool,
        stats: Dict,
    ):
        """Fetch and store cash flow statements."""
        current_year = datetime.now().year
        existing = existing_years["cashflow"]

        if not force_refresh and len(existing) >= years:
            logger.debug(f"Cash flows already complete for {company.ticker}")
            return

        logger.info(f"Fetching cash flow statements for {provider_ticker}")
        statements = await self.provider.get_cash_flow_statements(provider_ticker, years)
        stats["api_calls"] += 1
        await self._log_fetch(company.ticker, "cash_flow")

        added = 0
        for stmt in statements:
            if not force_refresh and stmt.fiscal_year in existing:
                if stmt.fiscal_year < current_year - 1:
                    continue

            cashflow = CashFlowStatement(
                company_id=company.id,
                fiscal_year=stmt.fiscal_year,
                fiscal_period=stmt.fiscal_period,
                net_income=stmt.net_income,
                depreciation_amortization=stmt.depreciation_amortization,
                stock_based_compensation=stmt.stock_based_compensation,
                operating_cash_flow=stmt.operating_cash_flow,
                capital_expenditure=stmt.capital_expenditure,
                acquisitions=stmt.acquisitions,
                investing_cash_flow=stmt.investing_cash_flow,
                debt_repayment=stmt.debt_repayment,
                dividends_paid=stmt.dividends_paid,
                share_repurchases=stmt.share_repurchases,
                financing_cash_flow=stmt.financing_cash_flow,
                free_cash_flow=stmt.free_cash_flow,
                data_source=stmt.data_source,
                fetched_at=datetime.utcnow(),
            )

            await self.db.merge(cashflow)
            added += 1

        stats["cash_flows_added"] = added
        logger.info(f"Added {added} cash flow statements for {company.ticker}")

    async def _ingest_stock_prices(
        self,
        company: Company,
        provider_ticker: str,
        years: int,
        stats: Dict,
    ):
        """Fetch and store stock prices."""
        # Get date range for prices
        end_date = date.today()
        start_date = end_date - timedelta(days=365 * years)

        # Check if we already have recent prices
        result = await self.db.execute(
            select(func.max(StockPrice.price_date))
            .where(StockPrice.company_id == company.id)
        )
        latest_price_date = result.scalar_one_or_none()

        if latest_price_date:
            # Only fetch new prices
            start_date = latest_price_date + timedelta(days=1)
            if start_date >= end_date:
                logger.debug(f"Prices already up to date for {company.ticker}")
                return

        logger.info(f"Fetching stock prices for {provider_ticker} from {start_date} to {end_date}")
        prices = await self.provider.get_stock_prices(provider_ticker, start_date, end_date)
        stats["api_calls"] += 1
        await self._log_fetch(company.ticker, "stock_prices")

        added = 0
        for price in prices:
            stock_price = StockPrice(
                company_id=company.id,
                price_date=price.price_date,
                open_price=price.open_price,
                high_price=price.high_price,
                low_price=price.low_price,
                close_price=price.close_price,
                adjusted_close=price.adjusted_close,
                volume=price.volume,
            )

            await self.db.merge(stock_price)
            added += 1

        stats["prices_added"] = added
        logger.info(f"Added {added} price records for {company.ticker}")

    async def _log_fetch(self, ticker: str, endpoint: str):
        """Log API fetch for cost tracking."""
        log = DataFetchLog(
            ticker=ticker,
            provider=self.provider.provider_name,
            endpoint=endpoint,
            fetched_at=datetime.utcnow(),
            was_cached=False,
        )
        self.db.add(log)


async def bulk_ingest(
    db: AsyncSession,
    provider: AbstractDataProvider,
    tickers: List[Dict[str, str]],
    delay_between_tickers: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Ingest multiple tickers with rate limiting.

    Args:
        db: Database session
        provider: Data provider
        tickers: List of dicts with 'ticker' and 'market' keys
        delay_between_tickers: Seconds to wait between each ticker

    Returns:
        List of ingestion stats for each ticker
    """
    service = IngestionService(db, provider)
    results = []

    for i, ticker_info in enumerate(tickers):
        ticker = ticker_info["ticker"]
        market = ticker_info["market"]

        logger.info(f"Processing ticker {i + 1}/{len(tickers)}: {ticker} ({market})")

        stats = await service.ingest_ticker(ticker, market)
        results.append(stats)

        # Rate limiting between tickers
        if i < len(tickers) - 1:
            await asyncio.sleep(delay_between_tickers)

    return results
