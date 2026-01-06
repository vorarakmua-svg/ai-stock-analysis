"""
Financial Modeling Prep (FMP) Data Provider.

Implements the AbstractDataProvider interface for the FMP API.
API Documentation: https://site.financialmodelingprep.com/developer/docs

Supports:
- US stocks (NYSE, NASDAQ)
- Thai stocks (SET) via .BK suffix
- 30+ years of historical financial data
"""

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Any, Dict

import httpx

from app.data_providers.base import (
    AbstractDataProvider,
    CompanyProfileData,
    IncomeStatementData,
    BalanceSheetData,
    CashFlowData,
    StockPriceData,
)

logger = logging.getLogger(__name__)


def safe_decimal(value: Any) -> Optional[Decimal]:
    """Safely convert a value to Decimal, handling None and invalid values."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return None


def safe_int(value: Any) -> Optional[int]:
    """Safely convert a value to int, handling None and invalid values."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


class FMPDataProvider(AbstractDataProvider):
    """
    Financial Modeling Prep data provider.

    API Features:
    - Free tier: 250 requests/day
    - Supports annual and quarterly financial statements
    - Historical data going back 30+ years for major companies
    - Thai stocks available with .BK suffix

    Rate Limiting:
    - Free tier: 5 requests/second
    - Add delays between requests to avoid hitting limits
    """

    BASE_URL = "https://financialmodelingprep.com/api/v3"
    REQUEST_DELAY = 0.3  # 300ms between requests to stay under rate limit

    def __init__(self, api_key: str):
        """
        Initialize FMP provider.

        Args:
            api_key: FMP API key
        """
        self.api_key = api_key
        self._last_request_time: float = 0

    @property
    def provider_name(self) -> str:
        return "FMP"

    async def _rate_limit(self):
        """Apply rate limiting between requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            await asyncio.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _fetch(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make an API request to FMP.

        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters

        Returns:
            JSON response data

        Raises:
            httpx.HTTPError: On network errors
        """
        await self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        query_params = {"apikey": self.api_key}
        if params:
            query_params.update(params)

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug(f"FMP Request: {url}")
            response = await client.get(url, params=query_params)
            response.raise_for_status()
            data = response.json()

            # FMP returns error messages in the response body
            if isinstance(data, dict) and "Error Message" in data:
                logger.error(f"FMP API Error: {data['Error Message']}")
                return None

            return data

    def normalize_ticker(self, ticker: str, market: str) -> str:
        """
        Convert to FMP ticker format.

        FMP Format:
        - US stocks: AAPL, MSFT (no suffix)
        - Thai stocks: PTT.BK, CPALL.BK (.BK suffix)

        Args:
            ticker: Base ticker symbol
            market: 'US' or 'SET'

        Returns:
            FMP-formatted ticker
        """
        ticker = ticker.upper().strip()

        # Remove any existing suffix
        if ticker.endswith(".BK"):
            base_ticker = ticker[:-3]
        elif ticker.endswith(".US"):
            base_ticker = ticker[:-3]
        else:
            base_ticker = ticker

        # Apply market-specific suffix
        if market == "SET":
            return f"{base_ticker}.BK"
        return base_ticker

    async def get_company_profile(self, ticker: str) -> Optional[CompanyProfileData]:
        """Fetch company profile from FMP."""
        try:
            data = await self._fetch(f"profile/{ticker}")
            if not data or len(data) == 0:
                logger.warning(f"No profile data found for {ticker}")
                return None

            profile = data[0]

            # Determine market from ticker and exchange
            exchange = profile.get("exchange", "")
            if ticker.endswith(".BK") or "SET" in exchange.upper():
                market = "SET"
                currency = "THB"
            else:
                market = "US"
                currency = profile.get("currency", "USD")

            return CompanyProfileData(
                ticker=ticker,
                name=profile.get("companyName", ""),
                market=market,
                sector=profile.get("sector"),
                industry=profile.get("industry"),
                currency=currency,
                description=profile.get("description"),
                exchange=exchange,
                country=profile.get("country"),
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching profile for {ticker}: {e}")
            return None

    async def get_income_statements(
        self,
        ticker: str,
        years: int = 30,
        period: str = "annual"
    ) -> List[IncomeStatementData]:
        """
        Fetch income statement history from FMP.

        FMP provides up to 30+ years of annual data for major companies.
        Uses the `limit` parameter to control the number of results.
        """
        try:
            endpoint = f"income-statement/{ticker}"
            params = {"period": period, "limit": years}
            data = await self._fetch(endpoint, params)

            if not data:
                return []

            statements = []
            for item in data:
                # Extract fiscal year from filing date or calendar year
                fiscal_year = None
                if "calendarYear" in item and item["calendarYear"]:
                    fiscal_year = int(item["calendarYear"])
                elif "date" in item and item["date"]:
                    fiscal_year = int(item["date"][:4])

                if not fiscal_year:
                    continue

                # Determine fiscal period
                fiscal_period = "FY"
                if period == "quarter" and "period" in item:
                    fiscal_period = item["period"]  # Q1, Q2, Q3, Q4

                stmt = IncomeStatementData(
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    revenue=safe_decimal(item.get("revenue")),
                    cost_of_revenue=safe_decimal(item.get("costOfRevenue")),
                    gross_profit=safe_decimal(item.get("grossProfit")),
                    operating_expenses=safe_decimal(item.get("operatingExpenses")),
                    operating_income=safe_decimal(item.get("operatingIncome")),
                    interest_expense=safe_decimal(item.get("interestExpense")),
                    pretax_income=safe_decimal(item.get("incomeBeforeTax")),
                    income_tax=safe_decimal(item.get("incomeTaxExpense")),
                    net_income=safe_decimal(item.get("netIncome")),
                    eps_basic=safe_decimal(item.get("eps")),
                    eps_diluted=safe_decimal(item.get("epsdiluted")),
                    shares_outstanding=safe_int(
                        item.get("weightedAverageShsOut") or
                        item.get("weightedAverageShsOutDil")
                    ),
                    is_estimated=False,
                    data_source="FMP",
                )
                statements.append(stmt)

            # Sort by fiscal year descending
            statements.sort(key=lambda x: (x.fiscal_year, x.fiscal_period), reverse=True)
            return statements

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching income statements for {ticker}: {e}")
            return []

    async def get_balance_sheets(
        self,
        ticker: str,
        years: int = 30,
        period: str = "annual"
    ) -> List[BalanceSheetData]:
        """Fetch balance sheet history from FMP."""
        try:
            endpoint = f"balance-sheet-statement/{ticker}"
            params = {"period": period, "limit": years}
            data = await self._fetch(endpoint, params)

            if not data:
                return []

            sheets = []
            for item in data:
                fiscal_year = None
                if "calendarYear" in item and item["calendarYear"]:
                    fiscal_year = int(item["calendarYear"])
                elif "date" in item and item["date"]:
                    fiscal_year = int(item["date"][:4])

                if not fiscal_year:
                    continue

                fiscal_period = "FY"
                if period == "quarter" and "period" in item:
                    fiscal_period = item["period"]

                sheet = BalanceSheetData(
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    cash_and_equivalents=safe_decimal(item.get("cashAndCashEquivalents")),
                    short_term_investments=safe_decimal(item.get("shortTermInvestments")),
                    accounts_receivable=safe_decimal(item.get("netReceivables")),
                    inventory=safe_decimal(item.get("inventory")),
                    total_current_assets=safe_decimal(item.get("totalCurrentAssets")),
                    property_plant_equipment=safe_decimal(item.get("propertyPlantEquipmentNet")),
                    goodwill=safe_decimal(item.get("goodwill")),
                    intangible_assets=safe_decimal(item.get("intangibleAssets")),
                    total_assets=safe_decimal(item.get("totalAssets")),
                    accounts_payable=safe_decimal(item.get("accountPayables")),
                    short_term_debt=safe_decimal(item.get("shortTermDebt")),
                    total_current_liabilities=safe_decimal(item.get("totalCurrentLiabilities")),
                    long_term_debt=safe_decimal(item.get("longTermDebt")),
                    total_liabilities=safe_decimal(item.get("totalLiabilities")),
                    retained_earnings=safe_decimal(item.get("retainedEarnings")),
                    total_equity=safe_decimal(item.get("totalStockholdersEquity")),
                    data_source="FMP",
                )
                sheets.append(sheet)

            sheets.sort(key=lambda x: (x.fiscal_year, x.fiscal_period), reverse=True)
            return sheets

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching balance sheets for {ticker}: {e}")
            return []

    async def get_cash_flow_statements(
        self,
        ticker: str,
        years: int = 30,
        period: str = "annual"
    ) -> List[CashFlowData]:
        """Fetch cash flow statement history from FMP."""
        try:
            endpoint = f"cash-flow-statement/{ticker}"
            params = {"period": period, "limit": years}
            data = await self._fetch(endpoint, params)

            if not data:
                return []

            statements = []
            for item in data:
                fiscal_year = None
                if "calendarYear" in item and item["calendarYear"]:
                    fiscal_year = int(item["calendarYear"])
                elif "date" in item and item["date"]:
                    fiscal_year = int(item["date"][:4])

                if not fiscal_year:
                    continue

                fiscal_period = "FY"
                if period == "quarter" and "period" in item:
                    fiscal_period = item["period"]

                # Calculate free cash flow if not provided
                ocf = safe_decimal(item.get("operatingCashFlow")) or Decimal(0)
                capex = safe_decimal(item.get("capitalExpenditure")) or Decimal(0)
                fcf = safe_decimal(item.get("freeCashFlow"))
                if fcf is None and ocf and capex:
                    # CapEx is typically negative, so we add it
                    fcf = ocf + capex if capex < 0 else ocf - capex

                stmt = CashFlowData(
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    net_income=safe_decimal(item.get("netIncome")),
                    depreciation_amortization=safe_decimal(item.get("depreciationAndAmortization")),
                    stock_based_compensation=safe_decimal(item.get("stockBasedCompensation")),
                    operating_cash_flow=safe_decimal(item.get("operatingCashFlow")),
                    capital_expenditure=safe_decimal(item.get("capitalExpenditure")),
                    acquisitions=safe_decimal(item.get("acquisitionsNet")),
                    investing_cash_flow=safe_decimal(item.get("netCashUsedForInvestingActivites")),
                    debt_repayment=safe_decimal(item.get("debtRepayment")),
                    dividends_paid=safe_decimal(item.get("dividendsPaid")),
                    share_repurchases=safe_decimal(item.get("commonStockRepurchased")),
                    financing_cash_flow=safe_decimal(item.get("netCashUsedProvidedByFinancingActivities")),
                    free_cash_flow=fcf,
                    data_source="FMP",
                )
                statements.append(stmt)

            statements.sort(key=lambda x: (x.fiscal_year, x.fiscal_period), reverse=True)
            return statements

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching cash flow statements for {ticker}: {e}")
            return []

    async def get_stock_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> List[StockPriceData]:
        """
        Fetch historical stock prices from FMP.

        Uses the historical-price-full endpoint for complete history.
        """
        try:
            endpoint = f"historical-price-full/{ticker}"
            params = {
                "from": start_date.isoformat(),
                "to": end_date.isoformat(),
            }
            data = await self._fetch(endpoint, params)

            if not data or "historical" not in data:
                return []

            prices = []
            for item in data["historical"]:
                try:
                    price_date = datetime.strptime(item["date"], "%Y-%m-%d").date()
                except (ValueError, KeyError):
                    continue

                price = StockPriceData(
                    price_date=price_date,
                    open_price=safe_decimal(item.get("open")),
                    high_price=safe_decimal(item.get("high")),
                    low_price=safe_decimal(item.get("low")),
                    close_price=safe_decimal(item.get("close")),
                    adjusted_close=safe_decimal(item.get("adjClose")),
                    volume=safe_int(item.get("volume")),
                )
                prices.append(price)

            # Sort by date descending
            prices.sort(key=lambda x: x.price_date, reverse=True)
            return prices

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching stock prices for {ticker}: {e}")
            return []

    async def get_all_financials(
        self,
        ticker: str,
        years: int = 30
    ) -> Dict[str, List]:
        """
        Convenience method to fetch all financial statements at once.

        Returns:
            Dict with keys: 'income', 'balance', 'cashflow'
        """
        # Fetch all three statement types concurrently
        income_task = self.get_income_statements(ticker, years)
        balance_task = self.get_balance_sheets(ticker, years)
        cashflow_task = self.get_cash_flow_statements(ticker, years)

        income, balance, cashflow = await asyncio.gather(
            income_task, balance_task, cashflow_task
        )

        return {
            "income": income,
            "balance": balance,
            "cashflow": cashflow,
        }
