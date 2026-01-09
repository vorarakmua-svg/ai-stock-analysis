/**
 * Stock TypeScript Interfaces
 * Matching the backend StockSummary model with all 51 fields from summary.csv
 */

/**
 * Stock Summary - Used in the screener grid
 * Contains all 51 columns from summary.csv
 */
export interface StockSummary {
  // === Identifiers ===
  ticker: string;
  cik: string;
  company_name: string;

  // === Classification ===
  sector: string;
  industry: string;
  country: string;
  website: string | null;

  // === Price & Market Data ===
  current_price: number;
  market_cap: number;
  volume: number;

  // === Valuation Ratios ===
  pe_trailing: number | null;
  pe_forward: number | null;
  peg_ratio: number | null;
  price_to_book: number | null;

  // === Earnings ===
  eps_trailing: number | null;
  eps_forward: number | null;

  // === Dividends ===
  dividend_yield: number | null;

  // === Risk Metrics ===
  beta: number | null;
  annual_volatility: number | null;
  max_drawdown: number | null;
  sharpe_ratio: number | null;
  risk_free_rate_10y: number | null;

  // === Income Statement ===
  total_revenue: number | null;
  net_income: number | null;
  ebitda: number | null;
  profit_margin: number | null;
  operating_margin: number | null;
  revenue_growth: number | null;

  // === Balance Sheet ===
  total_cash: number | null;
  total_debt: number | null;
  debt_to_equity: number | null;

  // === Profitability Ratios ===
  return_on_equity: number | null;
  return_on_assets: number | null;

  // === 52-Week Range ===
  "52_week_high": number | null;
  "52_week_low": number | null;

  // === Moving Averages ===
  ma_50: number | null;
  ma_200: number | null;

  // === Performance ===
  cagr_5y: number | null;
  total_return_5y: number | null;

  // === Shares & Ownership ===
  shares_outstanding: number;
  float_shares: number | null;
  insider_percent: number | null;
  institutional_percent: number | null;
  short_ratio: number | null;

  // === Employees ===
  employees: number | null;

  // === Calculated Metrics ===
  calc_ebitda: number | null;
  calc_ev: number | null;
  calc_ev_to_ebitda: number | null;
  calc_fcf: number | null;
  calc_interest_coverage: number | null;
  calc_net_debt: number | null;
  calc_roic: number | null;
  free_cash_flow: number | null;

  // === SEC Filing Data ===
  sec_fiscal_year: number | null;
  sec_net_income: number | null;
  sec_operating_cash_flow: number | null;
  sec_revenue: number | null;
  sec_stockholders_equity: number | null;
  sec_total_assets: number | null;
  sec_total_liabilities: number | null;

  // === Metadata ===
  collected_at: string;
  data_sources: string;
  treasury_yield_source: string | null;
  error_count: number;
  warning_count: number;
}

/**
 * Stock Detail - Extended data for individual stock page
 * Includes all summary fields plus additional detail data
 */
export interface StockDetail extends StockSummary {
  // Additional fields that may come from the detailed JSON files
  description?: string;
  exchange?: string;
  currency?: string;

  // Historical financials (from JSON files)
  financials_annual?: FinancialYear[];

  // Quarterly data
  income_statement_quarterly?: QuarterlyData[];
  balance_sheet_quarterly?: QuarterlyData[];
  cash_flow_quarterly?: QuarterlyData[];
}

/**
 * Annual Financial Data
 */
export interface FinancialYear {
  fiscal_year: number;
  revenue: number | null;
  gross_profit: number | null;
  operating_income: number | null;
  net_income: number | null;
  eps: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
  shareholders_equity: number | null;
  free_cash_flow: number | null;
  operating_cash_flow: number | null;
  capital_expenditures: number | null;
  depreciation_amortization: number | null;
}

/**
 * Quarterly Financial Data
 */
export interface QuarterlyData {
  period: string;
  fiscal_year: number;
  fiscal_quarter: number;
  [key: string]: string | number | null;
}

/**
 * Real-time Price Data
 */
export interface RealTimePrice {
  ticker: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  bid: number | null;
  ask: number | null;
  high: number | null;
  low: number | null;
  open: number | null;
  previous_close: number | null;
  timestamp: string;
  market_state: MarketState;
}

/**
 * Market State Enum
 */
export type MarketState = "PRE" | "REGULAR" | "POST" | "CLOSED";

/**
 * Chart Period Type for historical data
 */
export type ChartPeriod = "1mo" | "3mo" | "6mo" | "1y" | "5y";

/**
 * Historical Data Point (OHLCV)
 * Used for candlestick and volume charts
 */
export interface HistoricalDataPoint {
  /** Unix timestamp */
  time: number;
  /** Opening price */
  open: number;
  /** Highest price during the period */
  high: number;
  /** Lowest price during the period */
  low: number;
  /** Closing price */
  close: number;
  /** Trading volume */
  volume: number;
}

/**
 * Valuation Result from the backend
 */
export interface ValuationResult {
  ticker: string;
  company_name: string;
  calculation_timestamp: string;

  // Current Market Data
  current_price: number;
  market_cap: number;
  enterprise_value: number;
  shares_outstanding: number;

  // DCF Valuation
  dcf_valuation: DCFValuation;

  // Graham Valuation
  graham_number: GrahamNumber;
  graham_defensive_screen: GrahamDefensiveCriteria;

  // Composite Result
  valuation_methods_used: string[];
  composite_intrinsic_value: number;
  upside_downside_pct: number;
  margin_of_safety: number;
  verdict: ValuationVerdict;
  confidence_score: number;

  // Metadata
  key_assumptions: Record<string, string>;
  risk_factors: string[];
  data_quality_score: number;
}

/**
 * DCF Valuation Details
 */
export interface DCFValuation {
  calculation_timestamp: string;
  methodology: string;

  // Cost of Capital
  risk_free_rate: number;
  beta: number;
  equity_risk_premium: number;
  cost_of_equity: number;
  cost_of_debt_pretax: number;
  tax_rate: number;
  cost_of_debt_aftertax: number;
  debt_weight: number;
  equity_weight: number;
  wacc: number;

  // Scenarios
  conservative: DCFScenario;
  base_case: DCFScenario;
  optimistic: DCFScenario;

  // Weighted Result
  scenario_weights: Record<string, number>;
  weighted_intrinsic_value: number;

  // Sensitivity
  sensitivity_to_wacc: Record<string, number>;
  sensitivity_to_growth: Record<string, number>;
}

/**
 * Single DCF Scenario
 */
export interface DCFScenario {
  scenario_name: string;
  revenue_growth_rate: number;
  operating_margin_assumption: number;
  terminal_growth_rate: number;
  wacc: number;
  projection_years: number;
  projected_revenue: number[];
  projected_ebit: number[];
  projected_nopat: number[];
  projected_fcf: number[];
  terminal_fcf: number;
  terminal_value: number;
  pv_explicit_period: number;
  pv_terminal_value: number;
  enterprise_value: number;
  equity_value: number;
  intrinsic_value_per_share: number;
  current_price: number;
  upside_downside_pct: number;
}

/**
 * Graham Number Calculation
 */
export interface GrahamNumber {
  methodology: string;
  eps_ttm: number;
  book_value_per_share: number;
  graham_multiplier: number;
  graham_number: number;
  current_price: number;
  upside_pct: number;
  normalized_eps: number | null;
  earnings_power_value: number | null;
}

/**
 * Graham Defensive Criteria (7 criteria)
 */
export interface GrahamDefensiveCriteria {
  // Criterion 1: Adequate Size
  adequate_size: boolean;
  revenue_minimum: number;
  actual_revenue: number;

  // Criterion 2: Strong Financial Condition
  strong_financial_condition: boolean;
  current_ratio_minimum: number;
  actual_current_ratio: number;

  // Criterion 3: Earnings Stability
  earnings_stability: boolean;
  years_positive_earnings: number;
  required_years: number;

  // Criterion 4: Dividend Record
  dividend_record: boolean;
  years_dividends_paid: number;
  required_dividend_years: number;

  // Criterion 5: Earnings Growth
  earnings_growth: boolean;
  eps_10y_growth: number | null;
  required_growth: number;

  // Criterion 6: Moderate P/E
  moderate_pe: boolean;
  pe_maximum: number;
  actual_pe: number | null;

  // Criterion 7: Moderate P/B
  moderate_pb: boolean;
  pb_maximum: number;
  actual_pb: number | null;

  // Graham Product
  graham_product: number | null;
  graham_product_passes: boolean;

  // Summary
  criteria_passed: number;
  total_criteria: number;
  passes_screen: boolean;
}

/**
 * Valuation Verdict Enum
 */
export type ValuationVerdict =
  | "significantly_undervalued"
  | "undervalued"
  | "fairly_valued"
  | "overvalued"
  | "significantly_overvalued";

/**
 * Investment Rating
 */
export type InvestmentRating =
  | "strong_buy"
  | "buy"
  | "hold"
  | "sell"
  | "strong_sell";

/**
 * Risk Level
 */
export type RiskLevel = "low" | "moderate" | "high" | "very_high";

/**
 * AI Analysis Result (Warren Buffett Style)
 */
export interface AIAnalysis {
  ticker: string;
  company_name: string;
  analysis_date: string;

  // Executive Summary
  one_sentence_thesis: string;
  investment_thesis: string;

  // Business Quality
  business_understanding: string;
  business_simplicity_score: number;
  moat_summary: string;
  moat_durability: string;

  // Management
  management_assessment: string;
  management_integrity_score: number;
  capital_allocation_skill: string;
  owner_oriented: boolean;

  // Financial Analysis
  owner_earnings_analysis: string;
  earnings_predictability: string;
  balance_sheet_fortress: string;
  debt_comfort_level: string;
  cash_generation_power: string;
  return_on_capital_trend: string;

  // Valuation
  valuation_narrative: string;
  intrinsic_value_range: string;
  current_price_vs_value: string;
  margin_of_safety_assessment: string;

  // Key Considerations
  key_positives: string[];
  key_concerns: string[];
  potential_catalysts: string[];

  // Final Verdict
  investment_rating: InvestmentRating;
  conviction_level: number;
  risk_level: RiskLevel;
  suitable_for: string[];
  ideal_holding_period: string;
  patience_required_level: string;

  // Closing
  buffett_quote: string;
  final_thoughts: string;

  // Metadata
  ai_model_used: string;
  analysis_version: string;
  tokens_consumed: number;
  generation_time_seconds: number;
}

/**
 * API Error Response
 */
export interface APIError {
  detail: string;
  status_code: number;
}

/**
 * Pagination Parameters
 */
export interface PaginationParams {
  page?: number;
  limit?: number;
}

/**
 * Sort Parameters
 */
export interface SortParams {
  sort_by?: keyof StockSummary;
  sort_order?: "asc" | "desc";
}

/**
 * Filter Parameters for Stock Screener
 */
export interface StockFilterParams extends PaginationParams, SortParams {
  sector?: string;
  industry?: string;
  min_market_cap?: number;
  max_market_cap?: number;
  min_pe?: number;
  max_pe?: number;
  min_dividend_yield?: number;
  max_dividend_yield?: number;
  search?: string;
}
