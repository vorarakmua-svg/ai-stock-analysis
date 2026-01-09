"use client";

import { useState } from "react";
import {
  ValuationResult,
  DCFScenario,
  GrahamDefensiveCriteria,
  getVerdictDisplayProps,
  formatUpsideDownside,
} from "@/types/valuation";
import { useValuation, useRefreshValuation } from "@/hooks/useValuation";
import {
  formatCurrency,
  formatPercent,
  formatLargeNumber,
  cn,
} from "@/lib/utils";

/**
 * Whitelist of valid assumption keys from the backend
 * Used to prevent XSS through untrusted object keys
 */
const VALID_ASSUMPTION_KEYS = new Set([
  "risk_free_rate",
  "equity_risk_premium",
  "beta",
  "wacc",
  "tax_rate",
  "base_case_growth",
  "terminal_growth",
  "operating_margin",
  "dcf_weight",
  "graham_weight",
  "projection_years",
]);

/**
 * Sanitize assumption key for display
 * Only allows whitelisted keys, returns null for unknown keys
 */
function sanitizeAssumptionKey(key: string): string | null {
  if (!VALID_ASSUMPTION_KEYS.has(key)) {
    return null;
  }
  return key.replace(/_/g, " ");
}

/**
 * Props for ValuationCard component
 */
interface ValuationCardProps {
  /** Stock ticker symbol */
  ticker: string;
  /** Whether to auto-fetch data (default: false to prevent unwanted AI costs) */
  autoFetch?: boolean;
  /** Optional className for styling */
  className?: string;
}

/**
 * ValuationCard - Comprehensive valuation display component
 *
 * Displays DCF analysis, Graham Number, and defensive criteria
 * with Bloomberg Terminal dark theme styling
 *
 * NOTE: By default, autoFetch is false to prevent unwanted AI API costs.
 * User must click "Run Valuation" button to trigger the AI calculation.
 */
export function ValuationCard({
  ticker,
  autoFetch = false,
  className,
}: ValuationCardProps) {
  // State to track if user has manually triggered the valuation
  const [userTriggered, setUserTriggered] = useState(false);

  // Only enable fetching if autoFetch is true OR user has clicked the button
  const enabled = autoFetch || userTriggered;

  const {
    data: valuation,
    isLoading,
    error,
    refetch,
    isFetched,
  } = useValuation(ticker, enabled);
  const { mutate: refresh, isPending: isRefreshing } = useRefreshValuation();

  const [isAssumptionsExpanded, setIsAssumptionsExpanded] = useState(false);

  // Handle user triggering valuation
  const handleRunValuation = () => {
    setUserTriggered(true);
  };

  // Show "Run Valuation" button if not enabled yet and no cached data
  if (!enabled && !valuation) {
    return (
      <div
        className={cn(
          "rounded-lg border border-border bg-background-secondary p-6",
          className
        )}
      >
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-accent/10 mb-4">
            <svg
              className="h-8 w-8 text-accent"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">Valuation Analysis</h3>
          <p className="text-sm text-foreground-muted mb-4 max-w-md">
            DCF and Graham Number valuation requires AI processing.
            Click below to calculate intrinsic value.
          </p>
          <p className="text-xs text-foreground-muted mb-4">
            This will use AI API credits
          </p>
          <button
            onClick={handleRunValuation}
            className={cn(
              "inline-flex items-center gap-2 rounded-lg bg-accent px-6 py-3 text-sm font-medium text-white",
              "transition-colors hover:bg-accent/90"
            )}
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            Run Valuation
          </button>
        </div>
      </div>
    );
  }

  // Loading State
  if (isLoading) {
    return <ValuationSkeleton className={className} />;
  }

  // Error State
  if (error) {
    return (
      <ValuationError
        error={error}
        onRetry={() => refetch()}
        className={className}
      />
    );
  }

  // No Data State (after fetch attempt)
  if (!valuation) {
    return (
      <div
        className={cn(
          "rounded-lg border border-border bg-background-secondary p-6",
          className
        )}
      >
        <p className="text-foreground-muted">No valuation data available.</p>
        <button
          onClick={handleRunValuation}
          className={cn(
            "mt-4 inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white",
            "transition-colors hover:bg-accent/90"
          )}
        >
          Try Again
        </button>
      </div>
    );
  }

  const verdictProps = getVerdictDisplayProps(valuation.verdict);

  return (
    <div
      className={cn(
        "space-y-6 rounded-lg border border-border bg-background-secondary p-6",
        className
      )}
    >
      {/* Header Section */}
      <ValuationHeader
        valuation={valuation}
        verdictProps={verdictProps}
        onRefresh={() => refresh(ticker)}
        isRefreshing={isRefreshing}
      />

      {/* DCF Section */}
      <DCFSection dcf={valuation.dcf_valuation} />

      {/* Graham Section */}
      <GrahamSection
        grahamNumber={valuation.graham_number}
        defensiveCriteria={valuation.graham_defensive_screen}
      />

      {/* Methodology Section */}
      <MethodologySection
        methodology={valuation.composite_methodology}
        assumptions={valuation.key_assumptions}
        riskFactors={valuation.risk_factors}
        isExpanded={isAssumptionsExpanded}
        onToggle={() => setIsAssumptionsExpanded(!isAssumptionsExpanded)}
      />

      {/* Footer Section */}
      <ValuationFooter
        confidenceScore={valuation.confidence_score}
        dataQualityScore={valuation.data_quality_score}
        timestamp={valuation.calculation_timestamp}
      />
    </div>
  );
}

/**
 * Header Section - Verdict, Intrinsic Value, Upside/Downside
 */
interface ValuationHeaderProps {
  valuation: ValuationResult;
  verdictProps: ReturnType<typeof getVerdictDisplayProps>;
  onRefresh: () => void;
  isRefreshing: boolean;
}

function ValuationHeader({
  valuation,
  verdictProps,
  onRefresh,
  isRefreshing,
}: ValuationHeaderProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">
            Valuation Analysis
          </h2>
          <p className="mt-1 text-sm text-foreground-muted">
            DCF + Graham Number Hybrid Model
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className={cn(
            "flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm",
            "transition-colors hover:bg-background-tertiary",
            "disabled:cursor-not-allowed disabled:opacity-50"
          )}
        >
          <svg
            className={cn("h-4 w-4", isRefreshing && "animate-spin")}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* Verdict Badge and Key Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Verdict Badge */}
        <div
          className={cn(
            "rounded-lg border p-4",
            verdictProps.bgClass,
            verdictProps.borderClass
          )}
        >
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Verdict
          </p>
          <p className={cn("mt-1 text-lg font-bold", verdictProps.colorClass)}>
            {verdictProps.label}
          </p>
        </div>

        {/* Composite Intrinsic Value */}
        <div className="rounded-lg border border-border bg-background-tertiary p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Intrinsic Value
          </p>
          <p className="mt-1 font-mono text-lg font-bold tabular-nums text-accent">
            {formatCurrency(valuation.composite_intrinsic_value)}
          </p>
        </div>

        {/* Upside/Downside */}
        <div className="rounded-lg border border-border bg-background-tertiary p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Upside/Downside
          </p>
          <p
            className={cn(
              "mt-1 font-mono text-lg font-bold tabular-nums",
              valuation.upside_downside_pct >= 0
                ? "text-positive"
                : "text-negative"
            )}
          >
            {formatUpsideDownside(valuation.upside_downside_pct)}
          </p>
        </div>

        {/* Margin of Safety */}
        <div className="rounded-lg border border-border bg-background-tertiary p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Margin of Safety
          </p>
          <p
            className={cn(
              "mt-1 font-mono text-lg font-bold tabular-nums",
              valuation.margin_of_safety >= 0.25
                ? "text-positive"
                : valuation.margin_of_safety >= 0
                  ? "text-foreground"
                  : "text-negative"
            )}
          >
            {formatPercent(valuation.margin_of_safety)}
          </p>
        </div>
      </div>

      {/* Current Price vs Intrinsic Value Comparison */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-foreground-muted">Current Price:</span>
        <span className="font-mono font-medium tabular-nums">
          {formatCurrency(valuation.current_price)}
        </span>
        <span className="text-foreground-muted">vs</span>
        <span className="text-foreground-muted">Intrinsic Value:</span>
        <span className="font-mono font-medium tabular-nums text-accent">
          {formatCurrency(valuation.composite_intrinsic_value)}
        </span>
      </div>
    </div>
  );
}

/**
 * DCF Section - WACC breakdown and scenario analysis
 */
interface DCFSectionProps {
  dcf: ValuationResult["dcf_valuation"];
}

function DCFSection({ dcf }: DCFSectionProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">
        Discounted Cash Flow (DCF) Analysis
      </h3>

      {/* WACC Breakdown */}
      <div className="rounded-lg border border-border bg-background-tertiary p-4">
        <div className="mb-3 flex items-center justify-between">
          <h4 className="text-sm font-medium">
            WACC (Weighted Average Cost of Capital)
          </h4>
          <span className="font-mono text-lg font-bold tabular-nums text-accent">
            {formatPercent(dcf.wacc)}
          </span>
        </div>

        <div className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <WACCMetric
            label="Cost of Equity"
            value={formatPercent(dcf.cost_of_equity)}
            sublabel={`Rf ${formatPercent(dcf.risk_free_rate)} + Beta ${dcf.beta.toFixed(2)} x ERP ${formatPercent(dcf.equity_risk_premium)}`}
          />
          <WACCMetric
            label="Cost of Debt (After-Tax)"
            value={formatPercent(dcf.cost_of_debt_aftertax)}
            sublabel={`Pre-tax ${formatPercent(dcf.cost_of_debt_pretax)} x (1 - ${formatPercent(dcf.tax_rate)})`}
          />
          <WACCMetric
            label="Equity Weight"
            value={formatPercent(dcf.equity_weight)}
          />
          <WACCMetric
            label="Debt Weight"
            value={formatPercent(dcf.debt_weight)}
          />
        </div>
      </div>

      {/* Three Scenarios */}
      <div className="grid gap-4 lg:grid-cols-3">
        <ScenarioCard scenario={dcf.conservative} colorClass="text-orange-400" />
        <ScenarioCard scenario={dcf.base_case} colorClass="text-blue-400" />
        <ScenarioCard scenario={dcf.optimistic} colorClass="text-emerald-400" />
      </div>

      {/* Weighted Intrinsic Value */}
      <div className="flex items-center justify-between rounded-lg border border-accent/30 bg-accent/5 p-4">
        <div>
          <p className="text-sm font-medium">
            Probability-Weighted DCF Value
          </p>
          <p className="mt-0.5 text-xs text-foreground-muted">
            25% Conservative + 50% Base + 25% Optimistic
          </p>
        </div>
        <span className="font-mono text-xl font-bold tabular-nums text-accent">
          {formatCurrency(dcf.weighted_intrinsic_value)}
        </span>
      </div>

      {/* Sensitivity Analysis */}
      <SensitivityTable sensitivity={dcf.sensitivity_to_wacc} baseWacc={dcf.wacc} />
    </div>
  );
}

/**
 * WACC Metric Display
 */
interface WACCMetricProps {
  label: string;
  value: string;
  sublabel?: string;
}

function WACCMetric({ label, value, sublabel }: WACCMetricProps) {
  return (
    <div>
      <p className="text-foreground-muted">{label}</p>
      <p className="font-mono font-medium tabular-nums">{value}</p>
      {sublabel && (
        <p className="mt-0.5 text-xs text-foreground-muted">{sublabel}</p>
      )}
    </div>
  );
}

/**
 * DCF Scenario Card
 */
interface ScenarioCardProps {
  scenario: DCFScenario;
  colorClass: string;
}

function ScenarioCard({ scenario, colorClass }: ScenarioCardProps) {
  const isPositive = scenario.upside_downside_pct >= 0;

  return (
    <div className="rounded-lg border border-border bg-background-tertiary p-4">
      <div className="mb-3 flex items-center justify-between">
        <h4 className={cn("text-sm font-semibold capitalize", colorClass)}>
          {scenario.scenario_name.replace("_", " ")}
        </h4>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-xs font-medium",
            isPositive
              ? "bg-positive/10 text-positive"
              : "bg-negative/10 text-negative"
          )}
        >
          {formatUpsideDownside(scenario.upside_downside_pct)}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-foreground-muted">Growth Rate</span>
          <span className="font-mono tabular-nums">
            {formatPercent(scenario.revenue_growth_rate)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-foreground-muted">Terminal Growth</span>
          <span className="font-mono tabular-nums">
            {formatPercent(scenario.terminal_growth_rate)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-foreground-muted">Operating Margin</span>
          <span className="font-mono tabular-nums">
            {formatPercent(scenario.operating_margin_assumption)}
          </span>
        </div>
        <div className="my-2 border-t border-border" />
        <div className="flex justify-between">
          <span className="font-medium">Intrinsic Value</span>
          <span className="font-mono font-bold tabular-nums text-accent">
            {formatCurrency(scenario.intrinsic_value_per_share)}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * WACC Sensitivity Table
 */
interface SensitivityTableProps {
  sensitivity: Record<string, number>;
  baseWacc: number;
}

function SensitivityTable({
  sensitivity,
  baseWacc,
}: SensitivityTableProps) {
  const waccMinus1 = sensitivity["wacc_minus_1pct"];
  const waccPlus1 = sensitivity["wacc_plus_1pct"];

  if (!waccMinus1 && !waccPlus1) {
    return <></>;
  }

  return (
    <div className="rounded-lg border border-border bg-background-tertiary p-4">
      <h4 className="mb-3 text-sm font-medium">WACC Sensitivity Analysis</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="pb-2 text-left font-medium text-foreground-muted">
                WACC
              </th>
              <th className="pb-2 text-right font-medium text-foreground-muted">
                Intrinsic Value
              </th>
            </tr>
          </thead>
          <tbody className="font-mono tabular-nums">
            {waccMinus1 && (
              <tr className="border-b border-border/50">
                <td className="py-2 text-emerald-400">
                  {formatPercent(baseWacc - 0.01)} (-1%)
                </td>
                <td className="py-2 text-right">{formatCurrency(waccMinus1)}</td>
              </tr>
            )}
            <tr className="border-b border-border/50 bg-accent/5">
              <td className="py-2 font-medium text-accent">
                {formatPercent(baseWacc)} (Base)
              </td>
              <td className="py-2 text-right font-medium">-</td>
            </tr>
            {waccPlus1 && (
              <tr>
                <td className="py-2 text-orange-400">
                  {formatPercent(baseWacc + 0.01)} (+1%)
                </td>
                <td className="py-2 text-right">{formatCurrency(waccPlus1)}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Graham Section - Graham Number and Defensive Criteria
 */
interface GrahamSectionProps {
  grahamNumber: ValuationResult["graham_number"];
  defensiveCriteria: GrahamDefensiveCriteria;
}

function GrahamSection({
  grahamNumber,
  defensiveCriteria,
}: GrahamSectionProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Graham Valuation</h3>

      {/* Graham Number */}
      <div className="rounded-lg border border-border bg-background-tertiary p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h4 className="text-sm font-medium">Graham Number</h4>
            <p className="mt-0.5 text-xs text-foreground-muted">
              {grahamNumber.methodology}
            </p>
          </div>
          <div className="text-right">
            <p className="font-mono text-2xl font-bold tabular-nums text-accent">
              {formatCurrency(grahamNumber.graham_number)}
            </p>
            <p
              className={cn(
                "mt-0.5 font-mono text-sm tabular-nums",
                grahamNumber.upside_pct >= 0 ? "text-positive" : "text-negative"
              )}
            >
              {formatUpsideDownside(grahamNumber.upside_pct)} vs current price
            </p>
          </div>
        </div>

        {/* Formula Visualization */}
        <div className="mt-4 rounded-lg bg-background p-3">
          <p className="text-center font-mono text-sm">
            <span className="text-foreground-muted">Graham Number = </span>
            <span className="text-accent">sqrt</span>
            <span className="text-foreground-muted">(</span>
            <span className="text-orange-400">{grahamNumber.graham_multiplier}</span>
            <span className="text-foreground-muted"> x </span>
            <span className="text-emerald-400">
              {formatCurrency(grahamNumber.eps_ttm)}
            </span>
            <span className="text-foreground-muted"> x </span>
            <span className="text-blue-400">
              {formatCurrency(grahamNumber.book_value_per_share)}
            </span>
            <span className="text-foreground-muted">)</span>
          </p>
          <p className="mt-2 text-center text-xs text-foreground-muted">
            <span className="text-orange-400">22.5</span> (P/E 15 x P/B 1.5) x{" "}
            <span className="text-emerald-400">EPS</span> x{" "}
            <span className="text-blue-400">BVPS</span>
          </p>
        </div>
      </div>

      {/* Defensive Criteria Checklist */}
      <div className="rounded-lg border border-border bg-background-tertiary p-4">
        <div className="mb-4 flex items-center justify-between">
          <h4 className="text-sm font-medium">
            Graham Defensive Criteria
          </h4>
          <span
            className={cn(
              "rounded-full px-3 py-1 text-sm font-medium",
              defensiveCriteria.passes_screen
                ? "bg-positive/10 text-positive"
                : "bg-negative/10 text-negative"
            )}
          >
            {defensiveCriteria.criteria_passed}/{defensiveCriteria.total_criteria} Passed
          </span>
        </div>

        <div className="space-y-2">
          <CriterionRow
            number={1}
            name="Adequate Size"
            description={`Revenue > ${formatLargeNumber(defensiveCriteria.revenue_minimum)}`}
            passed={defensiveCriteria.adequate_size}
            actual={formatLargeNumber(defensiveCriteria.actual_revenue)}
          />
          <CriterionRow
            number={2}
            name="Strong Financial Condition"
            description={`Current Ratio >= ${defensiveCriteria.current_ratio_minimum.toFixed(1)}`}
            passed={defensiveCriteria.strong_financial_condition}
            actual={defensiveCriteria.actual_current_ratio.toFixed(2)}
          />
          <CriterionRow
            number={3}
            name="Earnings Stability"
            description={`${defensiveCriteria.required_years} years positive earnings`}
            passed={defensiveCriteria.earnings_stability}
            actual={`${defensiveCriteria.years_positive_earnings} years`}
          />
          <CriterionRow
            number={4}
            name="Dividend Record"
            description={`${defensiveCriteria.required_dividend_years} years of dividends`}
            passed={defensiveCriteria.dividend_record}
            actual={`${defensiveCriteria.years_dividends_paid} years`}
          />
          <CriterionRow
            number={5}
            name="Earnings Growth"
            description={`>${formatPercent(defensiveCriteria.required_growth)} over 10 years`}
            passed={defensiveCriteria.earnings_growth}
            actual={
              defensiveCriteria.eps_10y_growth !== null
                ? formatPercent(defensiveCriteria.eps_10y_growth)
                : "N/A"
            }
          />
          <CriterionRow
            number={6}
            name="Moderate P/E"
            description={`P/E <= ${defensiveCriteria.pe_maximum.toFixed(1)}`}
            passed={defensiveCriteria.moderate_pe}
            actual={
              defensiveCriteria.actual_pe !== null
                ? defensiveCriteria.actual_pe.toFixed(2)
                : "N/A"
            }
          />
          <CriterionRow
            number={7}
            name="Moderate P/B"
            description={`P/B <= ${defensiveCriteria.pb_maximum.toFixed(1)} or P/E x P/B < 22.5`}
            passed={defensiveCriteria.moderate_pb || defensiveCriteria.graham_product_passes}
            actual={
              defensiveCriteria.actual_pb !== null
                ? `P/B: ${defensiveCriteria.actual_pb.toFixed(2)}${defensiveCriteria.graham_product !== null ? ` (Product: ${defensiveCriteria.graham_product.toFixed(1)})` : ""}`
                : "N/A"
            }
          />
        </div>

        <div className="mt-4 rounded-lg bg-background p-3">
          <p className="text-center text-sm text-foreground-muted">
            {defensiveCriteria.passes_screen ? (
              <span className="text-positive">
                Passes Graham Defensive Screen (5+ criteria met)
              </span>
            ) : (
              <span className="text-negative">
                Does not pass Graham Defensive Screen (fewer than 5 criteria met)
              </span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Criterion Row for Defensive Checklist
 */
interface CriterionRowProps {
  number: number;
  name: string;
  description: string;
  passed: boolean;
  actual: string;
}

function CriterionRow({
  number,
  name,
  description,
  passed,
  actual,
}: CriterionRowProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg p-2 transition-colors",
        passed ? "bg-positive/5" : "bg-negative/5"
      )}
    >
      <div
        className={cn(
          "flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold",
          passed
            ? "bg-positive/20 text-positive"
            : "bg-negative/20 text-negative"
        )}
      >
        {passed ? (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-medium truncate">
            {number}. {name}
          </p>
          <span className="flex-shrink-0 font-mono text-xs tabular-nums text-foreground-muted">
            {actual}
          </span>
        </div>
        <p className="text-xs text-foreground-muted">{description}</p>
      </div>
    </div>
  );
}

/**
 * Methodology Section - Composite methodology and assumptions
 */
interface MethodologySectionProps {
  methodology: string;
  assumptions: Record<string, string>;
  riskFactors: string[];
  isExpanded: boolean;
  onToggle: () => void;
}

function MethodologySection({
  methodology,
  assumptions,
  riskFactors,
  isExpanded,
  onToggle,
}: MethodologySectionProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Methodology</h3>

      <div className="rounded-lg border border-border bg-background-tertiary p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Composite Valuation</p>
            <p className="mt-0.5 text-sm text-accent">{methodology}</p>
          </div>
          <button
            onClick={onToggle}
            className="flex items-center gap-1 text-sm text-foreground-muted transition-colors hover:text-foreground"
          >
            {isExpanded ? "Hide" : "Show"} Assumptions
            <svg
              className={cn(
                "h-4 w-4 transition-transform",
                isExpanded && "rotate-180"
              )}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>

        {isExpanded && (
          <div className="mt-4 space-y-4 border-t border-border pt-4">
            {/* Key Assumptions */}
            <div>
              <h4 className="mb-2 text-sm font-medium text-foreground-muted">
                Key Assumptions
              </h4>
              <div className="grid gap-2 sm:grid-cols-2">
                {Object.entries(assumptions).map(([key, value]) => {
                  const sanitizedKey = sanitizeAssumptionKey(key);
                  if (!sanitizedKey) return null; // Skip unknown keys
                  return (
                    <div
                      key={key}
                      className="flex justify-between text-sm"
                    >
                      <span className="text-foreground-muted capitalize">
                        {sanitizedKey}
                      </span>
                      <span className="font-mono tabular-nums">{value}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Risk Factors */}
            {riskFactors.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-medium text-foreground-muted">
                  Risk Factors
                </h4>
                <ul className="space-y-1">
                  {riskFactors.map((risk, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-2 text-sm text-foreground-muted"
                    >
                      <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-negative" />
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Footer Section - Confidence scores and timestamp
 */
interface ValuationFooterProps {
  confidenceScore: number;
  dataQualityScore: number;
  timestamp: string;
}

function ValuationFooter({
  confidenceScore,
  dataQualityScore,
  timestamp,
}: ValuationFooterProps) {
  return (
    <div className="space-y-4 border-t border-border pt-4">
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Confidence Score */}
        <div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-foreground-muted">Confidence Score</span>
            <span className="font-mono tabular-nums">
              {(confidenceScore * 100).toFixed(0)}%
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-background">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                confidenceScore >= 0.8
                  ? "bg-positive"
                  : confidenceScore >= 0.6
                    ? "bg-yellow-500"
                    : "bg-negative"
              )}
              style={{ width: `${confidenceScore * 100}%` }}
            />
          </div>
        </div>

        {/* Data Quality Score */}
        <div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-foreground-muted">Data Quality Score</span>
            <span className="font-mono tabular-nums">
              {(dataQualityScore * 100).toFixed(0)}%
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-background">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                dataQualityScore >= 0.8
                  ? "bg-positive"
                  : dataQualityScore >= 0.6
                    ? "bg-yellow-500"
                    : "bg-negative"
              )}
              style={{ width: `${dataQualityScore * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Timestamp */}
      <div className="text-right text-xs text-foreground-muted">
        Calculated: {new Date(timestamp).toLocaleString()}
      </div>
    </div>
  );
}

/**
 * Loading Skeleton for Valuation Card
 */
interface ValuationSkeletonProps {
  className?: string;
}

function ValuationSkeleton({ className }: ValuationSkeletonProps) {
  return (
    <div
      className={cn(
        "space-y-6 rounded-lg border border-border bg-background-secondary p-6",
        className
      )}
    >
      {/* Header Skeleton */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="h-7 w-48 skeleton rounded" />
            <div className="mt-2 h-4 w-64 skeleton rounded" />
          </div>
          <div className="h-9 w-24 skeleton rounded-lg" />
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-lg border border-border p-4">
              <div className="h-3 w-16 skeleton rounded" />
              <div className="mt-2 h-6 w-24 skeleton rounded" />
            </div>
          ))}
        </div>
      </div>

      {/* DCF Section Skeleton */}
      <div className="space-y-4">
        <div className="h-6 w-48 skeleton rounded" />
        <div className="h-32 skeleton rounded-lg" />
        <div className="grid gap-4 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-40 skeleton rounded-lg" />
          ))}
        </div>
      </div>

      {/* Graham Section Skeleton */}
      <div className="space-y-4">
        <div className="h-6 w-36 skeleton rounded" />
        <div className="h-32 skeleton rounded-lg" />
        <div className="h-64 skeleton rounded-lg" />
      </div>
    </div>
  );
}

/**
 * Error State for Valuation Card
 */
interface ValuationErrorProps {
  error: Error;
  onRetry: () => void;
  className?: string;
}

function ValuationError({
  error,
  onRetry,
  className,
}: ValuationErrorProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-negative/50 bg-negative/10 p-6",
        className
      )}
    >
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-negative/20">
          <svg
            className="h-5 w-5 text-negative"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-negative">
            Failed to Load Valuation
          </h3>
          <p className="mt-1 text-sm text-foreground-muted">
            {error.message || "An unexpected error occurred while loading valuation data."}
          </p>
          <button
            onClick={onRetry}
            className="mt-4 inline-flex items-center gap-2 rounded-lg border border-negative/50 px-4 py-2 text-sm font-medium text-negative transition-colors hover:bg-negative/20"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Retry
          </button>
        </div>
      </div>
    </div>
  );
}

export default ValuationCard;
