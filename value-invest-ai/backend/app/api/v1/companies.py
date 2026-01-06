"""
Companies API endpoints.

Provides endpoints for:
- Listing tracked companies
- Getting company details by ticker
- Searching companies
"""

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.models import Company

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class CompanyResponse(BaseModel):
    """Response model for a single company."""

    id: int
    ticker: str = Field(..., description="Stock ticker symbol")
    name: str = Field(..., description="Full company name")
    market: str = Field(..., description="Market: 'US' or 'SET'")
    sector: Optional[str] = Field(None, description="Business sector")
    industry: Optional[str] = Field(None, description="Specific industry")
    currency: str = Field(..., description="Trading currency: 'USD' or 'THB'")
    description: Optional[str] = Field(None, description="Company description")

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    """Response model for company list."""

    companies: List[CompanyResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "",
    response_model=CompanyListResponse,
    summary="List all tracked companies",
    description="Returns a paginated list of all companies tracked in the system.",
)
async def list_companies(
    db: DbSession,
    market: Optional[str] = Query(
        None,
        description="Filter by market ('US' or 'SET')",
        regex="^(US|SET)$"
    ),
    sector: Optional[str] = Query(
        None,
        description="Filter by sector"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> CompanyListResponse:
    """
    List all tracked companies with optional filtering.

    - **market**: Filter by market (US for NYSE/NASDAQ, SET for Thai)
    - **sector**: Filter by business sector
    - **page**: Page number for pagination
    - **page_size**: Number of items per page (max 100)
    """
    try:
        # Build query
        query = select(Company)

        if market:
            query = query.where(Company.market == market)
        if sector:
            query = query.where(Company.sector == sector)

        # Get total count
        count_query = select(Company.id)
        if market:
            count_query = count_query.where(Company.market == market)
        if sector:
            count_query = count_query.where(Company.sector == sector)

        count_result = await db.execute(count_query)
        total = len(count_result.all())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Company.ticker)

        # Execute query
        result = await db.execute(query)
        companies = result.scalars().all()

        return CompanyListResponse(
            companies=[CompanyResponse.model_validate(c) for c in companies],
            total=total,
            page=page,
            page_size=page_size,
        )

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/{ticker}",
    response_model=CompanyResponse,
    summary="Get company by ticker",
    description="Returns detailed information about a specific company.",
)
async def get_company(
    ticker: str,
    db: DbSession,
) -> CompanyResponse:
    """
    Get company details by ticker symbol.

    - **ticker**: Stock ticker symbol (e.g., AAPL, PTT.BK)
    """
    try:
        query = select(Company).where(Company.ticker == ticker.upper())
        result = await db.execute(query)
        company = result.scalar_one_or_none()

        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"Company with ticker '{ticker}' not found"
            )

        return CompanyResponse.model_validate(company)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/search/{query}",
    response_model=List[CompanyResponse],
    summary="Search companies",
    description="Search companies by name or ticker.",
)
async def search_companies(
    query: str,
    db: DbSession,
    market: Optional[str] = Query(None, regex="^(US|SET)$"),
    limit: int = Query(10, ge=1, le=50),
) -> List[CompanyResponse]:
    """
    Search companies by name or ticker.

    - **query**: Search term (minimum 1 character)
    - **market**: Optional market filter
    - **limit**: Maximum results to return
    """
    if len(query) < 1:
        raise HTTPException(
            status_code=400,
            detail="Search query must be at least 1 character"
        )

    try:
        search_term = f"%{query.upper()}%"
        stmt = select(Company).where(
            (Company.ticker.ilike(search_term)) |
            (Company.name.ilike(f"%{query}%"))
        )

        if market:
            stmt = stmt.where(Company.market == market)

        stmt = stmt.limit(limit).order_by(Company.ticker)

        result = await db.execute(stmt)
        companies = result.scalars().all()

        return [CompanyResponse.model_validate(c) for c in companies]

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
