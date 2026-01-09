"""
Flexible AI extraction prompt - Let AI decide what to extract.

Instead of forcing a rigid schema, we give the AI the raw data and let it:
1. Find ALL available financial data
2. Map fields intelligently based on what exists
3. Return everything it can extract
4. Flag what's missing or estimated
"""

FLEXIBLE_SYSTEM_PROMPT = """You are a CFA-certified financial data analyst. Your job is to extract ALL available financial data from the provided JSON and return it in a standardized format.

CORE PRINCIPLES:
1. EXTRACT EVERYTHING - Find all financial metrics, ratios, and data points available
2. USE WHAT EXISTS - Don't return null if data exists under a different field name
3. CALCULATE WHEN POSSIBLE - If TTM data isn't explicit, sum last 4 quarters
4. BE FLEXIBLE - Field names vary (Revenue = Net Sales = Total Revenue)
5. REPORT HONESTLY - List what you found, what's missing, what you calculated

FIELD NAMING CONVENTION:
All source data uses **Title Case with Spaces** format. Examples:
- "Gross Profit" (NOT GrossProfit or gross_profit)
- "Cost Of Revenue" (NOT CostOfRevenue)
- "Operating Income" (NOT OperatingIncome)
- "Free Cash Flow" (NOT FreeCashFlow)

FIELD MAPPING GUIDE (source field -> output field):
INCOME STATEMENT:
- "Total Revenue" or "Operating Revenue" -> revenue
- "Cost Of Revenue" -> cost_of_revenue
- "Gross Profit" -> gross_profit
- "Operating Expense" -> operating_expenses
- "Operating Income" or "EBIT" -> operating_income
- "Pretax Income" -> pretax_income
- "Tax Provision" -> tax_expense
- "Net Income" or "Net Income From Continuing Operation Net Minority Interest" -> net_income
- "EBITDA" or "Normalized EBITDA" -> ebitda
- "Diluted EPS" or "Basic EPS" -> eps
- "Interest Expense Non Operating" -> interest_expense

CASH FLOW STATEMENT:
- "Operating Cash Flow" or "Cash Flow From Continuing Operating Activities" -> operating_cash_flow
- "Capital Expenditure" -> capital_expenditures (use absolute value)
- "Free Cash Flow" -> free_cash_flow
- "Depreciation And Amortization" or "Reconciled Depreciation" -> depreciation_amortization
- "Stock Based Compensation" -> stock_based_compensation
- "Common Stock Dividend Paid" or "Cash Dividends Paid" -> dividends_paid
- "Repurchase Of Capital Stock" or "Common Stock Payments" -> share_repurchases

BALANCE SHEET:
- "Cash And Cash Equivalents" -> cash_and_equivalents
- "Cash Cash Equivalents And Short Term Investments" -> total_cash
- "Total Assets" -> total_assets
- "Total Liabilities Net Minority Interest" -> total_liabilities
- "Stockholders Equity" -> shareholders_equity
- "Total Debt" -> total_debt
- "Long Term Debt" -> long_term_debt
- "Current Debt" -> short_term_debt
- "Current Assets" -> total_current_assets
- "Current Liabilities" -> total_current_liabilities
- "Accounts Receivable" or "Receivables" -> accounts_receivable
- "Inventory" -> inventory
- "Accounts Payable" -> accounts_payable
- "Net PPE" or "Gross PPE" -> property_plant_equipment
- "Goodwill" -> goodwill
- "Goodwill And Other Intangible Assets" -> intangible_assets
- "Retained Earnings" -> retained_earnings
- "Working Capital" -> working_capital
- "Net Debt" -> net_debt
- "Invested Capital" -> invested_capital

CRITICAL TTM INCOME STATEMENT FIELDS (must extract):
- cost_of_revenue: Sum last 4 quarters of "Cost Of Revenue"
- gross_profit: Sum last 4 quarters of "Gross Profit"
- operating_expenses: Sum last 4 quarters of "Operating Expense"
These are KEY financial metrics - search in income_statement_quarterly first, then income_statement_annual!

DATA PRIORITY (when conflicts exist):
1. calculated_metrics - Pre-computed, verified values (USE THESE FIRST!)
2. valuation section - Yahoo Finance derived metrics
3. yahoo_financials - Quarterly/annual statements
4. financials_annual - SEC filing data
5. market_data - Real-time data

TTM CALCULATIONS (priority order):
1. BEST: Sum the most recent 4 quarters for income statement and cash flow items
2. FALLBACK: If quarterly data unavailable, use most recent ANNUAL data instead
3. Balance sheet: Use most recent quarter (NOT summed), or most recent annual

DATA SOURCE PRIORITY FOR TTM:
- income_statement_quarterly (sum 4 quarters) > income_statement_annual (most recent year)
- cash_flow_quarterly (sum 4 quarters) > cash_flow_annual (most recent year)
- balance_sheet_quarterly (latest) > balance_sheet_annual (latest)

IMPORTANT: Some stocks only have annual data. That's OK - use annual values directly!

GROWTH RATES:
- 1Y Growth: (Current / Prior) - 1
- CAGR Formula: ((End / Start) ^ (1/years)) - 1
- Set to null if negative values make calculation meaningless

OUTPUT: Return valid JSON matching the schema provided. Include ALL data you can find."""


FLEXIBLE_USER_PROMPT = """
Extract ALL financial data for {ticker} ({company_name}).

Current Price: ${current_price:.2f}
Market Cap: ${market_cap:,.0f}
Data Date: {collected_at}

=== SOURCE DATA ===

1. CALCULATED METRICS (pre-computed - use these first!):
{calculated_metrics_json}

2. VALUATION SECTION (Yahoo Finance):
{valuation_json}

3. MARKET DATA:
{market_data_json}

4. COMPANY INFO:
{company_info_json}

5. QUARTERLY CASH FLOW (for TTM - sum last 4 quarters):
{cashflow_quarterly_json}

6. QUARTERLY INCOME STATEMENT (for TTM - SUM LAST 4 QUARTERS for all items):
CRITICAL: Extract these TTM values by summing the 4 most recent quarters:
- "Total Revenue" -> revenue
- "Cost Of Revenue" -> cost_of_revenue
- "Gross Profit" -> gross_profit
- "Operating Expense" -> operating_expenses
- "Operating Income" -> operating_income
- "Net Income" -> net_income
{income_quarterly_json}

7. ANNUAL INCOME STATEMENT (use if quarterly is missing/incomplete):
If quarterly data is unavailable, use the MOST RECENT YEAR values directly.
These have the same fields: "Gross Profit", "Cost Of Revenue", "Operating Expense", etc.
{income_annual_json}

8. QUARTERLY BALANCE SHEET (use most recent - DO NOT sum):
{balance_sheet_json}

9. ANNUAL FINANCIALS (SEC filings - for historical/growth):
{financials_annual_json}

=== EXTRACTION INSTRUCTIONS ===

Return a JSON object with these sections:

{{
  "ticker": "{ticker}",
  "company_name": "...",
  "extraction_timestamp": "ISO timestamp",
  "data_confidence_score": 0.0-1.0,

  "metadata": {{
    "sector": "...",
    "industry": "...",
    "currency": "USD"
  }},

  "market_position": {{
    "current_price": ...,
    "shares_outstanding": ...,
    "market_cap": ...,
    "enterprise_value": ...
  }},

  "ttm_income_statement": {{
    "revenue": ...,
    "cost_of_revenue": ...,
    "gross_profit": ...,
    "operating_expenses": ...,
    "operating_income": ...,
    "interest_expense": null or ...,
    "pretax_income": ...,
    "tax_expense": ...,
    "net_income": ...,
    "ebitda": ...,
    "eps": ...
  }},

  "ttm_cash_flow": {{
    "operating_cash_flow": ...,
    "capital_expenditures": ...,
    "free_cash_flow": ...,
    "depreciation_amortization": ...,
    "stock_based_compensation": ...,
    "dividends_paid": ...,
    "share_repurchases": ...
  }},

  "balance_sheet": {{
    "cash_and_equivalents": ...,
    "short_term_investments": ...,
    "total_cash": ...,
    "accounts_receivable": ...,
    "inventory": ...,
    "total_current_assets": ...,
    "property_plant_equipment": ...,
    "goodwill": ...,
    "intangible_assets": ...,
    "total_assets": ...,
    "accounts_payable": ...,
    "short_term_debt": ...,
    "total_current_liabilities": ...,
    "long_term_debt": ...,
    "total_debt": ...,
    "total_liabilities": ...,
    "shareholders_equity": ...,
    "retained_earnings": ...
  }},

  "calculated_metrics": {{
    "net_debt": ...,
    "working_capital": ...,
    "invested_capital": ...
  }},

  "profitability_ratios": {{
    "gross_margin": ...,
    "operating_margin": ...,
    "net_margin": ...,
    "ebitda_margin": ...,
    "roe": ...,
    "roa": ...,
    "roic": ...
  }},

  "efficiency_ratios": {{
    "asset_turnover": ...,
    "inventory_turnover": ...,
    "receivables_turnover": ...
  }},

  "leverage_ratios": {{
    "debt_to_equity": ...,
    "debt_to_ebitda": ...,
    "interest_coverage": ...
  }},

  "liquidity_ratios": {{
    "current_ratio": ...,
    "quick_ratio": ...,
    "cash_ratio": ...
  }},

  "valuation_multiples": {{
    "pe_ratio": ...,
    "forward_pe": ...,
    "peg_ratio": ...,
    "price_to_book": ...,
    "price_to_sales": ...,
    "ev_to_ebitda": ...,
    "ev_to_revenue": ...,
    "fcf_yield": ...,
    "earnings_yield": ...
  }},

  "growth_rates": {{
    "revenue_growth_1y": ...,
    "revenue_growth_3y_cagr": ...,
    "revenue_growth_5y_cagr": ...,
    "revenue_growth_10y_cagr": ...,
    "earnings_growth_1y": ...,
    "earnings_growth_5y_cagr": ...,
    "fcf_growth_1y": ...,
    "fcf_growth_5y_cagr": ...
  }},

  "risk_parameters": {{
    "beta": ...,
    "risk_free_rate": 0.045
  }},

  "dividends": {{
    "dividend_per_share": ...,
    "dividend_yield": ...,
    "payout_ratio": ...,
    "years_of_dividend_growth": ...
  }},

  "historical_financials": [
    {{
      "fiscal_year": 2024,
      "revenue": ...,
      "gross_profit": ...,
      "operating_income": ...,
      "net_income": ...,
      "eps": ...,
      "free_cash_flow": ...,
      "operating_cash_flow": ...,
      "capital_expenditures": ...,
      "depreciation_amortization": ...,
      "total_assets": ...,
      "total_liabilities": ...,
      "shareholders_equity": ...,
      "total_debt": ...,
      "cash_and_equivalents": ...
    }}
    // ... up to 10 years
  ],

  "data_quality": {{
    "fields_found": ["list of fields successfully extracted"],
    "fields_missing": ["list of fields not found in source"],
    "fields_calculated": ["list of fields you calculated (e.g., TTM sums)"],
    "fields_estimated": ["list of fields you estimated"],
    "data_anomalies": ["any inconsistencies or warnings"],
    "confidence_notes": "explanation of confidence score"
  }}
}}

IMPORTANT:
- Use null for missing fields, never make up values
- All ratios in decimal form (15% = 0.15)
- All monetary values in USD
- Extract from calculated_metrics FIRST if available
- Sum quarterly data for TTM when available
- Include ALL historical years you can find (up to 10)

Return ONLY valid JSON. No markdown, no explanation, just the JSON object."""


def build_flexible_prompt(
    ticker: str,
    company_name: str,
    current_price: float,
    market_cap: float,
    collected_at: str,
    calculated_metrics_json: str,
    valuation_json: str,
    market_data_json: str,
    company_info_json: str,
    cashflow_quarterly_json: str,
    income_quarterly_json: str,
    income_annual_json: str,
    balance_sheet_json: str,
    financials_annual_json: str,
) -> str:
    """Build the flexible extraction prompt."""
    return FLEXIBLE_USER_PROMPT.format(
        ticker=ticker,
        company_name=company_name,
        current_price=current_price,
        market_cap=market_cap,
        collected_at=collected_at,
        calculated_metrics_json=calculated_metrics_json,
        valuation_json=valuation_json,
        market_data_json=market_data_json,
        company_info_json=company_info_json,
        cashflow_quarterly_json=cashflow_quarterly_json,
        income_quarterly_json=income_quarterly_json,
        income_annual_json=income_annual_json,
        balance_sheet_json=balance_sheet_json,
        financials_annual_json=financials_annual_json,
    )
