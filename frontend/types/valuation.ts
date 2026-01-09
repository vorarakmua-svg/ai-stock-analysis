/**
 * Valuation TypeScript Types
 * Matching the backend valuation models from Phase 5
 */

/**
 * Valuation Verdict - Assessment of stock's value relative to price
 */
export type ValuationVerdict =
  | "significantly_undervalued"  // >40% upside
  | "undervalued"                // 15-40% upside
  | "fairly_valued"              // -15% to +15%
  | "overvalued"                 // 15-40% downside
  | "significantly_overvalued";  // >40% downside

/**
 * DCF Scenario - Single scenario calculation for DCF valuation
 */
export interface DCFScenario {
  /** Scenario name: "conservative", "base_case", "optimistic" */
  scenario_name: string;

  /** Revenue growth rate assumption */
  revenue_growth_rate: number;

  /** Operating margin assumption */
  operating_margin_assumption: number;

  /** Terminal growth rate for Gordon Growth Model */
  terminal_growth_rate: number;

  /** Weighted Average Cost of Capital */
  wacc: number;

  /** Number of projection years (typically 5) */
  projection_years: number;

  /** Projected revenue for each year */
  projected_revenue: number[];

  /** Projected EBIT for each year */
  projected_ebit: number[];

  /** Projected NOPAT for each year */
  projected_nopat: number[];

  /** Projected free cash flow for each year */
  projected_fcf: number[];

  /** Terminal year free cash flow */
  terminal_fcf: number;

  /** Terminal value (Gordon Growth Model) */
  terminal_value: number;

  /** Present value of explicit period cash flows */
  pv_explicit_period: number;

  /** Present value of terminal value */
  pv_terminal_value: number;

  /** Calculated enterprise value */
  enterprise_value: number;

  /** Calculated equity value (EV - Net Debt) */
  equity_value: number;

  /** Intrinsic value per share */
  intrinsic_value_per_share: number;

  /** Current market price for comparison */
  current_price: number;

  /** Upside/downside percentage vs current price */
  upside_downside_pct: number;
}

/**
 * DCF Valuation - Complete DCF analysis with three scenarios
 */
export interface DCFValuation {
  /** Timestamp of calculation */
  calculation_timestamp: string;

  /** Valuation methodology description */
  methodology: string;

  /** Risk-free rate (10Y Treasury) */
  risk_free_rate: number;

  /** Stock beta (systematic risk) */
  beta: number;

  /** Equity risk premium */
  equity_risk_premium: number;

  /** Cost of equity (CAPM: Rf + Beta * ERP) */
  cost_of_equity: number;

  /** Pre-tax cost of debt */
  cost_of_debt_pretax: number;

  /** Effective tax rate */
  tax_rate: number;

  /** After-tax cost of debt */
  cost_of_debt_aftertax: number;

  /** Debt weight in capital structure */
  debt_weight: number;

  /** Equity weight in capital structure */
  equity_weight: number;

  /** Weighted Average Cost of Capital */
  wacc: number;

  /** Conservative scenario (lower growth assumptions) */
  conservative: DCFScenario;

  /** Base case scenario (consensus estimates) */
  base_case: DCFScenario;

  /** Optimistic scenario (higher growth assumptions) */
  optimistic: DCFScenario;

  /** Probability weights for each scenario */
  scenario_weights: Record<string, number>;

  /** Probability-weighted intrinsic value */
  weighted_intrinsic_value: number;

  /** Sensitivity analysis for WACC changes */
  sensitivity_to_wacc: Record<string, number>;

  /** Sensitivity analysis for growth changes */
  sensitivity_to_growth: Record<string, number>;
}

/**
 * Graham Number - Benjamin Graham's intrinsic value formula
 */
export interface GrahamNumber {
  /** Methodology description */
  methodology: string;

  /** Trailing twelve months EPS */
  eps_ttm: number;

  /** Book value per share */
  book_value_per_share: number;

  /** Graham multiplier (22.5 = 15 * 1.5) */
  graham_multiplier: number;

  /** Calculated Graham Number: sqrt(22.5 * EPS * BVPS) */
  graham_number: number;

  /** Current market price */
  current_price: number;

  /** Upside/downside percentage vs Graham Number */
  upside_pct: number;

  /** Normalized EPS (optional) */
  normalized_eps: number | null;

  /** Earnings power value (optional) */
  earnings_power_value: number | null;
}

/**
 * Graham Defensive Criteria - 7 criteria for defensive investors
 */
export interface GrahamDefensiveCriteria {
  /** Criterion 1: Adequate Size - Revenue > $700M */
  adequate_size: boolean;
  revenue_minimum: number;
  actual_revenue: number;

  /** Criterion 2: Strong Financial Condition - Current Ratio >= 2.0 */
  strong_financial_condition: boolean;
  current_ratio_minimum: number;
  actual_current_ratio: number;

  /** Criterion 3: Earnings Stability - 10 years positive earnings */
  earnings_stability: boolean;
  years_positive_earnings: number;
  required_years: number;

  /** Criterion 4: Dividend Record - 20 years of dividends */
  dividend_record: boolean;
  years_dividends_paid: number;
  required_dividend_years: number;

  /** Criterion 5: Earnings Growth - >33% over 10 years (~2.9% CAGR) */
  earnings_growth: boolean;
  eps_10y_growth: number | null;
  required_growth: number;

  /** Criterion 6: Moderate P/E - P/E <= 15 */
  moderate_pe: boolean;
  pe_maximum: number;
  actual_pe: number | null;

  /** Criterion 7: Moderate P/B - P/B <= 1.5 or P/E * P/B < 22.5 */
  moderate_pb: boolean;
  pb_maximum: number;
  actual_pb: number | null;

  /** Graham Product (P/E * P/B) */
  graham_product: number | null;
  graham_product_passes: boolean;

  /** Summary - number of criteria passed */
  criteria_passed: number;
  total_criteria: number;

  /** Overall pass/fail (passes if >= 5 criteria met) */
  passes_screen: boolean;
}

/**
 * Relative Valuation - Peer/sector comparison (optional)
 */
export interface RelativeValuation {
  /** List of peer company tickers */
  peer_group: string[];

  /** Peer median P/E ratio */
  peer_median_pe: number;

  /** Peer median EV/EBITDA */
  peer_median_ev_ebitda: number;

  /** Peer median Price/Sales */
  peer_median_ps: number;

  /** Peer median Price/Book */
  peer_median_pb: number;

  /** Implied value based on P/E */
  implied_value_from_pe: number;

  /** Implied value based on EV/EBITDA */
  implied_value_from_ev_ebitda: number;

  /** Implied value based on P/S */
  implied_value_from_ps: number;

  /** Implied value based on P/B */
  implied_value_from_pb: number;

  /** Composite implied value */
  composite_implied_value: number;

  /** Premium/discount to peers */
  premium_discount_to_peers: number;
}

/**
 * Valuation Result - Complete valuation output combining all methods
 */
export interface ValuationResult {
  /** Stock ticker symbol */
  ticker: string;

  /** Company name */
  company_name: string;

  /** Timestamp of calculation */
  calculation_timestamp: string;

  /** Current market price */
  current_price: number;

  /** Market capitalization */
  market_cap: number;

  /** Enterprise value */
  enterprise_value: number;

  /** Shares outstanding */
  shares_outstanding: number;

  /** DCF valuation analysis */
  dcf_valuation: DCFValuation;

  /** Graham Number calculation */
  graham_number: GrahamNumber;

  /** Graham Defensive Screen results */
  graham_defensive_screen: GrahamDefensiveCriteria;

  /** Relative valuation (optional) */
  relative_valuation?: RelativeValuation | null;

  /** List of valuation methods used */
  valuation_methods_used: string[];

  /** Composite intrinsic value (60% DCF + 40% Graham) */
  composite_intrinsic_value: number;

  /** Methodology description for composite */
  composite_methodology: string;

  /** Overall upside/downside percentage */
  upside_downside_pct: number;

  /** Margin of safety */
  margin_of_safety: number;

  /** Valuation verdict */
  verdict: ValuationVerdict;

  /** Confidence score (0.0 to 1.0) */
  confidence_score: number;

  /** Key assumptions used in calculations */
  key_assumptions: Record<string, string>;

  /** Risk factors identified */
  risk_factors: string[];

  /** Data quality score (0.0 to 1.0) */
  data_quality_score: number;
}

/**
 * Helper function to get verdict display properties
 */
export function getVerdictDisplayProps(verdict: ValuationVerdict): {
  label: string;
  colorClass: string;
  bgClass: string;
  borderClass: string;
} {
  switch (verdict) {
    case "significantly_undervalued":
      return {
        label: "Significantly Undervalued",
        colorClass: "text-emerald-400",
        bgClass: "bg-emerald-500/10",
        borderClass: "border-emerald-500/30",
      };
    case "undervalued":
      return {
        label: "Undervalued",
        colorClass: "text-green-400",
        bgClass: "bg-green-500/10",
        borderClass: "border-green-500/30",
      };
    case "fairly_valued":
      return {
        label: "Fairly Valued",
        colorClass: "text-gray-400",
        bgClass: "bg-gray-500/10",
        borderClass: "border-gray-500/30",
      };
    case "overvalued":
      return {
        label: "Overvalued",
        colorClass: "text-orange-400",
        bgClass: "bg-orange-500/10",
        borderClass: "border-orange-500/30",
      };
    case "significantly_overvalued":
      return {
        label: "Significantly Overvalued",
        colorClass: "text-red-400",
        bgClass: "bg-red-500/10",
        borderClass: "border-red-500/30",
      };
    default:
      return {
        label: "Unknown",
        colorClass: "text-gray-400",
        bgClass: "bg-gray-500/10",
        borderClass: "border-gray-500/30",
      };
  }
}

/**
 * Helper function to format upside/downside with sign
 */
export function formatUpsideDownside(value: number): string {
  const formatted = (value * 100).toFixed(1);
  return value >= 0 ? `+${formatted}%` : `${formatted}%`;
}
