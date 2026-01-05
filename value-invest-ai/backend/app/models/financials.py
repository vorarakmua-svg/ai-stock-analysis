from sqlalchemy import Column, Integer, String, Numeric, BigInteger, Boolean, DateTime, Date, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class IncomeStatement(Base):
    """
    Income Statement data - 30 years of history per company.
    """
    __tablename__ = "income_statements"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_period = Column(String(5), default="FY")  # FY, Q1, Q2, Q3, Q4

    # Revenue metrics
    revenue = Column(Numeric(20, 2), nullable=True)
    cost_of_revenue = Column(Numeric(20, 2), nullable=True)
    gross_profit = Column(Numeric(20, 2), nullable=True)

    # Operating metrics
    operating_expenses = Column(Numeric(20, 2), nullable=True)
    operating_income = Column(Numeric(20, 2), nullable=True)

    # Bottom line
    interest_expense = Column(Numeric(20, 2), nullable=True)
    pretax_income = Column(Numeric(20, 2), nullable=True)
    income_tax = Column(Numeric(20, 2), nullable=True)
    net_income = Column(Numeric(20, 2), nullable=True)

    # Per share
    eps_basic = Column(Numeric(10, 4), nullable=True)
    eps_diluted = Column(Numeric(10, 4), nullable=True)
    shares_outstanding = Column(BigInteger, nullable=True)

    # Metadata
    is_estimated = Column(Boolean, default=False)
    data_source = Column(String(50), nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="income_statements")

    __table_args__ = (
        UniqueConstraint('company_id', 'fiscal_year', 'fiscal_period', name='uq_income_company_year_period'),
        Index('idx_income_company_year', 'company_id', 'fiscal_year'),
    )

    def __repr__(self):
        return f"<IncomeStatement(company_id={self.company_id}, year={self.fiscal_year})>"


class BalanceSheet(Base):
    """
    Balance Sheet data - Assets, Liabilities, Equity.
    """
    __tablename__ = "balance_sheets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_period = Column(String(5), default="FY")

    # Assets
    cash_and_equivalents = Column(Numeric(20, 2), nullable=True)
    short_term_investments = Column(Numeric(20, 2), nullable=True)
    accounts_receivable = Column(Numeric(20, 2), nullable=True)
    inventory = Column(Numeric(20, 2), nullable=True)
    total_current_assets = Column(Numeric(20, 2), nullable=True)
    property_plant_equipment = Column(Numeric(20, 2), nullable=True)
    goodwill = Column(Numeric(20, 2), nullable=True)
    intangible_assets = Column(Numeric(20, 2), nullable=True)
    total_assets = Column(Numeric(20, 2), nullable=True)

    # Liabilities
    accounts_payable = Column(Numeric(20, 2), nullable=True)
    short_term_debt = Column(Numeric(20, 2), nullable=True)
    total_current_liabilities = Column(Numeric(20, 2), nullable=True)
    long_term_debt = Column(Numeric(20, 2), nullable=True)
    total_liabilities = Column(Numeric(20, 2), nullable=True)

    # Equity
    retained_earnings = Column(Numeric(20, 2), nullable=True)
    total_equity = Column(Numeric(20, 2), nullable=True)

    # Metadata
    data_source = Column(String(50), nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="balance_sheets")

    __table_args__ = (
        UniqueConstraint('company_id', 'fiscal_year', 'fiscal_period', name='uq_balance_company_year_period'),
        Index('idx_balance_company_year', 'company_id', 'fiscal_year'),
    )

    def __repr__(self):
        return f"<BalanceSheet(company_id={self.company_id}, year={self.fiscal_year})>"


class CashFlowStatement(Base):
    """
    Cash Flow Statement - Operating, Investing, Financing activities.
    """
    __tablename__ = "cash_flow_statements"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_period = Column(String(5), default="FY")

    # Operating activities
    net_income = Column(Numeric(20, 2), nullable=True)
    depreciation_amortization = Column(Numeric(20, 2), nullable=True)
    stock_based_compensation = Column(Numeric(20, 2), nullable=True)
    operating_cash_flow = Column(Numeric(20, 2), nullable=True)

    # Investing activities
    capital_expenditure = Column(Numeric(20, 2), nullable=True)
    acquisitions = Column(Numeric(20, 2), nullable=True)
    investing_cash_flow = Column(Numeric(20, 2), nullable=True)

    # Financing activities
    debt_repayment = Column(Numeric(20, 2), nullable=True)
    dividends_paid = Column(Numeric(20, 2), nullable=True)
    share_repurchases = Column(Numeric(20, 2), nullable=True)
    financing_cash_flow = Column(Numeric(20, 2), nullable=True)

    # Derived
    free_cash_flow = Column(Numeric(20, 2), nullable=True)  # OCF - CapEx

    # Metadata
    data_source = Column(String(50), nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="cash_flow_statements")

    __table_args__ = (
        UniqueConstraint('company_id', 'fiscal_year', 'fiscal_period', name='uq_cashflow_company_year_period'),
        Index('idx_cashflow_company_year', 'company_id', 'fiscal_year'),
    )

    def __repr__(self):
        return f"<CashFlowStatement(company_id={self.company_id}, year={self.fiscal_year})>"


class StockPrice(Base):
    """
    Daily stock price data.
    """
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    open_price = Column(Numeric(12, 4), nullable=True)
    high_price = Column(Numeric(12, 4), nullable=True)
    low_price = Column(Numeric(12, 4), nullable=True)
    close_price = Column(Numeric(12, 4), nullable=True)
    adjusted_close = Column(Numeric(12, 4), nullable=True)
    volume = Column(BigInteger, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="stock_prices")

    __table_args__ = (
        UniqueConstraint('company_id', 'price_date', name='uq_price_company_date'),
        Index('idx_price_company_date', 'company_id', 'price_date'),
    )

    def __repr__(self):
        return f"<StockPrice(company_id={self.company_id}, date={self.price_date})>"
