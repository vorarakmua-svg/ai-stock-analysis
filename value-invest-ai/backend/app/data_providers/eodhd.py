"""
EOD Historical Data Provider.

Implements the AbstractDataProvider interface for the EOD Historical Data API.
API Documentation: https://eodhistoricaldata.com/financial-apis/

Supports:
- US stocks (NYSE, NASDAQ, AMEX)
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


class EODDataProvider(AbstractDataProvider):
    """
    EOD Historical Data provider.

    API Features:
    - Generous free tier with 20 API calls/day
    - Supports fundamental data with annual and quarterly periods
    - Historical data going back 30+ years
    - Thai stocks available with .BK suffix
    - Requires .US suffix for US stocks

    Rate Limiting:
    - Free tier: Limited calls per day
    - Add delays between requests to be safe
    """

    BASE_URL = "https://eodhistoricaldata.com/api"
    REQUEST_DELAY = 0.5  # 500ms between requests

    def __init__(self, api_key: str):
        """
        Initialize EOD provider.

        Args:
            api_key: EOD Historical Data API key
        """
        self.api_key = api_key.strip()  # Remove any whitespace
        self._last_request_time: float = 0

    @property
    def provider_name(self) -> str:
        return "EOD"

    async def _rate_limit(self):
        """Apply rate limiting between requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            await asyncio.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _fetch(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make an API request to EOD.

        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters

        Returns:
            JSON response data
        """
        await self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        query_params = {"api_token": self.api_key, "fmt": "json"}
        if params:
            query_params.update(params)

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug(f"EOD Request: {url}")
            response = await client.get(url, params=query_params)
            response.raise_for_status()
            return response.json()

    def normalize_ticker(self, ticker: str, market: str) -> str:
        """
        Convert to EOD ticker format.

        EOD Format:
        - US stocks: AAPL.US, MSFT.US (.US suffix required)
        - Thai stocks: PTT.BK, CPALL.BK (.BK suffix)

        Args:
            ticker: Base ticker symbol
            market: 'US' or 'SET'

        Returns:
            EOD-formatted ticker
        """
        ticker = ticker.upper().strip()

        # Remove any existing suffix
        for suffix in [".BK", ".US", ".NYSE", ".NASDAQ"]:
            if ticker.endswith(suffix):
                ticker = ticker[:-len(suffix)]
                break

        # Apply market-specific suffix
        if market == "SET":
            return f"{ticker}.BK"
        return f"{ticker}.US"

    async def get_company_profile(self, ticker: str) -> Optional[CompanyProfileData]:
        """Fetch company profile from EOD fundamentals endpoint."""
        try:
            # EOD requires the full ticker including exchange suffix
            data = await self._fetch(f"fundamentals/{ticker}", {"filter": "General"})

            if not data or "General" not in data:
                logger.warning(f"No profile data found for {ticker}")
                return None

            general = data.get("General", {})

            # Determine market from ticker suffix
            if ticker.endswith(".BK"):
                market = "SET"
                currency = "THB"
            else:
                market = "US"
                currency = general.get("CurrencyCode", "USD")

            # Clean up ticker for internal storage
            internal_ticker = ticker.replace(".US", "")

            return CompanyProfileData(
                ticker=internal_ticker,
                name=general.get("Name", ""),
                market=market,
                sector=general.get("Sector"),
                industry=general.get("Industry"),
                currency=currency,
                description=general.get("Description"),
                exchange=general.get("Exchange"),
                country=general.get("CountryName"),
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
        Fetch income statement history from EOD.

        EOD provides fundamentals via a single endpoint with all statements.
        """
        try:
            # Fetch fundamentals with financials filter
            data = await self._fetch(
                f"fundamentals/{ticker}",
                {"filter": "Financials::Income_Statement::yearly" if period == "annual" else "Financials::Income_Statement::quarterly"}
            )

            if not data:
                return []

            # Navigate to income statement data
            financials = data.get("Financials", {})
            income_data = financials.get("Income_Statement", {})
            period_data = income_data.get("yearly" if period == "annual" else "quarterly", {})

            statements = []
            for date_key, item in period_data.items():
                try:
                    fiscal_year = int(date_key[:4])
                except (ValueError, IndexError):
                    continue

                fiscal_period = "FY" if period == "annual" else self._get_quarter(date_key)

                stmt = IncomeStatementData(
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    revenue=safe_decimal(item.get("totalRevenue")),
                    cost_of_revenue=safe_decimal(item.get("costOfRevenue")),
                    gross_profit=safe_decimal(item.get("grossProfit")),
                    operating_expenses=safe_decimal(item.get("totalOperatingExpenses")),
                    operating_income=safe_decimal(item.get("operatingIncome")),
                    interest_expense=safe_decimal(item.get("interestExpense")),
                    pretax_income=safe_decimal(item.get("incomeBeforeTax")),
                    income_tax=safe_decimal(item.get("incomeTaxExpense")),
                    net_income=safe_decimal(item.get("netIncome")),
                    eps_basic=safe_decimal(item.get("basicEPS")),
                    eps_diluted=safe_decimal(item.get("dilutedEPS")),
                    shares_outstanding=safe_int(item.get("commonStockSharesOutstanding")),
                    is_estimated=False,
                    data_source="EOD",
                )
                statements.append(stmt)

            # Sort by fiscal year descending and limit
            statements.sort(key=lambda x: (x.fiscal_year, x.fiscal_period), reverse=True)
            return statements[:years]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching income statements for {ticker}: {e}")
            return []

    async def get_balance_sheets(
        self,
        ticker: str,
        years: int = 30,
        period: str = "annual"
    ) -> List[BalanceSheetData]:
        """Fetch balance sheet history from EOD."""
        try:
            data = await self._fetch(
                f"fundamentals/{ticker}",
                {"filter": "Financials::Balance_Sheet::yearly" if period == "annual" else "Financials::Balance_Sheet::quarterly"}
            )

            if not data:
                return []

            financials = data.get("Financials", {})
            balance_data = financials.get("Balance_Sheet", {})
            period_data = balance_data.get("yearly" if period == "annual" else "quarterly", {})

            sheets = []
            for date_key, item in period_data.items():
                try:
                    fiscal_year = int(date_key[:4])
                except (ValueError, IndexError):
                    continue

                fiscal_period = "FY" if period == "annual" else self._get_quarter(date_key)

                sheet = BalanceSheetData(
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    cash_and_equivalents=safe_decimal(item.get("cash")),
                    short_term_investments=safe_decimal(item.get("shortTermInvestments")),
                    accounts_receivable=safe_decimal(item.get("netReceivables")),
                    inventory=safe_decimal(item.get("inventory")),
                    total_current_assets=safe_decimal(item.get("totalCurrentAssets")),
                    property_plant_equipment=safe_decimal(item.get("propertyPlantEquipment")),
                    goodwill=safe_decimal(item.get("goodWill")),
                    intangible_assets=safe_decimal(item.get("intangibleAssets")),
                    total_assets=safe_decimal(item.get("totalAssets")),
                    accounts_payable=safe_decimal(item.get("accountsPayable")),
                    short_term_debt=safe_decimal(item.get("shortTermDebt")),
                    total_current_liabilities=safe_decimal(item.get("totalCurrentLiabilities")),
                    long_term_debt=safe_decimal(item.get("longTermDebt")),
                    total_liabilities=safe_decimal(item.get("totalLiab")),
                    retained_earnings=safe_decimal(item.get("retainedEarnings")),
                    total_equity=safe_decimal(item.get("totalStockholderEquity")),
                    data_source="EOD",
                )
                sheets.append(sheet)

            sheets.sort(key=lambda x: (x.fiscal_year, x.fiscal_period), reverse=True)
            return sheets[:years]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching balance sheets for {ticker}: {e}")
            return []

    async def get_cash_flow_statements(
        self,
        ticker: str,
        years: int = 30,
        period: str = "annual"
    ) -> List[CashFlowData]:
        """Fetch cash flow statement history from EOD."""
        try:
            data = await self._fetch(
                f"fundamentals/{ticker}",
                {"filter": "Financials::Cash_Flow::yearly" if period == "annual" else "Financials::Cash_Flow::quarterly"}
            )

            if not data:
                return []

            financials = data.get("Financials", {})
            cashflow_data = financials.get("Cash_Flow", {})
            period_data = cashflow_data.get("yearly" if period == "annual" else "quarterly", {})

            statements = []
            for date_key, item in period_data.items():
                try:
                    fiscal_year = int(date_key[:4])
                except (ValueError, IndexError):
                    continue

                fiscal_period = "FY" if period == "annual" else self._get_quarter(date_key)

                # Calculate free cash flow
                ocf = safe_decimal(item.get("totalCashFromOperatingActivities")) or Decimal(0)
                capex = safe_decimal(item.get("capitalExpenditures")) or Decimal(0)
                fcf = safe_decimal(item.get("freeCashFlow"))
                if fcf is None and ocf and capex:
                    fcf = ocf + capex  # capex is typically negative

                stmt = CashFlowData(
                    fiscal_year=fiscal_year,
                    fiscal_period=fiscal_period,
                    net_income=safe_decimal(item.get("netIncome")),
                    depreciation_amortization=safe_decimal(item.get("depreciation")),
                    stock_based_compensation=safe_decimal(item.get("stockBasedCompensation")),
                    operating_cash_flow=safe_decimal(item.get("totalCashFromOperatingActivities")),
                    capital_expenditure=safe_decimal(item.get("capitalExpenditures")),
                    acquisitions=safe_decimal(item.get("netAcquisitions")),
                    investing_cash_flow=safe_decimal(item.get("totalCashflowsFromInvestingActivities")),
                    debt_repayment=safe_decimal(item.get("repaymentOfDebt")),
                    dividends_paid=safe_decimal(item.get("dividendsPaid")),
                    share_repurchases=safe_decimal(item.get("salePurchaseOfStock")),
                    financing_cash_flow=safe_decimal(item.get("totalCashFromFinancingActivities")),
                    free_cash_flow=fcf,
                    data_source="EOD",
                )
                statements.append(stmt)

            statements.sort(key=lambda x: (x.fiscal_year, x.fiscal_period), reverse=True)
            return statements[:years]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching cash flow statements for {ticker}: {e}")
            return []

    async def get_stock_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> List[StockPriceData]:
        """Fetch historical stock prices from EOD."""
        try:
            data = await self._fetch(
                f"eod/{ticker}",
                {
                    "from": start_date.isoformat(),
                    "to": end_date.isoformat(),
                    "period": "d",
                }
            )

            if not data or not isinstance(data, list):
                return []

            prices = []
            for item in data:
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
                    adjusted_close=safe_decimal(item.get("adjusted_close")),
                    volume=safe_int(item.get("volume")),
                )
                prices.append(price)

            # Sort by date descending
            prices.sort(key=lambda x: x.price_date, reverse=True)
            return prices

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching stock prices for {ticker}: {e}")
            return []

    def _get_quarter(self, date_str: str) -> str:
        """Extract quarter from date string (YYYY-MM-DD format)."""
        try:
            month = int(date_str[5:7])
            if month <= 3:
                return "Q1"
            elif month <= 6:
                return "Q2"
            elif month <= 9:
                return "Q3"
            else:
                return "Q4"
        except (ValueError, IndexError):
            return "FY"

    async def get_all_financials(
        self,
        ticker: str,
        years: int = 30
    ) -> Dict[str, List]:
        """
        Convenience method to fetch all financial statements at once.

        For EOD, this can be optimized by fetching full fundamentals in one call.
        """
        # Fetch all at once to minimize API calls
        try:
            data = await self._fetch(f"fundamentals/{ticker}")

            if not data:
                return {"income": [], "balance": [], "cashflow": []}

            # Process income statements
            income = await self._process_income_from_data(data, years)

            # Process balance sheets
            balance = await self._process_balance_from_data(data, years)

            # Process cash flows
            cashflow = await self._process_cashflow_from_data(data, years)

            return {
                "income": income,
                "balance": balance,
                "cashflow": cashflow,
            }

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching all financials for {ticker}: {e}")
            return {"income": [], "balance": [], "cashflow": []}

    async def _process_income_from_data(self, data: Dict, years: int) -> List[IncomeStatementData]:
        """Process income statements from full fundamentals data."""
        # Similar to get_income_statements but without API call
        financials = data.get("Financials", {})
        income_data = financials.get("Income_Statement", {})
        period_data = income_data.get("yearly", {})

        statements = []
        for date_key, item in period_data.items():
            try:
                fiscal_year = int(date_key[:4])
            except (ValueError, IndexError):
                continue

            stmt = IncomeStatementData(
                fiscal_year=fiscal_year,
                fiscal_period="FY",
                revenue=safe_decimal(item.get("totalRevenue")),
                cost_of_revenue=safe_decimal(item.get("costOfRevenue")),
                gross_profit=safe_decimal(item.get("grossProfit")),
                operating_expenses=safe_decimal(item.get("totalOperatingExpenses")),
                operating_income=safe_decimal(item.get("operatingIncome")),
                interest_expense=safe_decimal(item.get("interestExpense")),
                pretax_income=safe_decimal(item.get("incomeBeforeTax")),
                income_tax=safe_decimal(item.get("incomeTaxExpense")),
                net_income=safe_decimal(item.get("netIncome")),
                eps_basic=safe_decimal(item.get("basicEPS")),
                eps_diluted=safe_decimal(item.get("dilutedEPS")),
                shares_outstanding=safe_int(item.get("commonStockSharesOutstanding")),
                is_estimated=False,
                data_source="EOD",
            )
            statements.append(stmt)

        statements.sort(key=lambda x: x.fiscal_year, reverse=True)
        return statements[:years]

    async def _process_balance_from_data(self, data: Dict, years: int) -> List[BalanceSheetData]:
        """Process balance sheets from full fundamentals data."""
        financials = data.get("Financials", {})
        balance_data = financials.get("Balance_Sheet", {})
        period_data = balance_data.get("yearly", {})

        sheets = []
        for date_key, item in period_data.items():
            try:
                fiscal_year = int(date_key[:4])
            except (ValueError, IndexError):
                continue

            sheet = BalanceSheetData(
                fiscal_year=fiscal_year,
                fiscal_period="FY",
                cash_and_equivalents=safe_decimal(item.get("cash")),
                short_term_investments=safe_decimal(item.get("shortTermInvestments")),
                accounts_receivable=safe_decimal(item.get("netReceivables")),
                inventory=safe_decimal(item.get("inventory")),
                total_current_assets=safe_decimal(item.get("totalCurrentAssets")),
                property_plant_equipment=safe_decimal(item.get("propertyPlantEquipment")),
                goodwill=safe_decimal(item.get("goodWill")),
                intangible_assets=safe_decimal(item.get("intangibleAssets")),
                total_assets=safe_decimal(item.get("totalAssets")),
                accounts_payable=safe_decimal(item.get("accountsPayable")),
                short_term_debt=safe_decimal(item.get("shortTermDebt")),
                total_current_liabilities=safe_decimal(item.get("totalCurrentLiabilities")),
                long_term_debt=safe_decimal(item.get("longTermDebt")),
                total_liabilities=safe_decimal(item.get("totalLiab")),
                retained_earnings=safe_decimal(item.get("retainedEarnings")),
                total_equity=safe_decimal(item.get("totalStockholderEquity")),
                data_source="EOD",
            )
            sheets.append(sheet)

        sheets.sort(key=lambda x: x.fiscal_year, reverse=True)
        return sheets[:years]

    async def _process_cashflow_from_data(self, data: Dict, years: int) -> List[CashFlowData]:
        """Process cash flows from full fundamentals data."""
        financials = data.get("Financials", {})
        cashflow_data = financials.get("Cash_Flow", {})
        period_data = cashflow_data.get("yearly", {})

        statements = []
        for date_key, item in period_data.items():
            try:
                fiscal_year = int(date_key[:4])
            except (ValueError, IndexError):
                continue

            ocf = safe_decimal(item.get("totalCashFromOperatingActivities")) or Decimal(0)
            capex = safe_decimal(item.get("capitalExpenditures")) or Decimal(0)
            fcf = safe_decimal(item.get("freeCashFlow"))
            if fcf is None and ocf and capex:
                fcf = ocf + capex

            stmt = CashFlowData(
                fiscal_year=fiscal_year,
                fiscal_period="FY",
                net_income=safe_decimal(item.get("netIncome")),
                depreciation_amortization=safe_decimal(item.get("depreciation")),
                stock_based_compensation=safe_decimal(item.get("stockBasedCompensation")),
                operating_cash_flow=safe_decimal(item.get("totalCashFromOperatingActivities")),
                capital_expenditure=safe_decimal(item.get("capitalExpenditures")),
                acquisitions=safe_decimal(item.get("netAcquisitions")),
                investing_cash_flow=safe_decimal(item.get("totalCashflowsFromInvestingActivities")),
                debt_repayment=safe_decimal(item.get("repaymentOfDebt")),
                dividends_paid=safe_decimal(item.get("dividendsPaid")),
                share_repurchases=safe_decimal(item.get("salePurchaseOfStock")),
                financing_cash_flow=safe_decimal(item.get("totalCashFromFinancingActivities")),
                free_cash_flow=fcf,
                data_source="EOD",
            )
            statements.append(stmt)

        statements.sort(key=lambda x: x.fiscal_year, reverse=True)
        return statements[:years]
