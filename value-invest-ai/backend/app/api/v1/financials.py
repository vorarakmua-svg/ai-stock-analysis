"""
Financials API endpoints.

Provides endpoints for:
- Income statements (30 years of history)
- Balance sheets
- Cash flow statements
- Stock prices
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.models import (
    Company,
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    StockPrice,
)

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================

class IncomeStatementResponse(BaseModel):
    """Response model for income statement data."""

    fiscal_year: int
    fiscal_period: str
    revenue: Optional[Decimal] = None
    cost_of_revenue: Optional[Decimal] = None
    gross_profit: Optional[Decimal] = None
    operating_expenses: Optional[Decimal] = None
    operating_income: Optional[Decimal] = None
    interest_expense: Optional[Decimal] = None
    pretax_income: Optional[Decimal] = None
    income_tax: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    eps_basic: Optional[Decimal] = None
    eps_diluted: Optional[Decimal] = None
    shares_outstanding: Optional[int] = None

    class Config:
        from_attributes = True


class BalanceSheetResponse(BaseModel):
    """Response model for balance sheet data."""

    fiscal_year: int
    fiscal_period: str
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

    class Config:
        from_attributes = True


class CashFlowResponse(BaseModel):
    """Response model for cash flow statement data."""

    fiscal_year: int
    fiscal_period: str
    # Operating
    net_income: Optional[Decimal] = None
    depreciation_amortization: Optional[Decimal] = None
    stock_based_compensation: Optional[Decimal] = None
    operating_cash_flow: Optional[Decimal] = None
    # Investing
    capital_expenditure: Optional[Decimal] = None
    acquisitions: Optional[Decimal] = None
    investing_cash_flow: Optional[Decimal] = None
    # Financing
    debt_repayment: Optional[Decimal] = None
    dividends_paid: Optional[Decimal] = None
    share_repurchases: Optional[Decimal] = None
    financing_cash_flow: Optional[Decimal] = None
    # Derived
    free_cash_flow: Optional[Decimal] = None

    class Config:
        from_attributes = True


class StockPriceResponse(BaseModel):
    """Response model for stock price data."""

    price_date: date
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None

    class Config:
        from_attributes = True


class FinancialSummaryResponse(BaseModel):
    """Complete financial summary for a company."""

    ticker: str
    company_name: str
    market: str
    currency: str
    income_statements: List[IncomeStatementResponse]
    balance_sheets: List[BalanceSheetResponse]
    cash_flow_statements: List[CashFlowResponse]


# =============================================================================
# Endpoints
# =============================================================================

@router.get(
    "/{ticker}",
    response_model=FinancialSummaryResponse,
    summary="Get financial summary",
    description="Returns complete financial history for a company.",
)
async def get_financials(
    ticker: str,
    db: DbSession,
    years: int = Query(10, ge=1, le=30, description="Number of years of history"),
    period: str = Query("FY", description="Fiscal period: FY, Q1, Q2, Q3, Q4"),
) -> FinancialSummaryResponse:
    """
    Get complete financial data for a company.

    - **ticker**: Stock ticker symbol
    - **years**: Number of years of history (1-30)
    - **period**: Fiscal period filter (FY for annual, Q1-Q4 for quarterly)
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

        # Get income statements
        income_query = (
            select(IncomeStatement)
            .where(IncomeStatement.company_id == company.id)
            .where(IncomeStatement.fiscal_period == period)
            .order_by(IncomeStatement.fiscal_year.desc())
            .limit(years)
        )
        income_result = await db.execute(income_query)
        income_statements = income_result.scalars().all()

        # Get balance sheets
        balance_query = (
            select(BalanceSheet)
            .where(BalanceSheet.company_id == company.id)
            .where(BalanceSheet.fiscal_period == period)
            .order_by(BalanceSheet.fiscal_year.desc())
            .limit(years)
        )
        balance_result = await db.execute(balance_query)
        balance_sheets = balance_result.scalars().all()

        # Get cash flow statements
        cashflow_query = (
            select(CashFlowStatement)
            .where(CashFlowStatement.company_id == company.id)
            .where(CashFlowStatement.fiscal_period == period)
            .order_by(CashFlowStatement.fiscal_year.desc())
            .limit(years)
        )
        cashflow_result = await db.execute(cashflow_query)
        cash_flows = cashflow_result.scalars().all()

        return FinancialSummaryResponse(
            ticker=company.ticker,
            company_name=company.name,
            market=company.market,
            currency=company.currency,
            income_statements=[
                IncomeStatementResponse.model_validate(s) for s in income_statements
            ],
            balance_sheets=[
                BalanceSheetResponse.model_validate(s) for s in balance_sheets
            ],
            cash_flow_statements=[
                CashFlowResponse.model_validate(s) for s in cash_flows
            ],
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get(
    "/{ticker}/income",
    response_model=List[IncomeStatementResponse],
    summary="Get income statements",
    description="Returns income statement history for a company.",
)
async def get_income_statements(
    ticker: str,
    db: DbSession,
    years: int = Query(10, ge=1, le=30),
    period: str = Query("FY"),
) -> List[IncomeStatementResponse]:
    """Get income statements for a company."""
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = (
            select(IncomeStatement)
            .where(IncomeStatement.company_id == company.id)
            .where(IncomeStatement.fiscal_period == period)
            .order_by(IncomeStatement.fiscal_year.desc())
            .limit(years)
        )
        result = await db.execute(query)
        statements = result.scalars().all()

        return [IncomeStatementResponse.model_validate(s) for s in statements]

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{ticker}/balance",
    response_model=List[BalanceSheetResponse],
    summary="Get balance sheets",
    description="Returns balance sheet history for a company.",
)
async def get_balance_sheets(
    ticker: str,
    db: DbSession,
    years: int = Query(10, ge=1, le=30),
    period: str = Query("FY"),
) -> List[BalanceSheetResponse]:
    """Get balance sheets for a company."""
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = (
            select(BalanceSheet)
            .where(BalanceSheet.company_id == company.id)
            .where(BalanceSheet.fiscal_period == period)
            .order_by(BalanceSheet.fiscal_year.desc())
            .limit(years)
        )
        result = await db.execute(query)
        sheets = result.scalars().all()

        return [BalanceSheetResponse.model_validate(s) for s in sheets]

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{ticker}/cashflow",
    response_model=List[CashFlowResponse],
    summary="Get cash flow statements",
    description="Returns cash flow statement history for a company.",
)
async def get_cash_flows(
    ticker: str,
    db: DbSession,
    years: int = Query(10, ge=1, le=30),
    period: str = Query("FY"),
) -> List[CashFlowResponse]:
    """Get cash flow statements for a company."""
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = (
            select(CashFlowStatement)
            .where(CashFlowStatement.company_id == company.id)
            .where(CashFlowStatement.fiscal_period == period)
            .order_by(CashFlowStatement.fiscal_year.desc())
            .limit(years)
        )
        result = await db.execute(query)
        statements = result.scalars().all()

        return [CashFlowResponse.model_validate(s) for s in statements]

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{ticker}/prices",
    response_model=List[StockPriceResponse],
    summary="Get stock prices",
    description="Returns historical stock prices for a company.",
)
async def get_stock_prices(
    ticker: str,
    db: DbSession,
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(252, ge=1, le=7560, description="Max records (252 = 1 year)"),
) -> List[StockPriceResponse]:
    """
    Get historical stock prices for a company.

    - **ticker**: Stock ticker symbol
    - **start_date**: Start date for price history
    - **end_date**: End date for price history
    - **limit**: Maximum number of records (default 252 = 1 trading year)
    """
    try:
        company_query = select(Company).where(Company.ticker == ticker.upper())
        company_result = await db.execute(company_query)
        company = company_result.scalar_one_or_none()

        if not company:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = (
            select(StockPrice)
            .where(StockPrice.company_id == company.id)
        )

        if start_date:
            query = query.where(StockPrice.price_date >= start_date)
        if end_date:
            query = query.where(StockPrice.price_date <= end_date)

        query = query.order_by(StockPrice.price_date.desc()).limit(limit)

        result = await db.execute(query)
        prices = result.scalars().all()

        return [StockPriceResponse.model_validate(p) for p in prices]

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
