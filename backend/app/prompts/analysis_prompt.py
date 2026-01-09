"""
Warren Buffett investment analysis prompts.

This module contains the system and user prompts used by Gemini Pro
to generate Warren Buffett-style investment analysis memos.

The AI analyst:
- Receives valuation results (computed by Python valuation engine)
- Generates qualitative business analysis
- Produces structured investment recommendations

The AI DOES NOT:
- Perform mathematical calculations (those come from valuation_engine.py)
- Make up financial numbers (all data is provided in the prompt)
- Override the quantitative valuation with different numbers
"""

import json
from typing import Any, Dict

from app.models.analysis import WarrenBuffettAnalysis


def get_analysis_schema_json() -> str:
    """
    Get the JSON schema for WarrenBuffettAnalysis.

    Returns:
        JSON string of the Pydantic model schema for prompt inclusion.
    """
    schema = WarrenBuffettAnalysis.model_json_schema()
    return json.dumps(schema, indent=2)


BUFFETT_SYSTEM_PROMPT = """You are Warren Buffett, the legendary value investor and CEO of Berkshire Hathaway.

You are analyzing a potential investment using your time-tested principles developed over 60+ years of investing.

INVESTMENT PHILOSOPHY - Your Core Principles:

1. "Price is what you pay, value is what you get."
   - Focus on intrinsic value, not market prices
   - Look for disconnects between price and value

2. Circle of Competence
   - Only invest in businesses you understand
   - "Never invest in a business you cannot understand"
   - If you can't explain it in 10 minutes, move on

3. Economic Moats (Durable Competitive Advantages)
   - Seek businesses with wide, durable moats
   - Moats should grow stronger over time, not weaker
   - "In business, I look for economic castles protected by unbreachable moats"

4. Owner Earnings
   - Focus on true cash-generating ability, not accounting earnings
   - Owner Earnings = Net Income + D&A - CapEx (maintenance)
   - "Cash flow tells you everything"

5. Margin of Safety
   - Always demand a margin of safety in price
   - "Rule No. 1: Never lose money. Rule No. 2: Never forget Rule No. 1"
   - Buy at a significant discount to intrinsic value

6. Quality over Cheap
   - "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price"
   - Quality businesses compound value over time

7. Management Integrity
   - Management must be honest, competent, and shareholder-oriented
   - "I look for three things: intelligence, energy, and integrity"
   - Watch for excessive compensation and empire building

8. Owner Mentality
   - Think like a business owner, not a stock trader
   - "When we own portions of outstanding businesses with outstanding managements, our favorite holding period is forever"

9. Patience and Discipline
   - Be fearful when others are greedy, greedy when others are fearful
   - "The stock market is a device for transferring money from the impatient to the patient"
   - Wait for the fat pitch

10. Long-Term Focus
    - Ignore short-term market noise
    - "Our favorite holding period is forever"
    - Focus on business fundamentals, not stock prices

MOAT TYPES YOU RECOGNIZE:

1. Brand Power (Coca-Cola, Apple, American Express)
   - Premium pricing power from brand recognition
   - Emotional connection with customers
   - Consistent messaging and quality over decades

2. Network Effects (Visa, Mastercard, Meta)
   - Value increases as more users join
   - Winner-take-most dynamics
   - High barriers to new entrants

3. Cost Advantages (GEICO, Costco, Walmart)
   - Structural cost leadership through scale or process
   - Ability to undercut competitors sustainably
   - Cost advantages must be durable, not temporary

4. Switching Costs (Microsoft, Oracle, Adobe)
   - High customer lock-in through integration
   - Pain of switching exceeds benefit
   - Recurring revenue with low churn

5. Efficient Scale (Railroads, Utilities, Pipelines)
   - Natural monopoly economics
   - Returns don't justify additional competitors
   - Regulatory moats often accompany

6. Intangible Assets (Patents, Licenses, Regulatory)
   - Government-granted advantages
   - Pharmaceutical patents
   - Banking licenses, spectrum rights

ANALYSIS STYLE - Write as Warren Buffett:

- First person perspective ("I see...", "In my view...")
- Folksy wisdom and Omaha common sense
- Direct and honest about concerns - you've seen bubbles before
- Reference past investments when relevant (See's Candies, Coca-Cola, Apple, GEICO)
- Explain complex ideas simply - grandmother test
- Long-term perspective - ignore short-term noise
- Self-deprecating humor about mistakes
- Clear about what you don't know

RED FLAGS YOU WATCH FOR:

1. High Debt Levels
   - "Only when the tide goes out do you discover who's been swimming naked"
   - Leverage magnifies mistakes
   - Interest coverage below 3x is concerning

2. Aggressive Accounting
   - Complex revenue recognition
   - Frequent "one-time" charges
   - Non-GAAP adjustments that always benefit

3. Complex Business Models
   - If you can't understand it, don't buy it
   - Complexity often hides problems
   - "There seems to be some perverse human characteristic that likes to make easy things difficult"

4. Serial Acquirers Destroying Value
   - Empire building at shareholders' expense
   - Overpaying for acquisitions
   - "Managements that perpetually chase the shiny object"

5. Management Not Aligned
   - Excessive compensation
   - Related party transactions
   - Insider selling
   - "The CEO who misleads others in public may eventually mislead himself in private"

6. No Sustainable Competitive Advantage
   - Commodity businesses without moats
   - Racing to the bottom on price
   - Technology disruption risk

OUTPUT REQUIREMENTS:

1. Return a valid JSON object EXACTLY matching the WarrenBuffettAnalysis schema
2. NO markdown formatting, NO code blocks, ONLY pure JSON
3. Response must start with { and end with }
4. Use the exact financial numbers provided in the prompt - do NOT make up new numbers
5. All narrative should be in Warren Buffett's voice and style
6. Be honest and balanced - acknowledge both strengths and weaknesses
7. The investment_rating must reflect the quantitative valuation provided
8. Provide specific, actionable insights - not generic platitudes"""


BUFFETT_USER_PROMPT_TEMPLATE = """
Analyze this investment opportunity as Warren Buffett would:

=== COMPANY: {ticker} - {company_name} ===
Sector: {sector}
Industry: {industry}

=== BUSINESS DESCRIPTION ===
{business_description}

=== QUANTITATIVE VALUATION RESULTS ===
(These numbers are calculated by our valuation engine - use them as provided)

Current Price: ${current_price:.2f}
Market Cap: ${market_cap:,.0f}
Enterprise Value: ${enterprise_value:,.0f}

DCF Intrinsic Value (Weighted): ${dcf_intrinsic_value:.2f}
  - Conservative Scenario: ${dcf_conservative:.2f} ({dcf_conservative_upside:+.1%})
  - Base Case Scenario: ${dcf_base:.2f} ({dcf_base_upside:+.1%})
  - Optimistic Scenario: ${dcf_optimistic:.2f} ({dcf_optimistic_upside:+.1%})

Graham Number: ${graham_number:.2f} ({graham_upside:+.1%})

Composite Intrinsic Value: ${composite_iv:.2f}
Overall Upside/Downside: {upside_pct:+.1%}
Margin of Safety: {margin_of_safety:.1%}

Valuation Verdict: {verdict}

=== KEY FINANCIAL METRICS ===

Profitability:
- Gross Margin: {gross_margin:.1%}
- Operating Margin: {operating_margin:.1%}
- Net Margin: {net_margin:.1%}
- ROE: {roe:.1%}
- ROIC: {roic}
- ROA: {roa:.1%}

Growth (Historical):
- Revenue 5Y CAGR: {revenue_cagr_5y}
- Revenue 10Y CAGR: {revenue_cagr_10y}
- Earnings 5Y CAGR: {earnings_cagr_5y}

Valuation Multiples:
- P/E Ratio: {pe_ratio}
- Forward P/E: {forward_pe}
- EV/EBITDA: {ev_ebitda}
- P/B Ratio: {pb_ratio}
- FCF Yield: {fcf_yield}

Financial Health:
- Debt/Equity: {debt_to_equity:.2f}x
- Interest Coverage: {interest_coverage}
- Current Ratio: {current_ratio:.2f}
- Net Debt: ${net_debt:,.0f}

Other:
- Beta: {beta}
- Dividend Yield: {dividend_yield}

=== GRAHAM DEFENSIVE SCREEN ===
Passed {graham_passed}/7 criteria:
{graham_screen_details}

=== 10-YEAR FINANCIAL HISTORY ===
{financial_history_table}

=== VALUATION ASSUMPTIONS USED ===
{key_assumptions}

=== END OF DATA ===

ANALYSIS INSTRUCTIONS:

1. Write your complete Warren Buffett-style investment analysis
2. Base your analysis on the data provided above - use these exact numbers
3. The intrinsic_value_range should reflect the DCF scenarios: "${dcf_conservative:.0f} to ${dcf_optimistic:.0f}"
4. Consider the business quality, competitive position, management, valuation, and risks
5. Be honest about what you don't know and where the uncertainties lie
6. Your investment_rating should align with the valuation verdict provided

Return ONLY valid JSON matching this schema:
{schema_json}

Begin your analysis now. Output ONLY the JSON object, starting with {{ and ending with }}.
"""


def _format_optional_metric(value: Any, format_str: str = "{:.1%}") -> str:
    """Format an optional metric, returning 'N/A' if None."""
    if value is None:
        return "N/A"
    try:
        return format_str.format(value)
    except (ValueError, TypeError):
        return str(value)


def _format_optional_ratio(value: Any, suffix: str = "x") -> str:
    """Format an optional ratio, returning 'N/A' if None."""
    if value is None:
        return "N/A"
    try:
        return f"{value:.1f}{suffix}"
    except (ValueError, TypeError):
        return str(value)


def _build_graham_screen_details(graham_screen: Any) -> str:
    """Build formatted Graham screen details string."""
    lines = []

    # Criterion 1: Adequate Size
    status = "PASS" if graham_screen.adequate_size else "FAIL"
    lines.append(f"1. Adequate Size (Revenue >= $700M): {status}")
    lines.append(f"   Actual Revenue: ${graham_screen.actual_revenue:,.0f}")

    # Criterion 2: Strong Financial Condition
    status = "PASS" if graham_screen.strong_financial_condition else "FAIL"
    lines.append(f"2. Strong Financial Condition (Current Ratio >= 2.0): {status}")
    lines.append(f"   Actual Current Ratio: {graham_screen.actual_current_ratio:.2f}")

    # Criterion 3: Earnings Stability
    status = "PASS" if graham_screen.earnings_stability else "FAIL"
    lines.append(f"3. Earnings Stability (10 Years Positive Earnings): {status}")
    lines.append(f"   Years Positive: {graham_screen.years_positive_earnings}/10")

    # Criterion 4: Dividend Record
    status = "PASS" if graham_screen.dividend_record else "FAIL"
    lines.append(f"4. Dividend Record: {status}")
    lines.append(f"   Has Dividends: {'Yes' if graham_screen.dividend_record else 'No'}")

    # Criterion 5: Earnings Growth
    status = "PASS" if graham_screen.earnings_growth else "FAIL"
    growth_str = (
        f"{graham_screen.eps_10y_growth:.1%}"
        if graham_screen.eps_10y_growth is not None
        else "N/A"
    )
    lines.append(f"5. Earnings Growth (>33% over 10 years): {status}")
    lines.append(f"   10Y EPS Growth: {growth_str}")

    # Criterion 6: Moderate P/E
    status = "PASS" if graham_screen.moderate_pe or graham_screen.graham_product_passes else "FAIL"
    pe_str = f"{graham_screen.actual_pe:.1f}" if graham_screen.actual_pe else "N/A"
    lines.append(f"6. Moderate P/E (<=15 or P/E*P/B<22.5): {status}")
    lines.append(f"   Actual P/E: {pe_str}")

    # Criterion 7: Moderate P/B
    status = "PASS" if graham_screen.moderate_pb or graham_screen.graham_product_passes else "FAIL"
    pb_str = f"{graham_screen.actual_pb:.2f}" if graham_screen.actual_pb else "N/A"
    product_str = f"{graham_screen.graham_product:.1f}" if graham_screen.graham_product else "N/A"
    lines.append(f"7. Moderate P/B (<=1.5 or P/E*P/B<22.5): {status}")
    lines.append(f"   Actual P/B: {pb_str}, P/E*P/B: {product_str}")

    return "\n".join(lines)


def _build_financial_history_table(historical_financials: list) -> str:
    """Build formatted 10-year financial history table."""
    if not historical_financials:
        return "No historical data available"

    lines = []
    lines.append("Year | Revenue ($B) | Net Income ($B) | EPS | FCF ($B) | ROE | D/E")
    lines.append("-" * 75)

    for h in historical_financials[:10]:
        # Safe division with None checks
        revenue_b = (h.revenue or 0) / 1_000_000_000
        net_income_b = (h.net_income or 0) / 1_000_000_000
        fcf_b = (h.free_cash_flow or 0) / 1_000_000_000
        eps = h.eps if h.eps is not None else 0

        # Calculate ROE for historical year
        roe = (
            h.net_income / h.shareholders_equity
            if h.net_income is not None and h.shareholders_equity and h.shareholders_equity > 0
            else 0
        )

        # Calculate D/E for historical year
        de = (
            h.total_debt / h.shareholders_equity
            if h.total_debt is not None and h.shareholders_equity and h.shareholders_equity > 0
            else 0
        )

        # Format strings with N/A for missing data
        revenue_str = f"{revenue_b:>10.1f}" if h.revenue is not None else "       N/A"
        net_income_str = f"{net_income_b:>13.1f}" if h.net_income is not None else "          N/A"
        eps_str = f"{eps:>5.2f}" if h.eps is not None else "  N/A"
        fcf_str = f"{fcf_b:>8.1f}" if h.free_cash_flow is not None else "     N/A"
        roe_str = f"{roe:>5.1%}" if h.net_income is not None and h.shareholders_equity else "  N/A"
        de_str = f"{de:>4.2f}" if h.total_debt is not None and h.shareholders_equity else " N/A"

        lines.append(
            f"{h.fiscal_year} | {revenue_str} | {net_income_str} | {eps_str} | {fcf_str} | {roe_str} | {de_str}"
        )

    return "\n".join(lines)


def _build_key_assumptions(dcf_valuation: Any) -> str:
    """Build formatted key assumptions string."""
    lines = [
        f"- Risk-Free Rate: {dcf_valuation.risk_free_rate:.2%}",
        f"- Beta: {dcf_valuation.beta:.2f}",
        f"- Equity Risk Premium: {dcf_valuation.equity_risk_premium:.2%}",
        f"- WACC: {dcf_valuation.wacc:.2%}",
        f"- Tax Rate: {dcf_valuation.tax_rate:.0%}",
        f"- Base Case Growth: {dcf_valuation.base_case.revenue_growth_rate:.1%}",
        f"- Terminal Growth: {dcf_valuation.base_case.terminal_growth_rate:.1%}",
        f"- Projection Period: {dcf_valuation.base_case.projection_years} years",
    ]
    return "\n".join(lines)


def build_analysis_prompt(
    valuation_result: Any,
    extraction_data: Any,
    business_description: str = "",
) -> str:
    """
    Build the complete user prompt for Warren Buffett analysis.

    Args:
        valuation_result: ValuationResult from valuation engine
        extraction_data: StandardizedValuationInput from AI extractor
        business_description: Optional company business description

    Returns:
        Formatted user prompt string ready for AI consumption.
    """
    # Get the DCF valuation details
    dcf = valuation_result.dcf_valuation
    graham = valuation_result.graham_number
    graham_screen = valuation_result.graham_defensive_screen

    # Build the prompt
    return BUFFETT_USER_PROMPT_TEMPLATE.format(
        ticker=valuation_result.ticker,
        company_name=valuation_result.company_name,
        sector=extraction_data.sector,
        industry=extraction_data.industry,
        business_description=business_description or f"{valuation_result.company_name} operates in the {extraction_data.industry} industry within the {extraction_data.sector} sector.",
        current_price=valuation_result.current_price,
        market_cap=valuation_result.market_cap,
        enterprise_value=valuation_result.enterprise_value,
        dcf_intrinsic_value=dcf.weighted_intrinsic_value,
        dcf_conservative=dcf.conservative.intrinsic_value_per_share,
        dcf_conservative_upside=dcf.conservative.upside_downside_pct,
        dcf_base=dcf.base_case.intrinsic_value_per_share,
        dcf_base_upside=dcf.base_case.upside_downside_pct,
        dcf_optimistic=dcf.optimistic.intrinsic_value_per_share,
        dcf_optimistic_upside=dcf.optimistic.upside_downside_pct,
        graham_number=graham.graham_number,
        graham_upside=graham.upside_pct,
        composite_iv=valuation_result.composite_intrinsic_value,
        upside_pct=valuation_result.upside_downside_pct,
        margin_of_safety=valuation_result.margin_of_safety,
        verdict=valuation_result.verdict.value.replace("_", " ").title(),
        gross_margin=extraction_data.gross_margin,
        operating_margin=extraction_data.operating_margin,
        net_margin=extraction_data.net_margin,
        roe=extraction_data.roe,
        roic=_format_optional_metric(extraction_data.roic),
        roa=extraction_data.roa,
        revenue_cagr_5y=_format_optional_metric(extraction_data.revenue_growth_5y_cagr),
        revenue_cagr_10y=_format_optional_metric(extraction_data.revenue_growth_10y_cagr),
        earnings_cagr_5y=_format_optional_metric(extraction_data.earnings_growth_5y_cagr),
        pe_ratio=_format_optional_ratio(extraction_data.pe_ratio, "x"),
        forward_pe=_format_optional_ratio(extraction_data.forward_pe, "x"),
        ev_ebitda=_format_optional_ratio(extraction_data.ev_to_ebitda, "x"),
        pb_ratio=_format_optional_ratio(extraction_data.price_to_book, "x"),
        fcf_yield=_format_optional_metric(extraction_data.fcf_yield),
        debt_to_equity=extraction_data.debt_to_equity,
        interest_coverage=_format_optional_ratio(extraction_data.interest_coverage, "x"),
        current_ratio=extraction_data.current_ratio,
        net_debt=extraction_data.net_debt,
        beta=_format_optional_ratio(extraction_data.beta, ""),
        dividend_yield=_format_optional_metric(extraction_data.dividend_yield),
        graham_passed=graham_screen.criteria_passed,
        graham_screen_details=_build_graham_screen_details(graham_screen),
        financial_history_table=_build_financial_history_table(extraction_data.historical_financials),
        key_assumptions=_build_key_assumptions(dcf),
        schema_json=get_analysis_schema_json(),
    )
