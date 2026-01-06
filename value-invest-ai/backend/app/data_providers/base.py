"""
Abstract Data Provider Base Class.

Defines the interface for all financial data providers.
Implementations must normalize data to our internal schema.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional, List


@dataclass
class CompanyProfileData:
    """Normalized company profile data."""
    ticker: str
    name: str
    market: str  # 'US' or 'SET'
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"  # 'USD' or 'THB'
    description: Optional[str] = None
    exchange: Optional[str] = None
    country: Optional[str] = None


@dataclass
class IncomeStatementData:
    """Normalized income statement data."""
    fiscal_year: int
    fiscal_period: str = "FY"  # "FY", "Q1", "Q2", "Q3", "Q4"

    # Revenue metrics
    revenue: Optional[Decimal] = None
    cost_of_revenue: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None

    # Operating metrics
    operating_expenses: Optional[Decimal] = None
    operating_income: Optional[Decimal] = None

    # Bottom line
    interest_expense: Optional[Decimal] = None
    pretax_income: Optional[Decimal] = None
    income_tax: Optional[Decimal] = None
    net_income: Optional[Decimal] = None

    # Per share
    eps_basic: Optional[Decimal] = None
    eps_diluted: Optional[Decimal] = None
    shares_outstanding: Optional[int] = None

    # Metadata
    is_estimated: bool = False
    data_source: str = ""


@dataclass
class BalanceSheetData:
    """Normalized balance sheet data."""
    fiscal_year: int
    fiscal_period: str = "FY"

    # Assets
    cash_and_equivalents: Optional[Decimal] = None
    short_term_investments: Optional[Decimal] = None
    accounts_receivable: Optional[Decimal] = None
    inventory: Optional[Decimal] = None
    total_current_assets: Optional[Decimal] = None
    property_plant_equipment: Optional[Decimal] = None
    goodwill: Optional[Decimal] = None
    intangible_assets: Optional[Decimal] = None
    total_assets: Optional[Decimal] = None

    # Liabilities
    accounts_payable: Optional[Decimal] = None
    short_term_debt: Optional[Decimal] = None
    total_current_liabilities: Optional[Decimal] = None
    long_term_debt: Optional[Decimal] = None
    total_liabilities: Optional[Decimal] = None

    # Equity
    retained_earnings: Optional[Decimal] = None
    total_equity: Optional[Decimal] = None

    # Metadata
    data_source: str = ""


@dataclass
class CashFlowData:
    """Normalized cash flow statement data."""
    fiscal_year: int
    fiscal_period: str = "FY"

    # Operating activities
    net_income: Optional[Decimal] = None
    depreciation_amortization: Optional[Decimal] = None
    stock_based_compensation: Optional[Decimal] = None
    operating_cash_flow: Optional[Decimal] = None

    # Investing activities
    capital_expenditure: Optional[Decimal] = None
    acquisitions: Optional[Decimal] = None
    investing_cash_flow: Optional[Decimal] = None

    # Financing activities
    debt_repayment: Optional[Decimal] = None
    dividends_paid: Optional[Decimal] = None
    share_repurchases: Optional[Decimal] = None
    financing_cash_flow: Optional[Decimal] = None

    # Derived
    free_cash_flow: Optional[Decimal] = None

    # Metadata
    data_source: str = ""


@dataclass
class StockPriceData:
    """Normalized daily stock price data."""
    price_date: date
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None


class AbstractDataProvider(ABC):
    """
    Abstract base class for all financial data providers.

    All implementations must normalize API responses to our internal
    data structures defined in this module.

    Supported providers:
    - FMP (Financial Modeling Prep)
    - EOD (EOD Historical Data)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name for logging."""
        pass

    @abstractmethod
    async def get_company_profile(self, ticker: str) -> Optional[CompanyProfileData]:
        """
        Fetch company profile/overview.

        Args:
            ticker: Stock ticker in provider format

        Returns:
            CompanyProfileData or None if not found
        """
        pass

    @abstractmethod
    async def get_income_statements(
        self,
        ticker: str,
        years: int = 30,
        period: str = "annual"
    ) -> List[IncomeStatementData]:
        """
        Fetch income statement history.

        Args:
            ticker: Stock ticker in provider format
            years: Number of years of history to fetch
            period: "annual" or "quarterly"

        Returns:
            List of IncomeStatementData, sorted by fiscal_year descending
        """
        pass

    @abstractmethod
    async def get_balance_sheets(
        self,
        ticker: str,
        years: int = 30,
        period: str = "annual"
    ) -> List[BalanceSheetData]:
        """
        Fetch balance sheet history.

        Args:
            ticker: Stock ticker in provider format
            years: Number of years of history to fetch
            period: "annual" or "quarterly"

        Returns:
            List of BalanceSheetData, sorted by fiscal_year descending
        """
        pass

    @abstractmethod
    async def get_cash_flow_statements(
        self,
        ticker: str,
        years: int = 30,
        period: str = "annual"
    ) -> List[CashFlowData]:
        """
        Fetch cash flow statement history.

        Args:
            ticker: Stock ticker in provider format
            years: Number of years of history to fetch
            period: "annual" or "quarterly"

        Returns:
            List of CashFlowData, sorted by fiscal_year descending
        """
        pass

    @abstractmethod
    async def get_stock_prices(
        self,
        ticker: str,
        start_date: date,
        end_date: date
    ) -> List[StockPriceData]:
        """
        Fetch historical stock prices.

        Args:
            ticker: Stock ticker in provider format
            start_date: Start date for price history
            end_date: End date for price history

        Returns:
            List of StockPriceData, sorted by date descending
        """
        pass

    @abstractmethod
    def normalize_ticker(self, ticker: str, market: str) -> str:
        """
        Convert internal ticker format to provider-specific format.

        Args:
            ticker: Base ticker symbol (e.g., "AAPL", "PTT")
            market: Market identifier ("US" or "SET")

        Returns:
            Provider-specific ticker format
        """
        pass
