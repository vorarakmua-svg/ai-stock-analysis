"use client";

import { useState, useCallback, useId } from "react";
import {
  WarrenBuffettAnalysis,
  CompetitiveAdvantage,
  RiskFactor,
  getRatingDisplayProps,
  getRiskLevelDisplayProps,
  getMoatTypeLabel,
  getMoatDurabilityDisplayProps,
  getSeverityDisplayProps,
  getProbabilityDisplayProps,
  getEarningsPredictabilityDisplayProps,
  getInvestorTypeLabel,
  formatConvictionLevel,
  getConvictionColorClass,
} from "@/types/analysis";
import { useAIAnalysis, useRefreshAnalysis } from "@/hooks/useAIAnalysis";
import { cn } from "@/lib/utils";

/**
 * Props for AIAnalysis component
 */
interface AIAnalysisProps {
  /** Stock ticker symbol */
  ticker: string;
  /** Whether to auto-fetch data (default: false to prevent unwanted AI costs) */
  autoFetch?: boolean;
  /** Optional className for styling */
  className?: string;
}

/**
 * AIAnalysis - Comprehensive Warren Buffett-style investment memo display
 *
 * Displays AI-generated investment analysis with:
 * - Executive summary with investment thesis
 * - Business quality assessment and moat analysis
 * - Management evaluation
 * - Financial health assessment
 * - Valuation summary
 * - Risk factors and catalysts
 * - Final verdict with rating
 *
 * NOTE: By default, autoFetch is false to prevent unwanted AI API costs.
 * User must click "Generate Analysis" button to trigger the AI analysis.
 */
export function AIAnalysis({
  ticker,
  autoFetch = false,
  className,
}: AIAnalysisProps) {
  // State to track if user has manually triggered the analysis
  const [userTriggered, setUserTriggered] = useState(false);

  // Only enable fetching if autoFetch is true OR user has clicked the button
  const enabled = autoFetch || userTriggered;

  const {
    data: analysis,
    isLoading,
    error,
    refetch,
  } = useAIAnalysis(ticker, enabled);
  const { mutate: refresh, isPending: isRefreshing } = useRefreshAnalysis();

  // Section expansion states
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["executive", "verdict"])
  );

  const toggleSection = useCallback((section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  }, []);

  const expandAll = () => {
    setExpandedSections(
      new Set([
        "executive",
        "business",
        "management",
        "earnings",
        "financial",
        "valuation",
        "considerations",
        "timeHorizon",
        "verdict",
        "closing",
        "meta",
      ])
    );
  };

  const collapseAll = () => {
    setExpandedSections(new Set());
  };

  // Handle user triggering analysis
  const handleGenerateAnalysis = () => {
    setUserTriggered(true);
  };

  // Show "Generate Analysis" button if not enabled yet and no cached data
  if (!enabled && !analysis) {
    return (
      <div
        className={cn(
          "rounded-lg border border-border bg-background-secondary p-6",
          className
        )}
      >
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-purple-500/10 mb-4">
            <svg
              className="h-8 w-8 text-purple-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">AI Investment Analysis</h3>
          <p className="text-sm text-foreground-muted mb-4 max-w-md">
            Generate a comprehensive Warren Buffett-style investment memo
            with business quality, moat analysis, and valuation assessment.
          </p>
          <p className="text-xs text-foreground-muted mb-4">
            This will use AI API credits and may take 30-60 seconds
          </p>
          <button
            onClick={handleGenerateAnalysis}
            className={cn(
              "inline-flex items-center gap-2 rounded-lg bg-purple-600 px-6 py-3 text-sm font-medium text-white",
              "transition-colors hover:bg-purple-500"
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
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            Generate AI Analysis
          </button>
        </div>
      </div>
    );
  }

  // Loading State
  if (isLoading) {
    return <AnalysisSkeleton className={className} />;
  }

  // Error State
  if (error) {
    return (
      <AnalysisError
        error={error}
        onRetry={() => refetch()}
        className={className}
      />
    );
  }

  // No Data State (after fetch attempt)
  if (!analysis) {
    return (
      <div
        className={cn(
          "rounded-lg border border-border bg-background-secondary p-6",
          className
        )}
      >
        <p className="text-foreground-muted">No AI analysis available.</p>
        <button
          onClick={() => refresh(ticker)}
          disabled={isRefreshing}
          className={cn(
            "mt-4 inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white",
            "transition-colors hover:bg-accent/90",
            "disabled:cursor-not-allowed disabled:opacity-50"
          )}
        >
          {isRefreshing ? "Generating..." : "Generate Analysis"}
        </button>
      </div>
    );
  }

  const ratingProps = getRatingDisplayProps(analysis.investment_rating);
  const riskProps = getRiskLevelDisplayProps(analysis.risk_level);

  return (
    <div
      className={cn(
        "space-y-4 rounded-lg border border-border bg-background-secondary",
        className
      )}
    >
      {/* Header */}
      <AnalysisHeader
        analysis={analysis}
        ratingProps={ratingProps}
        onRefresh={() => refresh(ticker)}
        isRefreshing={isRefreshing}
        onExpandAll={expandAll}
        onCollapseAll={collapseAll}
      />

      {/* Sections */}
      <div className="space-y-2 px-6 pb-6">
        {/* Executive Summary */}
        <CollapsibleSection
          title="Executive Summary"
          isExpanded={expandedSections.has("executive")}
          onToggle={() => toggleSection("executive")}
          accentColor="blue"
        >
          <ExecutiveSummarySection analysis={analysis} ratingProps={ratingProps} />
        </CollapsibleSection>

        {/* Business Quality */}
        <CollapsibleSection
          title="Business Quality Assessment"
          isExpanded={expandedSections.has("business")}
          onToggle={() => toggleSection("business")}
          accentColor="emerald"
        >
          <BusinessQualitySection analysis={analysis} />
        </CollapsibleSection>

        {/* Management */}
        <CollapsibleSection
          title="Management Assessment"
          isExpanded={expandedSections.has("management")}
          onToggle={() => toggleSection("management")}
          accentColor="purple"
        >
          <ManagementSection analysis={analysis} />
        </CollapsibleSection>

        {/* Earnings Power */}
        <CollapsibleSection
          title="Earnings Power"
          isExpanded={expandedSections.has("earnings")}
          onToggle={() => toggleSection("earnings")}
          accentColor="yellow"
        >
          <EarningsPowerSection analysis={analysis} />
        </CollapsibleSection>

        {/* Financial Health */}
        <CollapsibleSection
          title="Financial Health"
          isExpanded={expandedSections.has("financial")}
          onToggle={() => toggleSection("financial")}
          accentColor="cyan"
        >
          <FinancialHealthSection analysis={analysis} />
        </CollapsibleSection>

        {/* Valuation */}
        <CollapsibleSection
          title="Valuation Assessment"
          isExpanded={expandedSections.has("valuation")}
          onToggle={() => toggleSection("valuation")}
          accentColor="orange"
        >
          <ValuationSection analysis={analysis} />
        </CollapsibleSection>

        {/* Key Considerations */}
        <CollapsibleSection
          title="Key Investment Considerations"
          isExpanded={expandedSections.has("considerations")}
          onToggle={() => toggleSection("considerations")}
          accentColor="rose"
        >
          <KeyConsiderationsSection analysis={analysis} />
        </CollapsibleSection>

        {/* Time Horizon */}
        <CollapsibleSection
          title="Time Horizon"
          isExpanded={expandedSections.has("timeHorizon")}
          onToggle={() => toggleSection("timeHorizon")}
          accentColor="indigo"
        >
          <TimeHorizonSection analysis={analysis} />
        </CollapsibleSection>

        {/* Final Verdict */}
        <CollapsibleSection
          title="Final Verdict"
          isExpanded={expandedSections.has("verdict")}
          onToggle={() => toggleSection("verdict")}
          accentColor="emerald"
        >
          <FinalVerdictSection
            analysis={analysis}
            ratingProps={ratingProps}
            riskProps={riskProps}
          />
        </CollapsibleSection>

        {/* Closing */}
        <CollapsibleSection
          title="Closing Wisdom"
          isExpanded={expandedSections.has("closing")}
          onToggle={() => toggleSection("closing")}
          accentColor="amber"
        >
          <ClosingSection analysis={analysis} />
        </CollapsibleSection>

        {/* Meta Information */}
        <CollapsibleSection
          title="Analysis Information"
          isExpanded={expandedSections.has("meta")}
          onToggle={() => toggleSection("meta")}
          accentColor="gray"
        >
          <MetaSection analysis={analysis} />
        </CollapsibleSection>
      </div>
    </div>
  );
}

/**
 * Analysis Header Component
 */
interface AnalysisHeaderProps {
  analysis: WarrenBuffettAnalysis;
  ratingProps: ReturnType<typeof getRatingDisplayProps>;
  onRefresh: () => void;
  isRefreshing: boolean;
  onExpandAll: () => void;
  onCollapseAll: () => void;
}

function AnalysisHeader({
  analysis,
  ratingProps,
  onRefresh,
  isRefreshing,
  onExpandAll,
  onCollapseAll,
}: AnalysisHeaderProps) {
  return (
    <div className="border-b border-border p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold tracking-tight">
              AI Investment Analysis
            </h2>
            <span
              className={cn(
                "rounded-full px-3 py-1 text-sm font-bold",
                ratingProps.bgClass,
                ratingProps.colorClass
              )}
            >
              {ratingProps.label}
            </span>
          </div>
          <p className="mt-1 text-sm text-foreground-muted">
            Warren Buffett-Style Investment Memo for {analysis.company_name}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onCollapseAll}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-background-tertiary"
          >
            Collapse All
          </button>
          <button
            onClick={onExpandAll}
            className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-background-tertiary"
          >
            Expand All
          </button>
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
            {isRefreshing ? "Regenerating..." : "Regenerate"}
          </button>
        </div>
      </div>

      {/* One-sentence thesis highlight */}
      <div className="mt-4 rounded-lg border border-accent/30 bg-accent/5 p-4">
        <p className="text-sm font-medium text-accent">Investment Thesis</p>
        <p className="mt-1 text-lg font-medium leading-relaxed">
          {analysis.one_sentence_thesis}
        </p>
      </div>
    </div>
  );
}

/**
 * Collapsible Section Component
 */
interface CollapsibleSectionProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  accentColor?: string;
  /** Unique identifier for the section (used for aria-controls) */
  sectionId?: string;
  children: React.ReactNode;
}

function CollapsibleSection({
  title,
  isExpanded,
  onToggle,
  accentColor = "gray",
  sectionId,
  children,
}: CollapsibleSectionProps) {
  // Generate a unique ID if not provided
  const generatedId = useId();
  const contentId = sectionId || `section-content-${generatedId}`;
  const buttonId = `section-button-${generatedId}`;

  const accentClasses: Record<string, string> = {
    blue: "border-l-blue-500",
    emerald: "border-l-emerald-500",
    purple: "border-l-purple-500",
    yellow: "border-l-yellow-500",
    cyan: "border-l-cyan-500",
    orange: "border-l-orange-500",
    rose: "border-l-rose-500",
    indigo: "border-l-indigo-500",
    amber: "border-l-amber-500",
    gray: "border-l-gray-500",
  };

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-background-tertiary overflow-hidden",
        "border-l-4",
        accentClasses[accentColor] || accentClasses.gray
      )}
    >
      <button
        id={buttonId}
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={contentId}
        className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-background/50"
      >
        <h3 className="text-base font-semibold">{title}</h3>
        <svg
          className={cn(
            "h-5 w-5 text-foreground-muted transition-transform duration-200",
            isExpanded && "rotate-180"
          )}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {isExpanded && (
        <div
          id={contentId}
          role="region"
          aria-labelledby={buttonId}
          className="border-t border-border px-4 pb-4 pt-3"
        >
          {children}
        </div>
      )}
    </div>
  );
}

/**
 * Executive Summary Section
 */
interface ExecutiveSummarySectionProps {
  analysis: WarrenBuffettAnalysis;
  ratingProps: ReturnType<typeof getRatingDisplayProps>;
}

function ExecutiveSummarySection({
  analysis,
  ratingProps,
}: ExecutiveSummarySectionProps) {
  return (
    <div className="space-y-4">
      {/* Investment Thesis */}
      <div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground-muted">
          {analysis.investment_thesis}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {/* Rating */}
        <div
          className={cn(
            "rounded-lg border p-3",
            ratingProps.bgClass,
            ratingProps.borderClass
          )}
        >
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Rating
          </p>
          <p className={cn("mt-1 text-lg font-bold", ratingProps.colorClass)}>
            {ratingProps.label}
          </p>
        </div>

        {/* Conviction Level */}
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Conviction
          </p>
          <div className="mt-1 flex items-center gap-2">
            <span
              className={cn(
                "text-lg font-bold font-mono tabular-nums",
                getConvictionColorClass(analysis.conviction_level)
              )}
            >
              {formatConvictionLevel(analysis.conviction_level)}
            </span>
            <div className="flex-1 h-2 rounded-full bg-background-tertiary overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  analysis.conviction_level >= 0.8
                    ? "bg-emerald-500"
                    : analysis.conviction_level >= 0.6
                      ? "bg-green-500"
                      : analysis.conviction_level >= 0.4
                        ? "bg-yellow-500"
                        : "bg-red-500"
                )}
                style={{ width: `${analysis.conviction_level * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Moat */}
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Moat Durability
          </p>
          <p
            className={cn(
              "mt-1 text-lg font-bold",
              getMoatDurabilityDisplayProps(analysis.moat_durability).colorClass
            )}
          >
            {getMoatDurabilityDisplayProps(analysis.moat_durability).label}
          </p>
        </div>

        {/* Simplicity Score */}
        <div className="rounded-lg border border-border bg-background p-3">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Business Simplicity
          </p>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-lg font-bold font-mono tabular-nums text-accent">
              {analysis.business_simplicity_score}/10
            </span>
            <div className="flex gap-0.5">
              {Array.from({ length: 10 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-4 w-1.5 rounded-sm",
                    i < analysis.business_simplicity_score
                      ? "bg-accent"
                      : "bg-background-tertiary"
                  )}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Business Quality Section
 */
interface BusinessQualitySectionProps {
  analysis: WarrenBuffettAnalysis;
}

function BusinessQualitySection({ analysis }: BusinessQualitySectionProps) {
  const [expandedMoat, setExpandedMoat] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      {/* Business Understanding */}
      <div>
        <h4 className="text-sm font-medium text-foreground-muted mb-2">
          Business Understanding
        </h4>
        <p className="text-sm leading-relaxed">{analysis.business_understanding}</p>
      </div>

      {/* Business Simplicity Score Visual */}
      <div className="rounded-lg border border-border bg-background p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium">Business Simplicity Score</h4>
            <p className="mt-0.5 text-xs text-foreground-muted">
              1 = Highly complex, 10 = Simple and predictable
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex gap-1">
              {Array.from({ length: 10 }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-8 w-3 rounded-sm transition-all",
                    i < analysis.business_simplicity_score
                      ? analysis.business_simplicity_score >= 7
                        ? "bg-emerald-500"
                        : analysis.business_simplicity_score >= 4
                          ? "bg-yellow-500"
                          : "bg-red-500"
                      : "bg-background-tertiary"
                  )}
                />
              ))}
            </div>
            <span className="font-mono text-2xl font-bold tabular-nums text-accent">
              {analysis.business_simplicity_score}
            </span>
          </div>
        </div>
      </div>

      {/* Moat Summary */}
      <div className="rounded-lg border border-border bg-background p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium">Economic Moat</h4>
          <span
            className={cn(
              "rounded-full px-3 py-1 text-sm font-medium",
              getMoatDurabilityDisplayProps(analysis.moat_durability).bgClass,
              getMoatDurabilityDisplayProps(analysis.moat_durability).colorClass
            )}
          >
            {getMoatDurabilityDisplayProps(analysis.moat_durability).label}
          </span>
        </div>
        <p className="text-sm text-foreground-muted">{analysis.moat_summary}</p>
      </div>

      {/* Competitive Advantages */}
      {analysis.competitive_advantages.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-foreground-muted">
            Competitive Advantages ({analysis.competitive_advantages.length})
          </h4>
          <div className="space-y-2">
            {analysis.competitive_advantages.map((advantage, index) => (
              <MoatCard
                key={`moat-${advantage.moat_type}-${index}`}
                advantage={advantage}
                isExpanded={expandedMoat === index}
                onToggle={() =>
                  setExpandedMoat(expandedMoat === index ? null : index)
                }
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Moat Card Component
 */
interface MoatCardProps {
  advantage: CompetitiveAdvantage;
  isExpanded: boolean;
  onToggle: () => void;
}

function MoatCard({ advantage, isExpanded, onToggle }: MoatCardProps) {
  const durabilityProps = getMoatDurabilityDisplayProps(advantage.durability);

  return (
    <div className="rounded-lg border border-border bg-background overflow-hidden">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between p-3 text-left hover:bg-background-tertiary transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/10 text-accent">
            <MoatIcon type={advantage.moat_type} />
          </div>
          <div>
            <p className="text-sm font-medium">
              {getMoatTypeLabel(advantage.moat_type)}
            </p>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className={cn(
                  "text-xs",
                  durabilityProps.colorClass
                )}
              >
                {durabilityProps.label}
              </span>
              <span className="text-xs text-foreground-muted">
                Confidence: {(advantage.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
        <svg
          className={cn(
            "h-4 w-4 text-foreground-muted transition-transform",
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

      {isExpanded && (
        <div className="border-t border-border p-3 space-y-3">
          <p className="text-sm text-foreground-muted">
            {advantage.description}
          </p>

          {advantage.evidence.length > 0 && (
            <div>
              <p className="text-xs font-medium text-foreground-muted mb-1">
                Evidence:
              </p>
              <ul className="space-y-1">
                {advantage.evidence.map((item, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-xs text-foreground-muted"
                  >
                    <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-accent" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Confidence Bar */}
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-foreground-muted">Confidence Level</span>
              <span className="font-mono tabular-nums">
                {(advantage.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-background-tertiary overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full",
                  advantage.confidence >= 0.8
                    ? "bg-emerald-500"
                    : advantage.confidence >= 0.6
                      ? "bg-green-500"
                      : advantage.confidence >= 0.4
                        ? "bg-yellow-500"
                        : "bg-red-500"
                )}
                style={{ width: `${advantage.confidence * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Moat Icon Component
 */
function MoatIcon({ type }: { type: string }) {
  switch (type) {
    case "brand":
      return (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      );
    case "network_effects":
      return (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
        </svg>
      );
    case "cost_advantage":
      return (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
        </svg>
      );
    case "switching_costs":
      return (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
        </svg>
      );
    case "efficient_scale":
      return (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      );
    case "intangible_assets":
      return (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
        </svg>
      );
    default:
      return (
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
        </svg>
      );
  }
}

/**
 * Management Section
 */
interface ManagementSectionProps {
  analysis: WarrenBuffettAnalysis;
}

function ManagementSection({ analysis }: ManagementSectionProps) {
  return (
    <div className="space-y-4">
      {/* Management Assessment */}
      <div>
        <p className="text-sm leading-relaxed">{analysis.management_assessment}</p>
      </div>

      {/* Management Metrics */}
      <div className="grid gap-3 sm:grid-cols-3">
        {/* Integrity Score */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Integrity Score
          </p>
          <div className="mt-2 flex items-center gap-3">
            <span className="font-mono text-2xl font-bold tabular-nums text-accent">
              {analysis.management_integrity_score}
            </span>
            <span className="text-foreground-muted">/10</span>
            <div className="flex-1 h-2 rounded-full bg-background-tertiary overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full",
                  analysis.management_integrity_score >= 8
                    ? "bg-emerald-500"
                    : analysis.management_integrity_score >= 6
                      ? "bg-yellow-500"
                      : "bg-red-500"
                )}
                style={{
                  width: `${analysis.management_integrity_score * 10}%`,
                }}
              />
            </div>
          </div>
        </div>

        {/* Capital Allocation */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Capital Allocation
          </p>
          <p className="mt-2 text-sm font-medium">
            {analysis.capital_allocation_skill}
          </p>
        </div>

        {/* Owner Oriented */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Owner-Oriented
          </p>
          <div className="mt-2 flex items-center gap-2">
            {analysis.owner_oriented ? (
              <>
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-positive/20">
                  <svg
                    className="h-4 w-4 text-positive"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <span className="text-sm font-medium text-positive">Yes</span>
              </>
            ) : (
              <>
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-negative/20">
                  <svg
                    className="h-4 w-4 text-negative"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <span className="text-sm font-medium text-negative">No</span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Earnings Power Section
 */
interface EarningsPowerSectionProps {
  analysis: WarrenBuffettAnalysis;
}

function EarningsPowerSection({ analysis }: EarningsPowerSectionProps) {
  const predictabilityProps = getEarningsPredictabilityDisplayProps(
    analysis.earnings_predictability
  );

  return (
    <div className="space-y-4">
      {/* Owner Earnings Analysis */}
      <div>
        <h4 className="text-sm font-medium text-foreground-muted mb-2">
          Owner Earnings Analysis
        </h4>
        <p className="text-sm leading-relaxed">{analysis.owner_earnings_analysis}</p>
      </div>

      {/* Earnings Predictability */}
      <div className="rounded-lg border border-border bg-background p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Earnings Predictability</p>
            <p className="mt-0.5 text-xs text-foreground-muted">
              How confident can we be in future earnings?
            </p>
          </div>
          <span
            className={cn(
              "rounded-full px-3 py-1 text-sm font-medium",
              predictabilityProps.bgClass,
              predictabilityProps.colorClass
            )}
          >
            {predictabilityProps.label}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Financial Health Section
 */
interface FinancialHealthSectionProps {
  analysis: WarrenBuffettAnalysis;
}

function FinancialHealthSection({ analysis }: FinancialHealthSectionProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        {/* Balance Sheet Fortress */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Balance Sheet Fortress
          </p>
          <p className="mt-2 text-sm leading-relaxed">
            {analysis.balance_sheet_fortress}
          </p>
        </div>

        {/* Debt Comfort Level */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Debt Comfort Level
          </p>
          <p className="mt-2 text-sm leading-relaxed">
            {analysis.debt_comfort_level}
          </p>
        </div>

        {/* Cash Generation Power */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Cash Generation Power
          </p>
          <p className="mt-2 text-sm leading-relaxed">
            {analysis.cash_generation_power}
          </p>
        </div>

        {/* Return on Capital Trend */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Return on Capital Trend
          </p>
          <p className="mt-2 text-sm leading-relaxed">
            {analysis.return_on_capital_trend}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Valuation Section
 */
interface ValuationSectionProps {
  analysis: WarrenBuffettAnalysis;
}

function ValuationSection({ analysis }: ValuationSectionProps) {
  return (
    <div className="space-y-4">
      {/* Valuation Narrative */}
      <div>
        <p className="text-sm leading-relaxed">{analysis.valuation_narrative}</p>
      </div>

      {/* Valuation Metrics */}
      <div className="grid gap-3 sm:grid-cols-2">
        {/* Intrinsic Value Range */}
        <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Intrinsic Value Range
          </p>
          <p className="mt-2 font-mono text-lg font-bold tabular-nums text-accent">
            {analysis.intrinsic_value_range}
          </p>
        </div>

        {/* Current Price vs Value */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Current Price vs Value
          </p>
          <p className="mt-2 text-sm leading-relaxed">
            {analysis.current_price_vs_value}
          </p>
        </div>
      </div>

      {/* Margin of Safety Assessment */}
      <div className="rounded-lg border border-border bg-background p-4">
        <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
          Margin of Safety Assessment
        </p>
        <p className="mt-2 text-sm leading-relaxed">
          {analysis.margin_of_safety_assessment}
        </p>
      </div>
    </div>
  );
}

/**
 * Key Considerations Section
 */
interface KeyConsiderationsSectionProps {
  analysis: WarrenBuffettAnalysis;
}

function KeyConsiderationsSection({ analysis }: KeyConsiderationsSectionProps) {
  const [expandedRisk, setExpandedRisk] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      {/* Key Positives */}
      <div className="rounded-lg border border-positive/30 bg-positive/5 p-4">
        <h4 className="text-sm font-medium text-positive mb-3">
          Key Positives
        </h4>
        <ul className="space-y-2">
          {analysis.key_positives.map((positive, index) => (
            <li
              key={`positive-${positive.slice(0, 20)}-${index}`}
              className="flex items-start gap-2 text-sm"
            >
              <svg
                className="mt-0.5 h-4 w-4 flex-shrink-0 text-positive"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              {positive}
            </li>
          ))}
        </ul>
      </div>

      {/* Key Concerns */}
      <div className="rounded-lg border border-orange-500/30 bg-orange-500/5 p-4">
        <h4 className="text-sm font-medium text-orange-400 mb-3">
          Key Concerns
        </h4>
        <ul className="space-y-2">
          {analysis.key_concerns.map((concern, index) => (
            <li
              key={`concern-${concern.slice(0, 20)}-${index}`}
              className="flex items-start gap-2 text-sm"
            >
              <svg
                className="mt-0.5 h-4 w-4 flex-shrink-0 text-orange-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              {concern}
            </li>
          ))}
        </ul>
      </div>

      {/* Key Risks */}
      {analysis.key_risks.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-foreground-muted mb-2">
            Risk Factors ({analysis.key_risks.length})
          </h4>
          <div className="space-y-2">
            {analysis.key_risks.map((risk, index) => (
              <RiskFactorCard
                key={`risk-${risk.title.slice(0, 20)}-${index}`}
                risk={risk}
                isExpanded={expandedRisk === index}
                onToggle={() =>
                  setExpandedRisk(expandedRisk === index ? null : index)
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Potential Catalysts */}
      {analysis.potential_catalysts.length > 0 && (
        <div className="rounded-lg border border-blue-500/30 bg-blue-500/5 p-4">
          <h4 className="text-sm font-medium text-blue-400 mb-3">
            Potential Catalysts
          </h4>
          <ul className="space-y-2">
            {analysis.potential_catalysts.map((catalyst, index) => (
              <li
                key={`catalyst-${catalyst.slice(0, 20)}-${index}`}
                className="flex items-start gap-2 text-sm"
              >
                <svg
                  className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                    clipRule="evenodd"
                  />
                </svg>
                {catalyst}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/**
 * Risk Factor Card Component
 */
interface RiskFactorCardProps {
  risk: RiskFactor;
  isExpanded: boolean;
  onToggle: () => void;
}

function RiskFactorCard({ risk, isExpanded, onToggle }: RiskFactorCardProps) {
  const severityProps = getSeverityDisplayProps(risk.severity);
  const probabilityProps = getProbabilityDisplayProps(risk.probability);

  return (
    <div className="rounded-lg border border-border bg-background overflow-hidden">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between p-3 text-left hover:bg-background-tertiary transition-colors"
      >
        <div className="flex items-center gap-3">
          <span
            className={cn(
              "rounded px-2 py-0.5 text-xs font-medium",
              severityProps.bgClass,
              severityProps.colorClass
            )}
          >
            {severityProps.label}
          </span>
          <div>
            <p className="text-sm font-medium">{risk.title}</p>
            <p className="text-xs text-foreground-muted capitalize">
              {risk.category}
            </p>
          </div>
        </div>
        <svg
          className={cn(
            "h-4 w-4 text-foreground-muted transition-transform",
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

      {isExpanded && (
        <div className="border-t border-border p-3 space-y-3">
          <p className="text-sm text-foreground-muted">{risk.description}</p>

          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <span className="text-foreground-muted">Probability:</span>
              <span className={probabilityProps.colorClass}>
                {probabilityProps.label}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-foreground-muted">Severity:</span>
              <span className={severityProps.colorClass}>
                {severityProps.label}
              </span>
            </div>
          </div>

          {risk.mitigation && (
            <div className="rounded-lg bg-background-tertiary p-2">
              <p className="text-xs font-medium text-foreground-muted mb-1">
                Potential Mitigation:
              </p>
              <p className="text-xs">{risk.mitigation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Time Horizon Section
 */
interface TimeHorizonSectionProps {
  analysis: WarrenBuffettAnalysis;
}

function TimeHorizonSection({ analysis }: TimeHorizonSectionProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        {/* Ideal Holding Period */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Ideal Holding Period
          </p>
          <p className="mt-2 text-lg font-medium">{analysis.ideal_holding_period}</p>
        </div>

        {/* Patience Required */}
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Patience Required
          </p>
          <p className="mt-2 text-lg font-medium">
            {analysis.patience_required_level}
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Final Verdict Section
 */
interface FinalVerdictSectionProps {
  analysis: WarrenBuffettAnalysis;
  ratingProps: ReturnType<typeof getRatingDisplayProps>;
  riskProps: ReturnType<typeof getRiskLevelDisplayProps>;
}

function FinalVerdictSection({
  analysis,
  ratingProps,
  riskProps,
}: FinalVerdictSectionProps) {
  return (
    <div className="space-y-4">
      {/* Main Verdict Display */}
      <div className="grid gap-4 sm:grid-cols-3">
        {/* Investment Rating */}
        <div
          className={cn(
            "rounded-lg border p-6 text-center",
            ratingProps.bgClass,
            ratingProps.borderClass
          )}
        >
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Investment Rating
          </p>
          <p className={cn("mt-2 text-2xl font-bold", ratingProps.colorClass)}>
            {ratingProps.label}
          </p>
        </div>

        {/* Conviction Level */}
        <div className="rounded-lg border border-border bg-background p-6 text-center">
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Conviction Level
          </p>
          <p
            className={cn(
              "mt-2 text-2xl font-bold font-mono tabular-nums",
              getConvictionColorClass(analysis.conviction_level)
            )}
          >
            {formatConvictionLevel(analysis.conviction_level)}
          </p>
          <div className="mt-2 h-2 rounded-full bg-background-tertiary overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                analysis.conviction_level >= 0.8
                  ? "bg-emerald-500"
                  : analysis.conviction_level >= 0.6
                    ? "bg-green-500"
                    : analysis.conviction_level >= 0.4
                      ? "bg-yellow-500"
                      : "bg-red-500"
              )}
              style={{ width: `${analysis.conviction_level * 100}%` }}
            />
          </div>
        </div>

        {/* Risk Level */}
        <div
          className={cn(
            "rounded-lg border p-6 text-center",
            riskProps.bgClass,
            "border-border"
          )}
        >
          <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
            Risk Level
          </p>
          <p className={cn("mt-2 text-2xl font-bold", riskProps.colorClass)}>
            {riskProps.label}
          </p>
        </div>
      </div>

      {/* Suitable For */}
      {analysis.suitable_for.length > 0 && (
        <div className="rounded-lg border border-border bg-background p-4">
          <p className="text-sm font-medium mb-3">Suitable For:</p>
          <div className="flex flex-wrap gap-2">
            {analysis.suitable_for.map((type, index) => (
              <span
                key={`investor-type-${type}-${index}`}
                className="rounded-full bg-accent/10 px-3 py-1 text-sm font-medium text-accent"
              >
                {getInvestorTypeLabel(type)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Closing Section
 */
interface ClosingSectionProps {
  analysis: WarrenBuffettAnalysis;
}

function ClosingSection({ analysis }: ClosingSectionProps) {
  return (
    <div className="space-y-4">
      {/* Buffett Quote */}
      <blockquote className="border-l-4 border-amber-500 bg-amber-500/5 p-4 rounded-r-lg">
        <p className="text-lg italic leading-relaxed">
          &ldquo;{analysis.buffett_quote}&rdquo;
        </p>
        <footer className="mt-2 text-sm text-foreground-muted">
          - Warren Buffett
        </footer>
      </blockquote>

      {/* Final Thoughts */}
      <div>
        <h4 className="text-sm font-medium text-foreground-muted mb-2">
          Final Thoughts
        </h4>
        <p className="text-sm leading-relaxed">{analysis.final_thoughts}</p>
      </div>
    </div>
  );
}

/**
 * Meta Section
 */
interface MetaSectionProps {
  analysis: WarrenBuffettAnalysis;
}

function MetaSection({ analysis }: MetaSectionProps) {
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-xs text-foreground-muted">AI Model</p>
          <p className="text-sm font-mono">{analysis.ai_model_used}</p>
        </div>
        <div>
          <p className="text-xs text-foreground-muted">Analysis Version</p>
          <p className="text-sm font-mono">{analysis.analysis_version}</p>
        </div>
        <div>
          <p className="text-xs text-foreground-muted">Analysis Date</p>
          <p className="text-sm font-mono">
            {new Date(analysis.analysis_date).toLocaleDateString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-foreground-muted">Generation Time</p>
          <p className="text-sm font-mono tabular-nums">
            {analysis.generation_time_seconds
              ? `${analysis.generation_time_seconds.toFixed(1)}s`
              : "N/A"}
          </p>
        </div>
      </div>

      {analysis.tokens_consumed && (
        <div>
          <p className="text-xs text-foreground-muted">Tokens Consumed</p>
          <p className="text-sm font-mono tabular-nums">
            {analysis.tokens_consumed.toLocaleString()}
          </p>
        </div>
      )}

      <p className="text-xs text-foreground-muted italic">
        This analysis is AI-generated and should not be considered financial advice.
        Always conduct your own research and consult with a qualified financial advisor
        before making investment decisions.
      </p>
    </div>
  );
}

/**
 * Loading Skeleton for AI Analysis
 */
interface AnalysisSkeletonProps {
  className?: string;
}

function AnalysisSkeleton({ className }: AnalysisSkeletonProps) {
  return (
    <div
      className={cn(
        "space-y-4 rounded-lg border border-border bg-background-secondary",
        className
      )}
    >
      {/* Header Skeleton */}
      <div className="border-b border-border p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="h-7 w-48 skeleton rounded" />
              <div className="h-7 w-24 skeleton rounded-full" />
            </div>
            <div className="h-4 w-64 skeleton rounded" />
          </div>
          <div className="flex items-center gap-2">
            <div className="h-8 w-24 skeleton rounded-lg" />
            <div className="h-8 w-28 skeleton rounded-lg" />
          </div>
        </div>
        <div className="mt-4 h-20 skeleton rounded-lg" />
      </div>

      {/* Sections Skeleton */}
      <div className="space-y-2 px-6 pb-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border border-border bg-background-tertiary overflow-hidden"
          >
            <div className="flex items-center justify-between p-4">
              <div className="h-5 w-48 skeleton rounded" />
              <div className="h-5 w-5 skeleton rounded" />
            </div>
            {i < 2 && (
              <div className="border-t border-border p-4 space-y-3">
                <div className="h-4 w-full skeleton rounded" />
                <div className="h-4 w-3/4 skeleton rounded" />
                <div className="h-4 w-1/2 skeleton rounded" />
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mt-4">
                  {Array.from({ length: 4 }).map((_, j) => (
                    <div key={j} className="h-20 skeleton rounded-lg" />
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Error State for AI Analysis
 */
interface AnalysisErrorProps {
  error: Error;
  onRetry: () => void;
  className?: string;
}

function AnalysisError({ error, onRetry, className }: AnalysisErrorProps) {
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
            Failed to Load AI Analysis
          </h3>
          <p className="mt-1 text-sm text-foreground-muted">
            {error.message ||
              "An unexpected error occurred while loading AI analysis data."}
          </p>
          <p className="mt-2 text-xs text-foreground-muted">
            AI analysis generation may take 30-60 seconds. If this is a new stock,
            the analysis may need to be generated first.
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

export default AIAnalysis;
