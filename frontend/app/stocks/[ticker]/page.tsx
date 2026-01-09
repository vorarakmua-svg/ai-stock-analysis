"use client";

import { useStock } from "@/hooks/useStocks";
import {
  formatCurrency,
  formatPercent,
  formatMarketCap,
  formatRatio,
  formatLargeNumber,
  getValueColorClass,
  cn,
} from "@/lib/utils";
import Link from "next/link";
import { use } from "react";
import { PriceHeader, ValuationCard, AIAnalysis } from "@/components/stock";
import { CandlestickChart } from "@/components/charts";

interface StockDetailPageProps {
  params: Promise<{
    ticker: string;
  }>;
}

/**
 * Stock Detail Page
 * Displays comprehensive stock information with financials, valuation, and analysis
 */
export default function StockDetailPage({
  params,
}: StockDetailPageProps) {
  // Unwrap the params Promise using React.use()
  const { ticker } = use(params);
  const upperTicker = ticker.toUpperCase();

  const { data: stock, isLoading, error, isError } = useStock(upperTicker);

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link
        href="/"
        className="inline-flex items-center text-sm text-foreground-muted transition-colors hover:text-accent"
      >
        <svg
          className="mr-1 h-4 w-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back to Screener
      </Link>

      {/* Error State */}
      {isError && (
        <div className="rounded-lg border border-negative/50 bg-negative/10 p-6">
          <h3 className="text-lg font-semibold text-negative">
            Error Loading Stock
          </h3>
          <p className="mt-2 text-foreground-muted">
            {error?.message ||
              `Failed to fetch data for ${upperTicker}. Please try again.`}
          </p>
          <p className="mt-2 text-sm text-foreground-muted">
            Make sure the backend server is running and accessible.
          </p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-6">
          {/* Header Skeleton */}
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="h-10 w-48 skeleton rounded" />
              <div className="h-6 w-64 skeleton rounded" />
            </div>
            <div className="text-right">
              <div className="h-10 w-32 skeleton rounded" />
              <div className="mt-2 h-5 w-24 skeleton rounded" />
            </div>
          </div>

          {/* Metrics Grid Skeleton */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-border p-4">
                <div className="h-4 w-20 skeleton rounded" />
                <div className="mt-2 h-6 w-16 skeleton rounded" />
              </div>
            ))}
          </div>

          {/* Content Skeleton */}
          <div className="h-96 skeleton rounded-lg" />
        </div>
      )}

      {/* Stock Detail Content */}
      {!isLoading && !isError && stock && (
        <>
          {/* Stock Header with Ticker and Sector */}
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold tracking-tight">
                  {stock.ticker}
                </h1>
                <span className="rounded-full bg-background-tertiary px-3 py-1 text-xs font-medium text-foreground-muted">
                  {stock.sector}
                </span>
              </div>
              <p className="mt-1 text-lg text-foreground-muted">
                {stock.company_name}
              </p>
              <p className="text-sm text-foreground-muted">{stock.industry}</p>
            </div>
            {stock.cagr_5y && (
              <div className="text-right">
                <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
                  5Y CAGR
                </p>
                <p
                  className={cn(
                    "mt-0.5 font-mono text-lg font-semibold tabular-nums",
                    getValueColorClass(stock.cagr_5y)
                  )}
                >
                  {formatPercent(stock.cagr_5y)}
                </p>
              </div>
            )}
          </div>

          {/* Real-Time Price Header */}
          <PriceHeader
            ticker={upperTicker}
            companyName={stock.company_name}
          />

          {/* Candlestick Chart */}
          <CandlestickChart
            ticker={upperTicker}
            initialPeriod="1y"
            height={500}
          />

          {/* Valuation Analysis Card */}
          <ValuationCard ticker={upperTicker} />

          {/* AI Investment Analysis */}
          <AIAnalysis ticker={upperTicker} />

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-5">
            <MetricCard
              label="Market Cap"
              value={formatMarketCap(stock.market_cap)}
            />
            <MetricCard
              label="P/E Ratio"
              value={stock.pe_trailing ? formatRatio(stock.pe_trailing) : "N/A"}
            />
            <MetricCard
              label="Forward P/E"
              value={stock.pe_forward ? formatRatio(stock.pe_forward) : "N/A"}
            />
            <MetricCard
              label="Dividend Yield"
              value={
                stock.dividend_yield
                  ? formatPercent(stock.dividend_yield)
                  : "-"
              }
              valueClassName={
                stock.dividend_yield && stock.dividend_yield > 0
                  ? "text-positive"
                  : undefined
              }
            />
            <MetricCard
              label="Beta"
              value={stock.beta?.toFixed(2) ?? "N/A"}
            />
            <MetricCard
              label="ROE"
              value={
                stock.return_on_equity
                  ? formatPercent(stock.return_on_equity)
                  : "N/A"
              }
              valueClassName={getValueColorClass(stock.return_on_equity)}
            />
            <MetricCard
              label="ROA"
              value={
                stock.return_on_assets
                  ? formatPercent(stock.return_on_assets)
                  : "N/A"
              }
              valueClassName={getValueColorClass(stock.return_on_assets)}
            />
            <MetricCard
              label="Profit Margin"
              value={
                stock.profit_margin
                  ? formatPercent(stock.profit_margin)
                  : "N/A"
              }
              valueClassName={getValueColorClass(stock.profit_margin)}
            />
            <MetricCard
              label="Operating Margin"
              value={
                stock.operating_margin
                  ? formatPercent(stock.operating_margin)
                  : "N/A"
              }
              valueClassName={getValueColorClass(stock.operating_margin)}
            />
            <MetricCard
              label="Debt/Equity"
              value={
                stock.debt_to_equity
                  ? `${stock.debt_to_equity.toFixed(2)}x`
                  : "N/A"
              }
              valueClassName={
                stock.debt_to_equity && stock.debt_to_equity > 1
                  ? "text-negative"
                  : undefined
              }
            />
          </div>

          {/* Financial Details */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Income Statement Highlights */}
            <div className="rounded-lg border border-border bg-background-secondary p-6">
              <h2 className="mb-4 text-lg font-semibold">Income Statement</h2>
              <div className="space-y-3">
                <DetailRow
                  label="Revenue (TTM)"
                  value={formatLargeNumber(stock.total_revenue)}
                />
                <DetailRow
                  label="Net Income (TTM)"
                  value={formatLargeNumber(stock.net_income)}
                />
                <DetailRow
                  label="EBITDA"
                  value={formatLargeNumber(stock.ebitda || stock.calc_ebitda)}
                />
                <DetailRow
                  label="EPS (TTM)"
                  value={formatCurrency(stock.eps_trailing ?? 0)}
                />
                <DetailRow
                  label="EPS (Forward)"
                  value={formatCurrency(stock.eps_forward ?? 0)}
                />
                <DetailRow
                  label="Revenue Growth"
                  value={
                    stock.revenue_growth
                      ? formatPercent(stock.revenue_growth)
                      : "N/A"
                  }
                  valueClassName={getValueColorClass(stock.revenue_growth)}
                />
              </div>
            </div>

            {/* Balance Sheet Highlights */}
            <div className="rounded-lg border border-border bg-background-secondary p-6">
              <h2 className="mb-4 text-lg font-semibold">Balance Sheet</h2>
              <div className="space-y-3">
                <DetailRow
                  label="Total Cash"
                  value={formatLargeNumber(stock.total_cash)}
                />
                <DetailRow
                  label="Total Debt"
                  value={formatLargeNumber(stock.total_debt)}
                />
                <DetailRow
                  label="Net Debt"
                  value={formatLargeNumber(stock.calc_net_debt)}
                  valueClassName={getValueColorClass(
                    stock.calc_net_debt ? -stock.calc_net_debt : null
                  )}
                />
                <DetailRow
                  label="Enterprise Value"
                  value={formatLargeNumber(stock.calc_ev)}
                />
                <DetailRow
                  label="EV/EBITDA"
                  value={
                    stock.calc_ev_to_ebitda
                      ? formatRatio(stock.calc_ev_to_ebitda)
                      : "N/A"
                  }
                />
                <DetailRow
                  label="Price/Book"
                  value={
                    stock.price_to_book
                      ? formatRatio(stock.price_to_book)
                      : "N/A"
                  }
                />
              </div>
            </div>
          </div>

          {/* 52-Week Range */}
          <div className="rounded-lg border border-border bg-background-secondary p-6">
            <h2 className="mb-4 text-lg font-semibold">52-Week Range</h2>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-foreground-muted">
                  Low: {formatCurrency(stock["52_week_low"])}
                </span>
                <span className="text-foreground-muted">
                  High: {formatCurrency(stock["52_week_high"])}
                </span>
              </div>
              <div className="relative h-2 rounded-full bg-background-tertiary">
                {stock["52_week_low"] !== null &&
                  stock["52_week_high"] !== null &&
                  stock.current_price !== null &&
                  stock["52_week_high"] > stock["52_week_low"] && (
                    <div
                      className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent"
                      style={{
                        left: `${Math.max(0, Math.min(100,
                          ((stock.current_price - stock["52_week_low"]) /
                            (stock["52_week_high"] - stock["52_week_low"])) *
                          100
                        ))}%`,
                      }}
                    />
                  )}
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-foreground-muted">
                  MA50: {formatCurrency(stock.ma_50)}
                </span>
                <span className="text-foreground-muted">
                  MA200: {formatCurrency(stock.ma_200)}
                </span>
              </div>
            </div>
          </div>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-4 text-xs text-foreground-muted">
            <span>
              Data collected:{" "}
              {stock.collected_at
                ? new Date(stock.collected_at).toLocaleString()
                : "N/A"}
            </span>
            <span>Sources: {stock.data_sources}</span>
            {stock.website && (
              <a
                href={stock.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline"
              >
                Company Website
              </a>
            )}
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Metric Card Component
 */
interface MetricCardProps {
  label: string;
  value: string;
  valueClassName?: string;
}

function MetricCard({
  label,
  value,
  valueClassName,
}: MetricCardProps) {
  return (
    <div className="rounded-lg border border-border bg-background-secondary p-4">
      <p className="text-xs font-medium uppercase tracking-wider text-foreground-muted">
        {label}
      </p>
      <p
        className={cn(
          "mt-1 font-mono text-lg font-semibold tabular-nums",
          valueClassName
        )}
      >
        {value}
      </p>
    </div>
  );
}

/**
 * Detail Row Component
 */
interface DetailRowProps {
  label: string;
  value: string;
  valueClassName?: string;
}

function DetailRow({
  label,
  value,
  valueClassName,
}: DetailRowProps) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-foreground-muted">{label}</span>
      <span
        className={cn("font-mono text-sm font-medium tabular-nums", valueClassName)}
      >
        {value}
      </span>
    </div>
  );
}
