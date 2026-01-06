"""
Valuations API endpoints.

Provides endpoints for:
- DCF valuations
- Graham Number calculations
- Peter Lynch Fair Value
- Financial health scores (Altman Z, Piotroski F)
- Moat analysis
- AI Analysis results
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.models import Company, Valuation, AIAnalysis

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class DCFValuationResponse(BaseModel):
    """DCF valuation response."""

    dcf_value: Optional[Decimal] = Field(None, description="DCF intrinsic value per share")
    dcf_assumptions: Optional[dict] = Field(
        None,
        description="DCF model assumptions (growth_rate, discount_rate, terminal_growth)"
    )
    current_price: Optional[Decimal] = None
    margin_of_safety: Optional[Decimal] = Field(
        None,
        description="(DCF value - current price) / DCF value"
    )

    class Config:
        from_attributes = True


class HealthScoresResponse(BaseModel):
    """Financial health scores response."""

    altman_z_score: Optional[Decimal] = Field(None, description="Altman Z-Score")
    altman_rating: Optional[str] = Field(None, description="Safe, Grey Zone, or Distress")
    piotroski_f_score: Optional[int] = Field(None, description="Piotroski F-Score (0-9)")
    piotroski_rating: Optional[str] = Field(None, description="Strong, Moderate, or Weak")

    class Config:
        from_attributes = True


class MoatAnalysisResponse(BaseModel):
    """Moat analysis response."""

    moat_rating: Optional[str] = Field(None, description="Wide, Narrow, or None")
    roic_average: Optional[Decimal] = Field(None, description="10-year average ROIC")
    roic_trend: Optional[str] = Field(None, description="Improving, Stable, or Declining")

    class Config:
        from_attributes = True


class ValuationResponse(BaseModel):
    """Complete valuation response."""

    ticker: str
    company_name: str
    calculated_at: datetime
    currency: str

    # DCF
    dcf_value: Optional[Decimal] = None
    dcf_assumptions: Optional[dict] = None

    # Graham Number
    graham_number: Optional[Decimal] = None

    # Lynch Fair Value
    lynch_fair_value: Optional[Decimal] = None
    peg_ratio: Optional[Decimal] = None

    # Current price and margin
    current_price: Optional[Decimal] = None
    margin_of_safety: Optional[Decimal] = None

    # Health scores
    altman_z_score: Optional[Decimal] = None
    altman_rating: Optional[str] = None
    piotroski_f_score: Optional[int] = None
    piotroski_rating: Optional[str] = None

    # Moat
    moat_rating: Optional[str] = None
    roic_average: Optional[Decimal] = None
    roic_trend: Optional[str] = None

    class Config:
        from_attributes = True


class AIAnalysisResponse(BaseModel):
    """AI Analysis response."""

    ticker: str
    analyzed_at: datetime
    verdict: Optional[str] = Field(None, description="BUY, HOLD, or SELL")
    confidence_score: Optional[Decimal] = Field(None, description="0-100 confidence")
    summary: Optional[str] = None
    pros: Optional[List[str]] = None
    cons: Optional[List[str]] = None
    detailed_analysis: Optional[str] = None
    key_metrics_cited: Optional[List[str]] = None
    would_buffett_buy: Optional[bool] = None
    price_to_consider: Optional[Decimal] = None
    model_version: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/{ticker}",
    response_model=ValuationResponse,
    summary="Get complete valuation",
    description="Returns all valuation metrics for a company.",
)
async def get_valuations(
    ticker: str,
    db: DbSession,
) -> ValuationResponse:
    """
    Get complete valuation data for a company.

    Includes:
    - DCF intrinsic value
    - Graham Number
    - Peter Lynch Fair Value
    - Altman Z-Score
    - Piotroski F-Score
    - Moat analysis
    """
    try:
        # Get company
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ticker '{ticker}' not found"
            )

        # Get latest valuation
        valuation_query = (
            select(Valuation)
            .where(Valuation.company_id == company.id)
            .order_by(Valuation.calculated_at.desc())
            .limit(1)
        )
        valuation_result = await db.execute(valuation_query)
        valuation = valuation_result.scalar_one_or_none()

        if not valuation:
            # Return empty valuation if none exists yet
            return ValuationResponse(
                ticker=company.ticker,
                company_name=company.name,
                calculated_at=datetime.utcnow(),
                currency=company.currency,
            )

        return ValuationResponse(
            ticker=company.ticker,
            company_name=company.name,
            calculated_at=valuation.calculated_at,
            currency=company.currency,
            dcf_value=valuation.dcf_value,
            dcf_assumptions=valuation.dcf_assumptions,
            graham_number=valuation.graham_number,
            lynch_fair_value=valuation.lynch_fair_value,
            peg_ratio=valuation.peg_ratio,
            current_price=valuation.current_price,
            margin_of_safety=valuation.margin_of_safety,
            altman_z_score=valuation.altman_z_score,
            altman_rating=valuation.altman_rating,
            piotroski_f_score=valuation.piotroski_f_score,
            piotroski_rating=valuation.piotroski_rating,
            moat_rating=valuation.moat_rating,
            roic_average=valuation.roic_average,
            roic_trend=valuation.roic_trend,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/{ticker}/dcf",
    response_model=DCFValuationResponse,
    summary="Get DCF valuation",
    description="Returns DCF intrinsic value calculation.",
)
async def get_dcf_valuation(
    ticker: str,
    db: DbSession,
) -> DCFValuationResponse:
    """Get DCF valuation for a company."""
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        valuation_query = (
            select(Valuation)
            .where(Valuation.company_id == company.id)
            .order_by(Valuation.calculated_at.desc())
            .limit(1)
        )
        result = await db.execute(valuation_query)
        valuation = result.scalar_one_or_none()

        if not valuation:
            return DCFValuationResponse()

        return DCFValuationResponse(
            dcf_value=valuation.dcf_value,
            dcf_assumptions=valuation.dcf_assumptions,
            current_price=valuation.current_price,
            margin_of_safety=valuation.margin_of_safety,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{ticker}/health",
    response_model=HealthScoresResponse,
    summary="Get financial health scores",
    description="Returns Altman Z-Score and Piotroski F-Score.",
)
async def get_health_scores(
    ticker: str,
    db: DbSession,
) -> HealthScoresResponse:
    """Get financial health scores for a company."""
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        valuation_query = (
            select(Valuation)
            .where(Valuation.company_id == company.id)
            .order_by(Valuation.calculated_at.desc())
            .limit(1)
        )
        result = await db.execute(valuation_query)
        valuation = result.scalar_one_or_none()

        if not valuation:
            return HealthScoresResponse()

        return HealthScoresResponse(
            altman_z_score=valuation.altman_z_score,
            altman_rating=valuation.altman_rating,
            piotroski_f_score=valuation.piotroski_f_score,
            piotroski_rating=valuation.piotroski_rating,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{ticker}/moat",
    response_model=MoatAnalysisResponse,
    summary="Get moat analysis",
    description="Returns economic moat analysis based on ROIC trends.",
)
async def get_moat_analysis(
    ticker: str,
    db: DbSession,
) -> MoatAnalysisResponse:
    """Get moat analysis for a company."""
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        valuation_query = (
            select(Valuation)
            .where(Valuation.company_id == company.id)
            .order_by(Valuation.calculated_at.desc())
            .limit(1)
        )
        result = await db.execute(valuation_query)
        valuation = result.scalar_one_or_none()

        if not valuation:
            return MoatAnalysisResponse()

        return MoatAnalysisResponse(
            moat_rating=valuation.moat_rating,
            roic_average=valuation.roic_average,
            roic_trend=valuation.roic_trend,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{ticker}/ai-analysis",
    response_model=AIAnalysisResponse,
    summary="Get AI analysis",
    description="Returns the latest Buffett AI investment analysis.",
)
async def get_ai_analysis(
    ticker: str,
    db: DbSession,
) -> AIAnalysisResponse:
    """
    Get the latest AI analysis for a company.

    Returns the most recent Buffett AI verdict including:
    - Investment verdict (BUY/HOLD/SELL)
    - Confidence score
    - Pros and cons
    - Detailed analysis
    """
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        analysis_query = (
            select(AIAnalysis)
            .where(AIAnalysis.company_id == company.id)
            .order_by(AIAnalysis.analyzed_at.desc())
            .limit(1)
        )
        result = await db.execute(analysis_query)
        analysis = result.scalar_one_or_none()

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"No AI analysis found for '{ticker}'. Analysis may need to be generated."
            )

        return AIAnalysisResponse(
            ticker=company.ticker,
            analyzed_at=analysis.analyzed_at,
            verdict=analysis.verdict,
            confidence_score=analysis.confidence_score,
            summary=analysis.summary,
            pros=analysis.pros,
            cons=analysis.cons,
            detailed_analysis=analysis.detailed_analysis,
            key_metrics_cited=analysis.key_metrics_cited,
            would_buffett_buy=analysis.would_buffett_buy,
            price_to_consider=analysis.price_to_consider,
            model_version=analysis.model_version,
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{ticker}/ai-analysis/history",
    response_model=List[AIAnalysisResponse],
    summary="Get AI analysis history",
    description="Returns historical AI analyses for a company.",
)
async def get_ai_analysis_history(
    ticker: str,
    db: DbSession,
    limit: int = Query(10, ge=1, le=50),
) -> List[AIAnalysisResponse]:
    """Get historical AI analyses for a company."""
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        analysis_query = (
            select(AIAnalysis)
            .where(AIAnalysis.company_id == company.id)
            .order_by(AIAnalysis.analyzed_at.desc())
            .limit(limit)
        )
        result = await db.execute(analysis_query)
        analyses = result.scalars().all()

        return [
            AIAnalysisResponse(
                ticker=company.ticker,
                analyzed_at=a.analyzed_at,
                verdict=a.verdict,
                confidence_score=a.confidence_score,
                summary=a.summary,
                pros=a.pros,
                cons=a.cons,
                detailed_analysis=a.detailed_analysis,
                key_metrics_cited=a.key_metrics_cited,
                would_buffett_buy=a.would_buffett_buy,
                price_to_consider=a.price_to_consider,
                model_version=a.model_version,
            )
            for a in analyses
        ]

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
