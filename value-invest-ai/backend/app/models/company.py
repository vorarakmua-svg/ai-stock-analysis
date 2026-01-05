from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Company(Base):
    """
    Companies master table.
    Handles both US (AAPL) and Thai (PTT.BK) ticker formats.
    """
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    market = Column(String(10), nullable=False)  # 'US' or 'SET'
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    currency = Column(String(3), nullable=False)  # 'USD' or 'THB'
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    income_statements = relationship("IncomeStatement", back_populates="company", cascade="all, delete-orphan")
    balance_sheets = relationship("BalanceSheet", back_populates="company", cascade="all, delete-orphan")
    cash_flow_statements = relationship("CashFlowStatement", back_populates="company", cascade="all, delete-orphan")
    stock_prices = relationship("StockPrice", back_populates="company", cascade="all, delete-orphan")
    valuations = relationship("Valuation", back_populates="company", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="company", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_companies_market', 'market'),
        Index('idx_companies_sector', 'sector'),
    )

    def __repr__(self):
        return f"<Company(ticker='{self.ticker}', market='{self.market}', currency='{self.currency}')>"
