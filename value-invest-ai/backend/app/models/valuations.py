from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Valuation(Base):
    """
    Calculated valuations - cached results from financial models.
    """
    __tablename__ = "valuations"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # DCF Model
    dcf_value = Column(Numeric(12, 4), nullable=True)
    dcf_assumptions = Column(JSONB, nullable=True)  # {growth_rate, discount_rate, terminal_growth}

    # Graham Number
    graham_number = Column(Numeric(12, 4), nullable=True)

    # Peter Lynch Fair Value
    lynch_fair_value = Column(Numeric(12, 4), nullable=True)
    peg_ratio = Column(Numeric(8, 4), nullable=True)

    # Current Price for Comparison
    current_price = Column(Numeric(12, 4), nullable=True)
    margin_of_safety = Column(Numeric(8, 4), nullable=True)  # (fair_value - price) / fair_value

    # Financial Health Scores
    altman_z_score = Column(Numeric(8, 4), nullable=True)
    altman_rating = Column(String(20), nullable=True)  # Safe, Grey Zone, Distress
    piotroski_f_score = Column(Integer, nullable=True)  # 0-9
    piotroski_rating = Column(String(20), nullable=True)  # Strong, Moderate, Weak

    # Moat Analysis
    moat_rating = Column(String(20), nullable=True)  # Wide, Narrow, None
    roic_average = Column(Numeric(8, 4), nullable=True)
    roic_trend = Column(String(20), nullable=True)  # Improving, Stable, Declining

    # Relationships
    company = relationship("Company", back_populates="valuations")

    __table_args__ = (
        Index('idx_valuation_company_date', 'company_id', 'calculated_at'),
    )

    def __repr__(self):
        return f"<Valuation(company_id={self.company_id}, dcf={self.dcf_value})>"


class AIAnalysis(Base):
    """
    AI Analysis Results - Buffett AI verdicts.
    """
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Input data snapshot
    input_summary = Column(JSONB, nullable=True)

    # AI Response
    verdict = Column(String(10), nullable=True)  # BUY, HOLD, SELL
    confidence_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    summary = Column(Text, nullable=True)

    pros = Column(JSONB, nullable=True)  # ["Strong moat", "Consistent FCF"]
    cons = Column(JSONB, nullable=True)  # ["High debt", "Declining margins"]

    detailed_analysis = Column(Text, nullable=True)
    key_metrics_cited = Column(JSONB, nullable=True)  # ["ROIC: 18%", "D/E: 0.3"]

    would_buffett_buy = Column(Boolean, nullable=True)
    price_to_consider = Column(Numeric(12, 4), nullable=True)

    # Metadata
    model_version = Column(String(50), nullable=True)
    prompt_version = Column(String(20), nullable=True)

    # Relationships
    company = relationship("Company", back_populates="ai_analyses")

    __table_args__ = (
        Index('idx_ai_analysis_company', 'company_id', 'analyzed_at'),
    )

    def __repr__(self):
        return f"<AIAnalysis(company_id={self.company_id}, verdict='{self.verdict}')>"


class DataFetchLog(Base):
    """
    API Fetch Logging - for cost tracking.
    """
    __tablename__ = "data_fetch_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False)
    provider = Column(String(50), nullable=False)
    endpoint = Column(String(100), nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    response_size = Column(Integer, nullable=True)
    was_cached = Column(Boolean, default=False)
    error_message = Column(String(500), nullable=True)

    __table_args__ = (
        Index('idx_fetch_log_ticker', 'ticker'),
        Index('idx_fetch_log_date', 'fetched_at'),
    )

    def __repr__(self):
        return f"<DataFetchLog(ticker='{self.ticker}', provider='{self.provider}')>"
