"use client";

import { useEffect, useRef, useState, useCallback, type ReactElement } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  Time,
  ColorType,
  CrosshairMode,
} from "lightweight-charts";
import { useStockHistory } from "@/hooks/useStocks";
import { cn } from "@/lib/utils";
import type { ChartPeriod, HistoricalDataPoint } from "@/types/stock";

/**
 * Props for CandlestickChart component
 */
interface CandlestickChartProps {
  /** Stock ticker symbol */
  ticker: string;
  /** Initial chart period */
  initialPeriod?: ChartPeriod;
  /** Chart height in pixels */
  height?: number;
  /** Enable/disable the chart */
  enabled?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Period button configuration
 */
interface PeriodButton {
  value: ChartPeriod;
  label: string;
  ariaLabel: string;
}

const periodButtons: PeriodButton[] = [
  { value: "1mo", label: "1M", ariaLabel: "Show 1 month of price data" },
  { value: "3mo", label: "3M", ariaLabel: "Show 3 months of price data" },
  { value: "6mo", label: "6M", ariaLabel: "Show 6 months of price data" },
  { value: "1y", label: "1Y", ariaLabel: "Show 1 year of price data" },
  { value: "5y", label: "5Y", ariaLabel: "Show 5 years of price data" },
];

/**
 * Bloomberg-style dark theme colors for the chart
 */
const chartColors = {
  background: "#0a0a0a",
  textColor: "#a1a1aa",
  gridColor: "#27272a",
  borderColor: "#27272a",
  crosshairColor: "#71717a",
  upColor: "#22c55e",
  downColor: "#ef4444",
  upWickColor: "#22c55e",
  downWickColor: "#ef4444",
  volumeUp: "rgba(34, 197, 94, 0.3)",
  volumeDown: "rgba(239, 68, 68, 0.3)",
};

/**
 * Validate and convert time value to lightweight-charts Time format
 * Handles both Unix timestamps (number) and date strings
 */
function parseTimeValue(timeValue: number | string): Time {
  // If it's a number, treat it as Unix timestamp (seconds)
  if (typeof timeValue === "number") {
    // lightweight-charts can use Unix timestamps directly
    return timeValue as Time;
  }

  // If it's a string, validate YYYY-MM-DD format
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (dateRegex.test(timeValue)) {
    return timeValue as Time;
  }

  // Fallback: try to parse and reformat the date
  const date = new Date(timeValue);
  if (!isNaN(date.getTime())) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}` as Time;
  }

  // Last resort: return as-is and let the chart handle it
  return timeValue as Time;
}

/**
 * Convert HistoricalDataPoint to Lightweight Charts format
 */
function transformToCandlestickData(data: HistoricalDataPoint[]): CandlestickData<Time>[] {
  return data.map((point) => ({
    time: parseTimeValue(point.time),
    open: point.open,
    high: point.high,
    low: point.low,
    close: point.close,
  }));
}

/**
 * Convert HistoricalDataPoint to volume histogram data
 */
function transformToVolumeData(
  data: HistoricalDataPoint[]
): HistogramData<Time>[] {
  return data.map((point) => ({
    time: parseTimeValue(point.time),
    value: point.volume,
    color: point.close >= point.open ? chartColors.volumeUp : chartColors.volumeDown,
  }));
}

/**
 * Loading skeleton for the chart
 */
function ChartSkeleton({ height }: { height: number }): ReactElement {
  return (
    <div
      className="rounded-lg border border-border bg-background-secondary"
      style={{ height: `${height}px` }}
    >
      <div className="flex h-full flex-col">
        {/* Period selector skeleton */}
        <div className="flex items-center justify-between border-b border-border p-4">
          <div className="h-5 w-32 skeleton rounded" />
          <div className="flex gap-2">
            {periodButtons.map((_, i) => (
              <div key={i} className="h-8 w-10 skeleton rounded" />
            ))}
          </div>
        </div>
        {/* Chart area skeleton */}
        <div className="flex-1 p-4">
          <div className="h-full w-full skeleton rounded" />
        </div>
      </div>
    </div>
  );
}

/**
 * Error display for the chart
 */
function ChartError({ message }: { message: string }): ReactElement {
  return (
    <div className="flex h-full items-center justify-center rounded-lg border border-negative/50 bg-negative/10 p-6">
      <div className="text-center">
        <svg
          className="mx-auto h-12 w-12 text-negative"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="mt-2 font-medium text-negative">Failed to load chart</p>
        <p className="mt-1 text-sm text-foreground-muted">{message}</p>
      </div>
    </div>
  );
}

/**
 * CandlestickChart Component
 * Displays OHLCV data with TradingView-style candlestick chart
 */
export function CandlestickChart({
  ticker,
  initialPeriod = "1y",
  height = 500,
  enabled = true,
  className,
}: CandlestickChartProps): ReactElement {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

  const [period, setPeriod] = useState<ChartPeriod>(initialPeriod);

  const {
    data: historyData,
    isLoading,
    isError,
    error,
    isFetching,
  } = useStockHistory(ticker, period, enabled);

  /**
   * Initialize chart on mount
   */
  useEffect(() => {
    if (!chartContainerRef.current) {
      return;
    }

    if (chartRef.current) {
      return;
    }

    const containerWidth = chartContainerRef.current.clientWidth || 800;
    const chartHeight = height - 80; // Account for header

    const chart = createChart(chartContainerRef.current, {
      width: containerWidth,
      height: chartHeight,
      layout: {
        background: { type: ColorType.Solid, color: chartColors.background },
        textColor: chartColors.textColor,
      },
      grid: {
        vertLines: { color: chartColors.gridColor },
        horzLines: { color: chartColors.gridColor },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: chartColors.crosshairColor,
          width: 1,
          style: 2,
          labelBackgroundColor: "#27272a",
        },
        horzLine: {
          color: chartColors.crosshairColor,
          width: 1,
          style: 2,
          labelBackgroundColor: "#27272a",
        },
      },
      rightPriceScale: {
        borderColor: chartColors.borderColor,
        scaleMargins: {
          top: 0.1,
          bottom: 0.25, // Leave room for volume
        },
      },
      timeScale: {
        borderColor: chartColors.borderColor,
        timeVisible: true,
        secondsVisible: false,
      },
      handleScale: {
        axisPressedMouseMove: true,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
    });

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: chartColors.upColor,
      downColor: chartColors.downColor,
      wickUpColor: chartColors.upWickColor,
      wickDownColor: chartColors.downWickColor,
      borderVisible: false,
    });

    // Create volume series
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "", // Use overlay mode
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.85, // Volume at bottom 15%
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // Handle resize
    const handleResize = (): void => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        candlestickSeriesRef.current = null;
        volumeSeriesRef.current = null;
      }
    };
  }, [height]);

  /**
   * Update chart data when history data changes
   */
  useEffect(() => {
    if (!historyData) {
      return;
    }

    // Track if this effect is still valid (not superseded by new data)
    let isCurrentEffect = true;

    // Function to update chart data
    const updateChartData = () => {
      // Don't update if this effect has been superseded
      if (!isCurrentEffect) {
        return false;
      }
      if (!candlestickSeriesRef.current || !volumeSeriesRef.current) {
        return false;
      }

      const candlestickData = transformToCandlestickData(historyData);
      const volumeData = transformToVolumeData(historyData);

      candlestickSeriesRef.current.setData(candlestickData);
      volumeSeriesRef.current.setData(volumeData);

      // Fit content to view
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
      }
      return true;
    };

    // Try to update immediately
    if (updateChartData()) {
      return () => {
        isCurrentEffect = false;
      };
    }

    // If chart not ready yet, retry after a short delay
    const retryTimeout = setTimeout(() => {
      updateChartData();
    }, 100);

    return () => {
      isCurrentEffect = false;
      clearTimeout(retryTimeout);
    };
  }, [historyData]);

  /**
   * Handle period change
   */
  const handlePeriodChange = useCallback((newPeriod: ChartPeriod) => {
    setPeriod(newPeriod);
  }, []);

  // Always render the chart container so the ref is attached
  // Show loading overlay on top when loading
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-background-secondary",
        className
      )}
      style={{ height: `${height}px` }}
    >
      {/* Header with period selector */}
      <div className="flex items-center justify-between border-b border-border p-4">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-medium text-foreground-muted">
            Price Chart
          </h3>
          {(isLoading || isFetching) && (
            <span className="flex items-center gap-1.5 text-xs text-foreground-muted">
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-accent" />
              Loading...
            </span>
          )}
        </div>

        {/* Period selector buttons */}
        <div className="flex gap-1" role="group" aria-label="Chart time period selection">
          {periodButtons.map((btn) => (
            <button
              key={btn.value}
              onClick={() => handlePeriodChange(btn.value)}
              disabled={isLoading || isFetching}
              aria-label={btn.ariaLabel}
              aria-pressed={period === btn.value}
              className={cn(
                "rounded px-3 py-1.5 text-xs font-medium transition-colors",
                period === btn.value
                  ? "bg-accent text-white"
                  : "bg-background-tertiary text-foreground-muted hover:bg-background-tertiary/80 hover:text-foreground",
                (isLoading || isFetching) && "cursor-not-allowed opacity-50"
              )}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart container - explicit height to match chart initialization */}
      <div
        className="relative"
        style={{ height: `${height - 80}px` }}
      >
        {/* Loading overlay */}
        {isLoading && !historyData && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-background-secondary">
            <div className="flex flex-col items-center gap-3">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
              <span className="text-sm text-foreground-muted">Loading chart data...</span>
            </div>
          </div>
        )}
        {isError ? (
          <ChartError message={error?.message || "Unable to load chart data"} />
        ) : (
          <div
            ref={chartContainerRef}
            className="w-full"
            style={{ height: `${height - 80}px` }}
          />
        )}
      </div>
    </div>
  );
}

export default CandlestickChart;
