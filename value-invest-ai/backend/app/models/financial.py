"""
Financial statement models for ValueInvestAI.

This module contains all financial data models:
- IncomeStatement: Revenue, expenses, and profitability data
- BalanceSheet: Assets, liabilities, and equity data
- CashFlowStatement: Operating, investing, and financing cash flows
- StockPrice: Daily stock price data
- Valuation: Calculated valuation metrics (DCF, Graham, Lynch)
- AIAnalysis: AI-generated investment analysis
- DataFetchLog: API call logging for cost tracking

All models follow the schema defined in PROJECT_BLUEPRINT.md Section 5.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Integer, String, Numeric, BigInteger, Boolean, DateTime, Date,
    ForeignKey, Index, UniqueConstraint, Text
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.company import Company


class IncomeStatement(Base):
    """
    Income Statement data - stores up to 30 years of financial history per company.

    Contains revenue metrics, operating metrics, bottom line results, and per-share data.
    All monetary values use DECIMAL(20,2) for precision in financial calculations.
    """

    __tablename__ = "income_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(
        String(5),
        default="FY",
        doc="FY for annual, Q1-Q4 for quarterly"
    )

    # Revenue metrics
    revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    cost_of_revenue: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    gross_profit: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Operating metrics
    operating_expenses: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    operating_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Bottom line
    interest_expense: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    pretax_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    income_tax: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    net_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Per share
    eps_basic: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    eps_diluted: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    shares_outstanding: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Metadata
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    data_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="income_statements")

    __table_args__ = (
        UniqueConstraint(
            'company_id', 'fiscal_year', 'fiscal_period',
            name='uq_income_company_year_period'
        ),
        Index('idx_income_company_year', 'company_id', 'fiscal_year'),
    )

    def __repr__(self) -> str:
        return f"<IncomeStatement(company_id={self.company_id}, year={self.fiscal_year}, period={self.fiscal_period})>"


class BalanceSheet(Base):
    """
    Balance Sheet data - Assets, Liabilities, and Equity.

    Captures the financial position of a company at a specific point in time.
    Used for calculating financial ratios and health metrics.
    """

    __tablename__ = "balance_sheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(5), default="FY")

    # Assets
    cash_and_equivalents: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    short_term_investments: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    accounts_receivable: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    inventory: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_current_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    property_plant_equipment: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    goodwill: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    intangible_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_assets: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Liabilities
    accounts_payable: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    short_term_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_current_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    long_term_debt: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_liabilities: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Equity
    retained_earnings: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    total_equity: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Metadata
    data_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="balance_sheets")

    __table_args__ = (
        UniqueConstraint(
            'company_id', 'fiscal_year', 'fiscal_period',
            name='uq_balance_company_year_period'
        ),
        Index('idx_balance_company_year', 'company_id', 'fiscal_year'),
    )

    def __repr__(self) -> str:
        return f"<BalanceSheet(company_id={self.company_id}, year={self.fiscal_year})>"


class CashFlowStatement(Base):
    """
    Cash Flow Statement - Operating, Investing, and Financing activities.

    Tracks actual cash movements, essential for DCF valuations and
    assessing quality of earnings.
    """

    __tablename__ = "cash_flow_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(5), default="FY")

    # Operating activities
    net_income: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    depreciation_amortization: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    stock_based_compensation: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    operating_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Investing activities
    capital_expenditure: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    acquisitions: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    investing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Financing activities
    debt_repayment: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    dividends_paid: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    share_repurchases: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)
    financing_cash_flow: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), nullable=True)

    # Derived metric
    free_cash_flow: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        doc="Operating Cash Flow minus Capital Expenditure"
    )

    # Metadata
    data_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="cash_flow_statements")

    __table_args__ = (
        UniqueConstraint(
            'company_id', 'fiscal_year', 'fiscal_period',
            name='uq_cashflow_company_year_period'
        ),
        Index('idx_cashflow_company_year', 'company_id', 'fiscal_year'),
    )

    def __repr__(self) -> str:
        return f"<CashFlowStatement(company_id={self.company_id}, year={self.fiscal_year})>"


class StockPrice(Base):
    """
    Daily stock price data.

    Stores OHLCV (Open, High, Low, Close, Volume) data for historical analysis
    and current price comparisons in valuations.
    """

    __tablename__ = "stock_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    high_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    low_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    adjusted_close: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="stock_prices")

    __table_args__ = (
        UniqueConstraint('company_id', 'price_date', name='uq_price_company_date'),
        Index('idx_price_company_date', 'company_id', 'price_date'),
    )

    def __repr__(self) -> str:
        return f"<StockPrice(company_id={self.company_id}, date={self.price_date}, close={self.close_price})>"


class Valuation(Base):
    """
    Calculated valuations - cached results from financial models.

    Stores the output of valuation calculations:
    - DCF (Discounted Cash Flow) intrinsic value
    - Graham Number
    - Peter Lynch Fair Value
    - Financial health scores (Altman Z, Piotroski F)
    - Moat analysis results
    """

    __tablename__ = "valuations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # DCF Model
    dcf_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    dcf_assumptions: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        doc="JSON with growth_rate, discount_rate, terminal_growth"
    )

    # Graham Number
    graham_number: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)

    # Peter Lynch Fair Value
    lynch_fair_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    peg_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)

    # Current Price for Comparison
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    margin_of_safety: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 4),
        nullable=True,
        doc="(fair_value - price) / fair_value"
    )

    # Financial Health Scores
    altman_z_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    altman_rating: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Safe, Grey Zone, or Distress"
    )
    piotroski_f_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Score from 0-9"
    )
    piotroski_rating: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Strong, Moderate, or Weak"
    )

    # Moat Analysis
    moat_rating: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Wide, Narrow, or None"
    )
    roic_average: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    roic_trend: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Improving, Stable, or Declining"
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="valuations")

    __table_args__ = (
        Index('idx_valuation_company_date', 'company_id', 'calculated_at'),
    )

    def __repr__(self) -> str:
        return f"<Valuation(company_id={self.company_id}, dcf={self.dcf_value}, graham={self.graham_number})>"


class AIAnalysis(Base):
    """
    AI Analysis Results - Buffett AI investment verdicts.

    Stores the complete output from the Gemini AI analysis,
    including verdict, confidence scores, pros/cons, and detailed analysis.
    """

    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False
    )
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Input data snapshot
    input_summary: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Snapshot of financial data used for analysis"
    )

    # AI Response
    verdict: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        doc="BUY, HOLD, or SELL"
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="0-100 confidence percentage"
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Detailed analysis components
    pros: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    cons: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    detailed_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_metrics_cited: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Buffett-specific outputs
    would_buffett_buy: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    price_to_consider: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)

    # Metadata for versioning and reproducibility
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="ai_analyses")

    __table_args__ = (
        Index('idx_ai_analysis_company', 'company_id', 'analyzed_at'),
    )

    def __repr__(self) -> str:
        return f"<AIAnalysis(company_id={self.company_id}, verdict='{self.verdict}', confidence={self.confidence_score})>"


class DataFetchLog(Base):
    """
    API Fetch Logging - for cost tracking and debugging.

    Tracks all external API calls to monitor usage, costs, and errors.
    Essential for the 'fetch-once-store-forever' caching strategy.
    """

    __tablename__ = "data_fetch_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    response_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    was_cached: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Request duration in milliseconds"
    )

    __table_args__ = (
        Index('idx_fetch_log_ticker', 'ticker'),
        Index('idx_fetch_log_date', 'fetched_at'),
        Index('idx_fetch_log_provider', 'provider'),
    )

    def __repr__(self) -> str:
        return f"<DataFetchLog(ticker='{self.ticker}', provider='{self.provider}', cached={self.was_cached})>"
