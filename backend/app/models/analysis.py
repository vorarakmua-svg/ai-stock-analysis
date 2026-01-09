"""
Pydantic models for AI-generated investment analysis.

This module defines the complete schema for Warren Buffett-style
investment analysis including:
- Competitive advantage (moat) analysis
- Risk factor categorization
- Investment rating and conviction scoring
- Business quality assessment

The AI analyst generates these outputs based on valuation results
and company financial data. All mathematical calculations are
performed in Python (valuation_engine.py) - the AI only generates
qualitative analysis and structured narratives.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InvestmentRating(str, Enum):
    """
    Investment recommendation rating.

    Ratings follow a traditional five-tier system:
    - STRONG_BUY: Exceptional opportunity with high conviction
    - BUY: Attractive investment with good risk/reward
    - HOLD: Fair value, hold existing positions
    - SELL: Overvalued, reduce exposure
    - STRONG_SELL: Significant downside risk, exit position
    """

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class RiskLevel(str, Enum):
    """
    Overall risk assessment level.

    Considers business risk, financial risk, and valuation risk:
    - LOW: Stable business, strong balance sheet, reasonable valuation
    - MODERATE: Some risk factors but manageable
    - HIGH: Significant risks that could impact returns
    - VERY_HIGH: Substantial downside risks, speculative
    """

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MoatType(str, Enum):
    """
    Types of competitive advantages (economic moats).

    Based on Morningstar's moat framework:
    - BRAND: Strong brand recognition and pricing power (e.g., Coca-Cola, Apple)
    - NETWORK_EFFECTS: Value increases with users (e.g., Visa, Meta)
    - COST_ADVANTAGE: Structural cost leadership (e.g., Costco, GEICO)
    - SWITCHING_COSTS: High customer lock-in (e.g., Microsoft, Oracle)
    - EFFICIENT_SCALE: Natural monopoly economics (e.g., railroads, utilities)
    - INTANGIBLE_ASSETS: Patents, licenses, regulatory advantages
    - NONE: No identifiable durable competitive advantage
    """

    BRAND = "brand"
    NETWORK_EFFECTS = "network_effects"
    COST_ADVANTAGE = "cost_advantage"
    SWITCHING_COSTS = "switching_costs"
    EFFICIENT_SCALE = "efficient_scale"
    INTANGIBLE_ASSETS = "intangible_assets"
    NONE = "none"


class CompetitiveAdvantage(BaseModel):
    """
    Analysis of a single competitive moat.

    Identifies the type of moat, provides supporting evidence,
    and assesses its durability and strength.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    moat_type: MoatType = Field(
        ...,
        description="Type of competitive advantage identified",
    )
    description: str = Field(
        ...,
        description="Detailed description of the competitive advantage",
    )
    durability: str = Field(
        ...,
        description="Assessment of moat durability: 'narrow', 'wide', or 'eroding'",
    )
    evidence: List[str] = Field(
        ...,
        description="Specific evidence supporting this moat (2-4 bullet points)",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level in this moat assessment (0.0 to 1.0)",
    )


class RiskFactor(BaseModel):
    """
    Detailed risk assessment for a specific risk.

    Categorizes risks and provides severity, probability,
    and potential mitigation strategies.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    category: str = Field(
        ...,
        description="Risk category: 'market', 'regulatory', 'competitive', 'operational', 'financial'",
    )
    title: str = Field(
        ...,
        description="Brief title summarizing the risk",
    )
    description: str = Field(
        ...,
        description="Detailed explanation of the risk and its potential impact",
    )
    severity: str = Field(
        ...,
        description="Impact severity if risk materializes: 'low', 'medium', 'high', 'critical'",
    )
    probability: str = Field(
        ...,
        description="Likelihood of occurrence: 'unlikely', 'possible', 'likely', 'very_likely'",
    )
    mitigation: Optional[str] = Field(
        None,
        description="Potential mitigation strategies or factors that reduce the risk",
    )


class WarrenBuffettAnalysis(BaseModel):
    """
    AI-generated investment memo in Warren Buffett style.

    Combines quantitative valuation results with qualitative business
    analysis to produce a comprehensive investment assessment. Written
    in first person as Warren Buffett would analyze a potential investment.

    The analysis covers:
    - Executive Summary with one-sentence thesis
    - Business Quality Assessment (understanding, moats, management)
    - Financial Health evaluation
    - Valuation Summary with intrinsic value assessment
    - Key Investment Considerations (positives, concerns, risks, catalysts)
    - Final Verdict with rating and conviction level

    Note: All numerical values in this analysis come from the Python
    valuation engine. The AI only generates narrative and qualitative
    assessments based on those computed values.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )

    # === Header ===
    ticker: str = Field(
        ...,
        description="Stock ticker symbol",
    )
    company_name: str = Field(
        ...,
        description="Full company name",
    )
    analysis_date: datetime = Field(
        ...,
        description="Date and time of analysis generation",
    )

    # === Executive Summary ===
    one_sentence_thesis: str = Field(
        ...,
        description="One compelling sentence summarizing the investment case",
    )
    investment_thesis: str = Field(
        ...,
        description="2-3 paragraph detailed investment thesis explaining the opportunity",
    )

    # === Business Quality Assessment ===

    # Circle of Competence
    business_understanding: str = Field(
        ...,
        description="Can I understand this business in 10 minutes? Explanation of business model simplicity.",
    )
    business_simplicity_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Business simplicity: 1=highly complex/unpredictable, 10=simple and predictable",
    )

    # Economic Moat
    competitive_advantages: List[CompetitiveAdvantage] = Field(
        ...,
        description="List of identified competitive moats (can be empty if none found)",
    )
    moat_summary: str = Field(
        ...,
        description="Summary paragraph describing the company's overall competitive position",
    )
    moat_durability: str = Field(
        ...,
        description="Overall moat assessment: 'none', 'narrow', or 'wide'",
    )

    # Management Quality
    management_assessment: str = Field(
        ...,
        description="Assessment of management quality, track record, and alignment with shareholders",
    )
    management_integrity_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Management integrity and competence: 1=concerning, 10=exceptional",
    )
    capital_allocation_skill: str = Field(
        ...,
        description="Assessment of management's capital allocation decisions (buybacks, dividends, M&A)",
    )
    owner_oriented: bool = Field(
        ...,
        description="Does management think and act like owners?",
    )

    # Owner Earnings Power
    owner_earnings_analysis: str = Field(
        ...,
        description="Analysis of true cash-generating ability (owner earnings concept)",
    )
    earnings_predictability: str = Field(
        ...,
        description="Earnings predictability: 'highly_predictable', 'predictable', 'uncertain', 'unpredictable'",
    )

    # === Financial Health ===
    balance_sheet_fortress: str = Field(
        ...,
        description="Assessment of balance sheet strength and financial stability",
    )
    debt_comfort_level: str = Field(
        ...,
        description="Comfort level with company's debt situation and leverage",
    )
    cash_generation_power: str = Field(
        ...,
        description="Assessment of cash flow generation capability and consistency",
    )
    return_on_capital_trend: str = Field(
        ...,
        description="Analysis of ROE/ROIC trends and capital efficiency",
    )

    # === Valuation Summary ===
    valuation_narrative: str = Field(
        ...,
        description="Narrative explaining the valuation analysis and key drivers",
    )
    intrinsic_value_range: str = Field(
        ...,
        description="Intrinsic value estimate range in '$X to $Y' format",
    )
    current_price_vs_value: str = Field(
        ...,
        description="Assessment of current price relative to intrinsic value",
    )
    margin_of_safety_assessment: str = Field(
        ...,
        description="Assessment of margin of safety for this investment",
    )

    # === Key Investment Considerations ===
    key_positives: List[str] = Field(
        ...,
        min_length=3,
        max_length=7,
        description="Main reasons to buy this stock (3-7 bullet points)",
    )
    key_concerns: List[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Main risks and concerns about this investment (2-5 bullet points)",
    )
    key_risks: List[RiskFactor] = Field(
        ...,
        description="Detailed risk factor analysis (2-4 key risks)",
    )
    potential_catalysts: List[str] = Field(
        ...,
        description="Events or factors that could unlock value (2-5 catalysts)",
    )

    # === Time Horizon ===
    ideal_holding_period: str = Field(
        ...,
        description="Recommended holding period: '3-5 years', '5-10 years', or 'forever'",
    )
    patience_required_level: str = Field(
        ...,
        description="Description of patience required for this investment",
    )

    # === Final Verdict ===
    investment_rating: InvestmentRating = Field(
        ...,
        description="Final investment recommendation rating",
    )
    conviction_level: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence/conviction level in this rating (0.0 to 1.0)",
    )
    risk_level: RiskLevel = Field(
        ...,
        description="Overall risk assessment level",
    )
    suitable_for: List[str] = Field(
        ...,
        description="Investor types this investment suits: 'value_investors', 'dividend_seekers', 'growth_investors', 'conservative_investors', etc.",
    )

    # === Closing Wisdom ===
    buffett_quote: str = Field(
        ...,
        description="Relevant Warren Buffett quote that applies to this situation",
    )
    final_thoughts: str = Field(
        ...,
        description="Closing thoughts and final perspective on the investment",
    )

    # === Meta ===
    ai_model_used: str = Field(
        ...,
        description="Name of the AI model used for analysis generation",
    )
    analysis_version: str = Field(
        default="1.0",
        description="Version of the analysis schema/methodology",
    )
    tokens_consumed: Optional[int] = Field(
        None,
        description="Number of tokens consumed in generation (if available)",
    )
    generation_time_seconds: Optional[float] = Field(
        None,
        description="Time taken to generate this analysis in seconds",
    )
