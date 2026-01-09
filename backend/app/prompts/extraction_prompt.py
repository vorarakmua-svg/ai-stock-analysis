"""
AI extraction prompts for standardized valuation input data.

This module contains the system and user prompts used by Gemini Pro
to extract and normalize financial data from raw JSON into the
StandardizedValuationInput schema.

The AI layer handles:
- Field name normalization (Revenue = Net Sales = Total Revenue)
- TTM calculations from quarterly data
- CAGR calculations from historical annual data
- Data quality assessment and confidence scoring
- Missing field handling

The AI DOES NOT:
- Calculate valuation formulas (DCF, Graham, WACC)
- Make investment recommendations
- Perform complex mathematical operations
"""

import json

# Schema definition for inclusion in prompts
STANDARDIZED_VALUATION_INPUT_SCHEMA = {
    "type": "object",
    "required": [
        "ticker",
        "company_name",
        "sector",
        "industry",
        "extraction_timestamp",
        "data_confidence_score",
        "current_price",
        "shares_outstanding",
        "market_cap",
        "enterprise_value",
        "ttm_revenue",
        "ttm_cost_of_revenue",
        "ttm_gross_profit",
        "ttm_operating_expenses",
        "ttm_operating_income",
        "ttm_pretax_income",
        "ttm_tax_expense",
        "ttm_net_income",
        "ttm_ebitda",
        "ttm_eps",
        "ttm_operating_cash_flow",
        "ttm_capital_expenditures",
        "ttm_free_cash_flow",
        "ttm_depreciation_amortization",
        "cash_and_equivalents",
        "total_cash",
        "accounts_receivable",
        "total_current_assets",
        "property_plant_equipment",
        "total_assets",
        "accounts_payable",
        "short_term_debt",
        "total_current_liabilities",
        "long_term_debt",
        "total_debt",
        "total_liabilities",
        "shareholders_equity",
        "retained_earnings",
        "net_debt",
        "working_capital",
        "invested_capital",
        "gross_margin",
        "operating_margin",
        "net_margin",
        "ebitda_margin",
        "roe",
        "roa",
        "roic",
        "asset_turnover",
        "debt_to_equity",
        "current_ratio",
        "quick_ratio",
        "cash_ratio",
        "risk_free_rate",
        "historical_financials",
    ],
    "properties": {
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
        "company_name": {"type": "string", "description": "Full company name"},
        "sector": {"type": "string", "description": "GICS sector"},
        "industry": {"type": "string", "description": "GICS industry"},
        "extraction_timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp",
        },
        "data_confidence_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Confidence in extraction quality",
        },
        "current_price": {"type": "number", "description": "Current stock price"},
        "shares_outstanding": {"type": "number", "description": "Shares outstanding"},
        "market_cap": {"type": "number", "description": "Market capitalization"},
        "enterprise_value": {"type": "number", "description": "Enterprise value"},
        "ttm_revenue": {"type": "number", "description": "TTM revenue"},
        "ttm_cost_of_revenue": {"type": "number", "description": "TTM COGS"},
        "ttm_gross_profit": {"type": "number", "description": "TTM gross profit"},
        "ttm_operating_expenses": {"type": "number", "description": "TTM OpEx"},
        "ttm_operating_income": {"type": "number", "description": "TTM EBIT"},
        "ttm_interest_expense": {
            "type": ["number", "null"],
            "description": "TTM interest expense",
        },
        "ttm_pretax_income": {"type": "number", "description": "TTM pretax income"},
        "ttm_tax_expense": {"type": "number", "description": "TTM tax expense"},
        "ttm_net_income": {"type": "number", "description": "TTM net income"},
        "ttm_ebitda": {"type": "number", "description": "TTM EBITDA"},
        "ttm_eps": {"type": "number", "description": "TTM diluted EPS"},
        "ttm_operating_cash_flow": {"type": "number", "description": "TTM OCF"},
        "ttm_capital_expenditures": {"type": "number", "description": "TTM CapEx"},
        "ttm_free_cash_flow": {"type": "number", "description": "TTM FCF"},
        "ttm_depreciation_amortization": {"type": "number", "description": "TTM D&A"},
        "ttm_stock_based_compensation": {
            "type": ["number", "null"],
            "description": "TTM SBC",
        },
        "ttm_dividends_paid": {
            "type": ["number", "null"],
            "description": "TTM dividends",
        },
        "ttm_share_repurchases": {
            "type": ["number", "null"],
            "description": "TTM buybacks",
        },
        "cash_and_equivalents": {"type": "number", "description": "Cash balance"},
        "short_term_investments": {
            "type": ["number", "null"],
            "description": "ST investments",
        },
        "total_cash": {"type": "number", "description": "Total cash + ST investments"},
        "accounts_receivable": {"type": "number", "description": "A/R balance"},
        "inventory": {"type": ["number", "null"], "description": "Inventory"},
        "total_current_assets": {"type": "number", "description": "Current assets"},
        "property_plant_equipment": {"type": "number", "description": "PP&E net"},
        "goodwill": {"type": ["number", "null"], "description": "Goodwill"},
        "intangible_assets": {
            "type": ["number", "null"],
            "description": "Intangibles",
        },
        "total_assets": {"type": "number", "description": "Total assets"},
        "accounts_payable": {"type": "number", "description": "A/P balance"},
        "short_term_debt": {"type": "number", "description": "Current debt"},
        "total_current_liabilities": {
            "type": "number",
            "description": "Current liabilities",
        },
        "long_term_debt": {"type": "number", "description": "LT debt"},
        "total_debt": {"type": "number", "description": "Total debt"},
        "total_liabilities": {"type": "number", "description": "Total liabilities"},
        "shareholders_equity": {"type": "number", "description": "Equity"},
        "retained_earnings": {"type": "number", "description": "Retained earnings"},
        "net_debt": {"type": "number", "description": "Net debt = debt - cash"},
        "working_capital": {
            "type": "number",
            "description": "WC = CA - CL",
        },
        "invested_capital": {
            "type": "number",
            "description": "IC = equity + debt - cash",
        },
        "gross_margin": {"type": "number", "description": "Gross profit / Revenue"},
        "operating_margin": {"type": "number", "description": "EBIT / Revenue"},
        "net_margin": {"type": "number", "description": "Net income / Revenue"},
        "ebitda_margin": {"type": "number", "description": "EBITDA / Revenue"},
        "roe": {"type": "number", "description": "Net income / Equity"},
        "roa": {"type": "number", "description": "Net income / Assets"},
        "roic": {"type": "number", "description": "NOPAT / Invested capital"},
        "asset_turnover": {"type": "number", "description": "Revenue / Assets"},
        "inventory_turnover": {
            "type": ["number", "null"],
            "description": "COGS / Inventory",
        },
        "receivables_turnover": {
            "type": ["number", "null"],
            "description": "Revenue / A/R",
        },
        "debt_to_equity": {"type": "number", "description": "Debt / Equity"},
        "debt_to_ebitda": {
            "type": ["number", "null"],
            "description": "Debt / EBITDA",
        },
        "interest_coverage": {
            "type": ["number", "null"],
            "description": "EBIT / Interest",
        },
        "current_ratio": {"type": "number", "description": "CA / CL"},
        "quick_ratio": {"type": "number", "description": "(CA - Inv) / CL"},
        "cash_ratio": {"type": "number", "description": "Cash / CL"},
        "pe_ratio": {"type": ["number", "null"], "description": "Price / EPS"},
        "forward_pe": {"type": ["number", "null"], "description": "Price / Fwd EPS"},
        "peg_ratio": {"type": ["number", "null"], "description": "P/E / Growth"},
        "price_to_book": {"type": ["number", "null"], "description": "P/B ratio"},
        "price_to_sales": {"type": ["number", "null"], "description": "P/S ratio"},
        "ev_to_ebitda": {"type": ["number", "null"], "description": "EV/EBITDA"},
        "ev_to_revenue": {"type": ["number", "null"], "description": "EV/Revenue"},
        "fcf_yield": {"type": ["number", "null"], "description": "FCF / Market cap"},
        "earnings_yield": {"type": ["number", "null"], "description": "EPS / Price"},
        "revenue_growth_1y": {
            "type": ["number", "null"],
            "description": "1Y revenue growth",
        },
        "revenue_growth_3y_cagr": {
            "type": ["number", "null"],
            "description": "3Y revenue CAGR",
        },
        "revenue_growth_5y_cagr": {
            "type": ["number", "null"],
            "description": "5Y revenue CAGR",
        },
        "revenue_growth_10y_cagr": {
            "type": ["number", "null"],
            "description": "10Y revenue CAGR",
        },
        "earnings_growth_1y": {
            "type": ["number", "null"],
            "description": "1Y earnings growth",
        },
        "earnings_growth_3y_cagr": {
            "type": ["number", "null"],
            "description": "3Y earnings CAGR",
        },
        "earnings_growth_5y_cagr": {
            "type": ["number", "null"],
            "description": "5Y earnings CAGR",
        },
        "earnings_growth_10y_cagr": {
            "type": ["number", "null"],
            "description": "10Y earnings CAGR",
        },
        "fcf_growth_1y": {
            "type": ["number", "null"],
            "description": "1Y FCF growth",
        },
        "fcf_growth_3y_cagr": {
            "type": ["number", "null"],
            "description": "3Y FCF CAGR",
        },
        "fcf_growth_5y_cagr": {
            "type": ["number", "null"],
            "description": "5Y FCF CAGR",
        },
        "beta": {"type": ["number", "null"], "description": "5Y beta vs S&P 500"},
        "risk_free_rate": {"type": "number", "description": "10Y Treasury yield"},
        "equity_risk_premium": {
            "type": "number",
            "default": 0.05,
            "description": "ERP",
        },
        "dividend_per_share": {
            "type": ["number", "null"],
            "description": "Annual DPS",
        },
        "dividend_yield": {
            "type": ["number", "null"],
            "description": "Dividend yield",
        },
        "payout_ratio": {
            "type": ["number", "null"],
            "description": "Payout ratio",
        },
        "dividend_growth_5y": {
            "type": ["number", "null"],
            "description": "5Y div growth",
        },
        "years_of_dividend_growth": {
            "type": ["integer", "null"],
            "description": "Consecutive years",
        },
        "historical_financials": {
            "type": "array",
            "description": "10 years of annual data, most recent first",
            "items": {
                "type": "object",
                "required": [
                    "fiscal_year",
                    "revenue",
                    "gross_profit",
                    "operating_income",
                    "net_income",
                    "free_cash_flow",
                    "eps",
                    "depreciation_amortization",
                    "capital_expenditures",
                    "total_assets",
                    "total_liabilities",
                    "shareholders_equity",
                    "total_debt",
                    "cash_and_equivalents",
                ],
                "properties": {
                    "fiscal_year": {"type": "integer"},
                    "revenue": {"type": "number"},
                    "gross_profit": {"type": "number"},
                    "operating_income": {"type": "number"},
                    "net_income": {"type": "number"},
                    "free_cash_flow": {"type": "number"},
                    "eps": {"type": "number"},
                    "depreciation_amortization": {"type": "number"},
                    "capital_expenditures": {"type": "number"},
                    "total_assets": {"type": "number"},
                    "total_liabilities": {"type": "number"},
                    "shareholders_equity": {"type": "number"},
                    "total_debt": {"type": "number"},
                    "cash_and_equivalents": {"type": "number"},
                },
            },
        },
        "missing_fields": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Fields not found",
        },
        "estimated_fields": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Fields estimated by AI",
        },
        "data_anomalies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Data quality warnings",
        },
    },
}


SYSTEM_PROMPT = """You are a CFA Level 3 Charterholder and expert financial data analyst specializing in equity valuation.

YOUR MISSION:
Extract and normalize financial data from messy JSON structures into a standardized format suitable for DCF and Graham valuation models.

CRITICAL REQUIREMENTS:

1. DATA INTEGRITY
   - All monetary values MUST be in USD (no conversion needed - source is USD)
   - All ratios MUST be in decimal form (15% = 0.15, NOT 15)
   - All growth rates MUST be annualized and in decimal form
   - If data is MISSING, set to null - NEVER fabricate values
   - If data is INCONSISTENT, flag it in data_anomalies

2. FIELD NAME NORMALIZATION
   Handle common variations in source data:
   - "Revenue" = "Net Sales" = "Total Revenue" = "Sales" = "Operating Revenue"
   - "Net Income" = "Net Earnings" = "Profit" = "Net Income Common Stockholders"
   - "Operating Income" = "EBIT" = "Operating Profit" = "Income from Operations"
   - "Free Cash Flow" = "FCF" = "Levered Free Cash Flow"
   - "Shareholders Equity" = "Stockholders Equity" = "Total Equity" = "Total Stockholders Equity"
   - "Cost of Revenue" = "Cost of Goods Sold" = "COGS"
   - "Depreciation and Amortization" = "D&A" = "Depreciation" (when includes amortization)

3. TTM (TRAILING TWELVE MONTHS) CALCULATIONS
   For income statement and cash flow items:
   - Sum the most recent 4 quarters of data
   - If quarterly data unavailable, use the most recent annual data
   - For balance sheet items: use the most recent quarter's values (NOT summed)

4. GROWTH RATE CALCULATIONS
   Use the CAGR formula: ((End Value / Start Value) ^ (1/years)) - 1
   - 1Y Growth: (Current Year / Prior Year) - 1
   - 3Y CAGR: ((Year 0 / Year -3) ^ (1/3)) - 1
   - 5Y CAGR: ((Year 0 / Year -5) ^ (1/5)) - 1
   - 10Y CAGR: ((Year 0 / Year -10) ^ (1/10)) - 1

   IMPORTANT: For negative values, growth rate calculation may not be meaningful.
   Set to null if either start or end value is negative.

5. DATA PRIORITY (when conflicts exist between sources)
   1. financials_annual (SEC filings - most authoritative)
   2. yahoo_financials (comprehensive, reconciled with SEC)
   3. calculated_metrics (pre-computed, verified where possible)
   4. valuation section (Yahoo Finance API derived)
   5. market_data (real-time, may lag)

6. CONFIDENCE SCORING (0.0 to 1.0)
   Score based on:
   - 0.9-1.0: All key fields present, consistent across sources, recent data
   - 0.7-0.89: Most fields present, minor inconsistencies
   - 0.5-0.69: Several missing fields, some estimation required
   - 0.3-0.49: Significant missing data, heavy estimation
   - 0.0-0.29: Critical data missing, unreliable extraction

7. RISK-FREE RATE
   Use 0.045 (4.5%) as the default 10-year Treasury yield if not provided.

8. HANDLING SPECIAL CASES
   - For companies without inventory (service companies): set inventory and inventory_turnover to null
   - For companies without interest expense: set interest_expense and interest_coverage to null
   - For companies without dividends: set all dividend fields to null or 0

OUTPUT FORMAT:
Return a valid JSON object EXACTLY matching the StandardizedValuationInput schema.
NO markdown formatting. NO code blocks. NO explanatory text. ONLY pure JSON.
The response must start with { and end with }."""


USER_PROMPT_TEMPLATE = """
Analyze the following financial data for {ticker} ({company_name}) and extract standardized valuation inputs.

=== CURRENT MARKET DATA ===
Price: ${current_price:.2f}
Market Cap: ${market_cap:,.0f}
Data Collection Time: {collected_at}

=== COMPANY INFORMATION ===
{company_info_json}

=== MARKET DATA ===
{market_data_json}

=== VALUATION METRICS ===
{valuation_json}

=== CALCULATED METRICS ===
{calculated_metrics_json}

=== ANNUAL FINANCIALS (Last 10 Years - from SEC filings) ===
{financials_annual_json}

=== QUARTERLY INCOME STATEMENT (Last 4-8 Quarters for TTM) ===
{income_quarterly_json}

=== BALANCE SHEET (Most Recent) ===
{balance_sheet_json}

=== QUARTERLY CASH FLOW (Last 4-8 Quarters for TTM) ===
{cashflow_quarterly_json}

=== END OF DATA ===

EXTRACTION INSTRUCTIONS:

1. METADATA
   - ticker: "{ticker}"
   - company_name: Extract from company_info
   - sector: Extract from company_info
   - industry: Extract from company_info
   - extraction_timestamp: Use current UTC time in ISO 8601 format
   - data_confidence_score: Assess based on data completeness and consistency

2. MARKET POSITION
   - current_price: Use provided price (${current_price:.2f})
   - shares_outstanding: From shareholders section
   - market_cap: Use provided market cap
   - enterprise_value: market_cap + total_debt - total_cash

3. TTM METRICS
   - Sum last 4 quarters for income statement and cash flow items
   - Use most recent for balance sheet items

4. GROWTH RATES
   - Calculate CAGRs from historical data in financials_annual
   - Formula: ((End/Start)^(1/years)) - 1

5. RATIOS
   - Calculate all ratios from extracted values
   - Use decimal form (0.15 for 15%)

6. HISTORICAL FINANCIALS
   - Extract up to 10 years from financials_annual
   - Order by fiscal_year descending (most recent first)
   - Map fields carefully to the HistoricalFinancials schema

7. DATA QUALITY
   - List any fields that could not be extracted in missing_fields
   - List any fields that were estimated in estimated_fields
   - Note any anomalies or inconsistencies in data_anomalies

Return ONLY valid JSON matching this schema:
{schema_json}

Begin extraction now. Output ONLY the JSON object, starting with {{ and ending with }}."""


def get_schema_json() -> str:
    """Return the schema as a formatted JSON string for prompt inclusion."""
    return json.dumps(STANDARDIZED_VALUATION_INPUT_SCHEMA, indent=2)


def build_user_prompt(
    ticker: str,
    company_name: str,
    current_price: float,
    market_cap: float,
    collected_at: str,
    company_info_json: str,
    market_data_json: str,
    valuation_json: str,
    calculated_metrics_json: str,
    financials_annual_json: str,
    income_quarterly_json: str,
    balance_sheet_json: str,
    cashflow_quarterly_json: str,
) -> str:
    """
    Build the complete user prompt for financial data extraction.

    Args:
        ticker: Stock ticker symbol
        company_name: Full company name
        current_price: Current stock price
        market_cap: Market capitalization
        collected_at: Data collection timestamp
        company_info_json: Company information as JSON string
        market_data_json: Market data as JSON string
        valuation_json: Valuation metrics as JSON string
        calculated_metrics_json: Pre-calculated metrics as JSON string
        financials_annual_json: Annual financials as JSON string
        income_quarterly_json: Quarterly income statements as JSON string
        balance_sheet_json: Balance sheet as JSON string
        cashflow_quarterly_json: Quarterly cash flow statements as JSON string

    Returns:
        Formatted user prompt string ready for AI consumption.
    """
    return USER_PROMPT_TEMPLATE.format(
        ticker=ticker,
        company_name=company_name,
        current_price=current_price,
        market_cap=market_cap,
        collected_at=collected_at,
        company_info_json=company_info_json,
        market_data_json=market_data_json,
        valuation_json=valuation_json,
        calculated_metrics_json=calculated_metrics_json,
        financials_annual_json=financials_annual_json,
        income_quarterly_json=income_quarterly_json,
        balance_sheet_json=balance_sheet_json,
        cashflow_quarterly_json=cashflow_quarterly_json,
        schema_json=get_schema_json(),
    )
