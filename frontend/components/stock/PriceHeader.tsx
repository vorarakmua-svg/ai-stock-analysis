"use client";

import type { ReactElement } from "react";
import { useRealTimePrice } from "@/hooks/useStocks";
import { formatCurrency, formatNumber, cn } from "@/lib/utils";
import type { MarketState } from "@/types/stock";

/**
 * Props for PriceHeader component
 */
interface PriceHeaderProps {
  /** Stock ticker symbol */
  ticker: string;
  /** Company name to display */
  companyName?: string;
  /** Enable/disable real-time price fetching */
  enabled?: boolean;
}

/**
 * Market state badge configuration
 */
const marketStateBadge: Record<
  MarketState,
  { label: string; className: string }
> = {
  PRE: {
    label: "Pre-Market",
    className: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  },
  REGULAR: {
    label: "Market Open",
    className: "bg-positive/20 text-positive border-positive/30",
  },
  POST: {
    label: "After Hours",
    className: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  },
  CLOSED: {
    label: "Market Closed",
    className: "bg-foreground-muted/20 text-foreground-muted border-foreground-muted/30",
  },
};

/**
 * Format time since last update
 */
function formatTimeAgo(timestamp: string): string {
  const now = new Date();
  const updated = new Date(timestamp);
  const diffSeconds = Math.floor((now.getTime() - updated.getTime()) / 1000);

  if (diffSeconds < 60) {
    return `${diffSeconds}s ago`;
  }
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  const diffHours = Math.floor(diffMinutes / 60);
  return `${diffHours}h ago`;
}

/**
 * Loading skeleton for PriceHeader
 */
function PriceHeaderSkeleton(): ReactElement {
  return (
    <div className="rounded-lg border border-border bg-background-secondary p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        {/* Left side - Price info skeleton */}
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="h-12 w-40 skeleton rounded" />
            <div className="h-6 w-24 skeleton rounded-full" />
          </div>
          <div className="flex items-center gap-4">
            <div className="h-6 w-20 skeleton rounded" />
            <div className="h-6 w-24 skeleton rounded" />
          </div>
        </div>

        {/* Right side - Stats skeleton */}
        <div className="flex gap-6">
          <div className="space-y-1">
            <div className="h-4 w-12 skeleton rounded" />
            <div className="h-5 w-16 skeleton rounded" />
          </div>
          <div className="space-y-1">
            <div className="h-4 w-12 skeleton rounded" />
            <div className="h-5 w-16 skeleton rounded" />
          </div>
          <div className="space-y-1">
            <div className="h-4 w-12 skeleton rounded" />
            <div className="h-5 w-20 skeleton rounded" />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * PriceHeader Component
 * Displays real-time stock price with change indicators and market status
 */
export function PriceHeader({
  ticker,
  companyName,
  enabled = true,
}: PriceHeaderProps): ReactElement {
  const {
    data: priceData,
    isLoading,
    isError,
    error,
    dataUpdatedAt,
    isFetching,
    refetch,
  } = useRealTimePrice(ticker, enabled);

  // Loading state
  if (isLoading) {
    return <PriceHeaderSkeleton />;
  }

  // Error state
  if (isError) {
    return (
      <div className="rounded-lg border border-negative/50 bg-negative/10 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
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
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <p className="font-medium text-negative">
                Failed to load price data
              </p>
              <p className="text-sm text-foreground-muted">
                {error?.message || "Unable to fetch real-time price"}
              </p>
            </div>
          </div>
          <button
            onClick={() => refetch()}
            className="rounded-lg bg-negative/20 px-4 py-2 text-sm font-medium text-negative transition-colors hover:bg-negative/30"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // No data state
  if (!priceData) {
    return (
      <div className="rounded-lg border border-border bg-background-secondary p-6">
        <p className="text-foreground-muted">No price data available</p>
      </div>
    );
  }

  const { price, change, change_percent, volume, high, low, open, market_state, timestamp } =
    priceData;
  const isPositive = change >= 0;
  const changeColor = isPositive ? "text-positive" : "text-negative";
  const badge = marketStateBadge[market_state];

  return (
    <div className="rounded-lg border border-border bg-background-secondary p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        {/* Left side - Main price display */}
        <div className="space-y-2">
          {/* Ticker and market status */}
          <div className="flex flex-wrap items-center gap-3">
            {companyName && (
              <span className="text-sm text-foreground-muted">{companyName}</span>
            )}
            <span
              className={cn(
                "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
                badge.className
              )}
            >
              {badge.label}
            </span>
          </div>

          {/* Price and change */}
          <div className="flex flex-wrap items-baseline gap-4">
            <span className="font-mono text-5xl font-bold tabular-nums tracking-tight">
              {formatCurrency(price)}
            </span>
            <div className="flex items-baseline gap-2">
              <span className={cn("font-mono text-xl font-semibold tabular-nums", changeColor)}>
                {isPositive ? "+" : ""}
                {formatCurrency(change)}
              </span>
              <span className={cn("font-mono text-lg tabular-nums", changeColor)}>
                ({isPositive ? "+" : ""}
                {change_percent.toFixed(2)}%)
              </span>
            </div>
          </div>

          {/* Update indicator */}
          <div className="flex items-center gap-2 text-xs text-foreground-muted">
            {isFetching && (
              <span className="flex items-center gap-1">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-accent" />
                Updating...
              </span>
            )}
            {!isFetching && dataUpdatedAt && (
              <span>
                Updated {formatTimeAgo(new Date(dataUpdatedAt).toISOString())}
              </span>
            )}
            <span className="text-foreground-muted/50">|</span>
            <span>Auto-refresh: 30s</span>
          </div>
        </div>

        {/* Right side - Additional stats */}
        <div className="flex flex-wrap gap-6 border-t border-border pt-4 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
          {/* Open */}
          {open !== null && (
            <div className="min-w-[80px]">
              <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
                Open
              </p>
              <p className="mt-0.5 font-mono text-sm font-medium tabular-nums">
                {formatCurrency(open)}
              </p>
            </div>
          )}

          {/* High */}
          {high !== null && (
            <div className="min-w-[80px]">
              <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
                High
              </p>
              <p className="mt-0.5 font-mono text-sm font-medium tabular-nums text-positive">
                {formatCurrency(high)}
              </p>
            </div>
          )}

          {/* Low */}
          {low !== null && (
            <div className="min-w-[80px]">
              <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
                Low
              </p>
              <p className="mt-0.5 font-mono text-sm font-medium tabular-nums text-negative">
                {formatCurrency(low)}
              </p>
            </div>
          )}

          {/* Volume */}
          <div className="min-w-[100px]">
            <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
              Volume
            </p>
            <p className="mt-0.5 font-mono text-sm font-medium tabular-nums">
              {formatNumber(volume)}
            </p>
          </div>
        </div>
      </div>

      {/* Day range bar */}
      {high !== null && low !== null && price !== null && high > low && (
        <div className="mt-4 border-t border-border pt-4">
          <div className="flex items-center justify-between text-xs text-foreground-muted">
            <span>Day Range</span>
            <span>
              {formatCurrency(low)} - {formatCurrency(high)}
            </span>
          </div>
          <div className="relative mt-2 h-1.5 rounded-full bg-background-tertiary">
            <div
              className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent shadow-lg shadow-accent/25"
              style={{
                left: `${Math.max(0, Math.min(100, ((price - low) / (high - low)) * 100))}%`,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default PriceHeader;
