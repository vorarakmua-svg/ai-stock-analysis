"""
Company model for ValueInvestAI.

The Company model is the core entity that represents a tracked stock.
It supports both US (NYSE/NASDAQ) and Thai (SET) markets with appropriate
ticker format handling.

Ticker Format Examples:
- US: AAPL, MSFT, GOOGL (1-5 uppercase letters)
- Thai: PTT.BK, SCB.BK, KBANK.BK (letters + .BK suffix)
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import re

from sqlalchemy import Integer, String, DateTime, Index, CheckConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base

if TYPE_CHECKING:
    from app.models.financial import (
        IncomeStatement, BalanceSheet, CashFlowStatement,
        StockPrice, Valuation, AIAnalysis
    )


class Company(Base):
    """
    Companies master table.

    Handles both US (AAPL) and Thai (PTT.BK) ticker formats.
    The market field determines the expected ticker format and currency.

    Attributes:
        id: Primary key
        ticker: Stock ticker symbol (unique, max 20 chars for Thai .BK format)
        name: Full company name
        market: Market identifier ('US' for NYSE/NASDAQ, 'SET' for Thai)
        sector: Business sector (e.g., 'Technology', 'Healthcare')
        industry: Specific industry (e.g., 'Consumer Electronics')
        currency: Trading currency ('USD' for US, 'THB' for Thai)
        description: Optional company description
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="Stock ticker symbol (e.g., AAPL or PTT.BK)"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Full company name"
    )
    market: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Market identifier: 'US' or 'SET'"
    )
    sector: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Business sector"
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Specific industry"
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        doc="Trading currency: 'USD' or 'THB'"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
        doc="Company description"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    income_statements: Mapped[List["IncomeStatement"]] = relationship(
        "IncomeStatement",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    balance_sheets: Mapped[List["BalanceSheet"]] = relationship(
        "BalanceSheet",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    cash_flow_statements: Mapped[List["CashFlowStatement"]] = relationship(
        "CashFlowStatement",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    stock_prices: Mapped[List["StockPrice"]] = relationship(
        "StockPrice",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    valuations: Mapped[List["Valuation"]] = relationship(
        "Valuation",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    ai_analyses: Mapped[List["AIAnalysis"]] = relationship(
        "AIAnalysis",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index('idx_companies_market', 'market'),
        Index('idx_companies_sector', 'sector'),
        Index('idx_companies_market_ticker', 'market', 'ticker'),
        CheckConstraint(
            "market IN ('US', 'SET')",
            name='chk_valid_market'
        ),
        CheckConstraint(
            "currency IN ('USD', 'THB')",
            name='chk_valid_currency'
        ),
    )

    # Ticker validation patterns
    US_TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')
    THAI_TICKER_PATTERN = re.compile(r'^[A-Z0-9]{1,10}\.BK$')

    @validates('ticker')
    def validate_ticker(self, key: str, ticker: str) -> str:
        """
        Validate ticker format based on market.

        US tickers: 1-5 uppercase letters (AAPL, MSFT, GOOGL)
        Thai tickers: Letters/numbers + .BK suffix (PTT.BK, CPALL.BK)
        """
        if not ticker:
            raise ValueError("Ticker cannot be empty")

        ticker = ticker.upper().strip()

        # Determine market from ticker format
        if ticker.endswith('.BK'):
            if not self.THAI_TICKER_PATTERN.match(ticker):
                raise ValueError(
                    f"Invalid Thai ticker format: {ticker}. "
                    "Expected format: SYMBOL.BK (e.g., PTT.BK)"
                )
        else:
            if not self.US_TICKER_PATTERN.match(ticker):
                raise ValueError(
                    f"Invalid US ticker format: {ticker}. "
                    "Expected format: 1-5 uppercase letters (e.g., AAPL)"
                )

        return ticker

    @validates('market')
    def validate_market(self, key: str, market: str) -> str:
        """Validate market is either 'US' or 'SET'."""
        if market not in ('US', 'SET'):
            raise ValueError(f"Invalid market: {market}. Must be 'US' or 'SET'")
        return market

    @validates('currency')
    def validate_currency(self, key: str, currency: str) -> str:
        """Validate currency is either 'USD' or 'THB'."""
        if currency not in ('USD', 'THB'):
            raise ValueError(f"Invalid currency: {currency}. Must be 'USD' or 'THB'")
        return currency

    @property
    def is_us_stock(self) -> bool:
        """Check if this is a US stock."""
        return self.market == 'US'

    @property
    def is_thai_stock(self) -> bool:
        """Check if this is a Thai stock."""
        return self.market == 'SET'

    @property
    def base_ticker(self) -> str:
        """
        Get the base ticker without market suffix.

        Example: PTT.BK -> PTT, AAPL -> AAPL
        """
        if self.ticker.endswith('.BK'):
            return self.ticker[:-3]
        return self.ticker

    @classmethod
    def detect_market_from_ticker(cls, ticker: str) -> str:
        """
        Auto-detect market from ticker format.

        Args:
            ticker: Stock ticker symbol

        Returns:
            'SET' if ticker ends with .BK, 'US' otherwise
        """
        return 'SET' if ticker.upper().endswith('.BK') else 'US'

    @classmethod
    def get_currency_for_market(cls, market: str) -> str:
        """
        Get the default currency for a market.

        Args:
            market: Market identifier ('US' or 'SET')

        Returns:
            'USD' for US, 'THB' for SET
        """
        return 'THB' if market == 'SET' else 'USD'

    def __repr__(self) -> str:
        return (
            f"<Company(id={self.id}, ticker='{self.ticker}', "
            f"name='{self.name}', market='{self.market}', currency='{self.currency}')>"
        )
