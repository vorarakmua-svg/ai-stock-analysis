"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { COLUMN_CATEGORIES, DEFAULT_VISIBLE_COLUMNS } from "./DataGrid";

/**
 * Props for the ColumnSelector component
 */
interface ColumnSelectorProps {
  /** Currently visible columns */
  visibleColumns: string[];
  /** Callback when column visibility changes */
  onColumnsChange: (columns: string[]) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Column metadata with human-readable labels
 */
const COLUMN_LABELS: Record<string, string> = {
  // Identifiers
  ticker: "Ticker",
  cik: "CIK",
  company_name: "Company Name",
  sector: "Sector",
  industry: "Industry",
  country: "Country",
  website: "Website",
  // Market Data
  current_price: "Price",
  market_cap: "Market Cap",
  volume: "Volume",
  shares_outstanding: "Shares Outstanding",
  float_shares: "Float Shares",
  // Valuation
  pe_trailing: "P/E (TTM)",
  pe_forward: "P/E (Forward)",
  peg_ratio: "PEG Ratio",
  price_to_book: "Price/Book",
  // Earnings
  eps_trailing: "EPS (TTM)",
  eps_forward: "EPS (Forward)",
  // Profitability
  profit_margin: "Profit Margin",
  operating_margin: "Operating Margin",
  return_on_equity: "ROE",
  return_on_assets: "ROA",
  calc_roic: "ROIC",
  // Dividends
  dividend_yield: "Dividend Yield",
  // Income Statement
  total_revenue: "Revenue",
  net_income: "Net Income",
  ebitda: "EBITDA",
  calc_ebitda: "EBITDA (Calc)",
  // Balance Sheet
  total_cash: "Total Cash",
  total_debt: "Total Debt",
  calc_net_debt: "Net Debt",
  debt_to_equity: "Debt/Equity",
  // Cash Flow
  free_cash_flow: "Free Cash Flow",
  calc_fcf: "FCF (Calc)",
  // Calculated Metrics
  calc_ev: "Enterprise Value",
  calc_ev_to_ebitda: "EV/EBITDA",
  calc_interest_coverage: "Interest Coverage",
  // Risk
  beta: "Beta",
  annual_volatility: "Annual Volatility",
  max_drawdown: "Max Drawdown",
  sharpe_ratio: "Sharpe Ratio",
  risk_free_rate_10y: "Risk-Free Rate",
  // Technicals
  "52_week_high": "52W High",
  "52_week_low": "52W Low",
  ma_50: "MA 50",
  ma_200: "MA 200",
  // Performance
  cagr_5y: "5Y CAGR",
  total_return_5y: "5Y Total Return",
  revenue_growth: "Revenue Growth",
  // Ownership
  insider_percent: "Insider %",
  institutional_percent: "Institutional %",
  short_ratio: "Short Ratio",
  // Company Info
  employees: "Employees",
  // SEC Filings
  sec_fiscal_year: "SEC Fiscal Year",
  sec_revenue: "SEC Revenue",
  sec_net_income: "SEC Net Income",
  sec_operating_cash_flow: "SEC Op Cash Flow",
  sec_stockholders_equity: "SEC Equity",
  sec_total_assets: "SEC Total Assets",
  sec_total_liabilities: "SEC Liabilities",
  // Metadata
  collected_at: "Collected At",
  data_sources: "Data Sources",
  treasury_yield_source: "Yield Source",
  error_count: "Errors",
  warning_count: "Warnings",
};

/**
 * Columns icon SVG component
 */
function ColumnsIcon({ className }: { className?: string }): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("w-4 h-4", className)}
    >
      <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
      <line x1="12" x2="12" y1="3" y2="21" />
    </svg>
  );
}

/**
 * Check icon SVG component
 */
function CheckIcon({ className }: { className?: string }): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("w-4 h-4", className)}
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

/**
 * Chevron icon SVG component
 */
function ChevronIcon({
  className,
  direction = "down",
}: {
  className?: string;
  direction?: "up" | "down";
}): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn(
        "w-4 h-4 transition-transform",
        direction === "up" && "rotate-180",
        className
      )}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

/**
 * ColumnSelector Component
 * Dropdown/popover for toggling column visibility in the DataGrid
 */
export function ColumnSelector({
  visibleColumns,
  onColumnsChange,
  className,
}: ColumnSelectorProps): React.ReactElement {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(Object.keys(COLUMN_CATEGORIES))
  );
  const containerRef = useRef<HTMLDivElement>(null);

  /**
   * Handle click outside to close dropdown
   */
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  /**
   * Handle escape key to close dropdown
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  /**
   * Toggle a single column's visibility
   */
  const toggleColumn = useCallback(
    (columnId: string) => {
      const newColumns = visibleColumns.includes(columnId)
        ? visibleColumns.filter((c) => c !== columnId)
        : [...visibleColumns, columnId];
      onColumnsChange(newColumns);
    },
    [visibleColumns, onColumnsChange]
  );

  /**
   * Toggle all columns in a category
   */
  const toggleCategory = useCallback(
    (categoryKey: keyof typeof COLUMN_CATEGORIES) => {
      const categoryColumns = COLUMN_CATEGORIES[categoryKey].columns;
      const allVisible = categoryColumns.every((col) =>
        visibleColumns.includes(col)
      );

      const newColumns = allVisible
        ? visibleColumns.filter((c) => !categoryColumns.includes(c as never))
        : [...new Set([...visibleColumns, ...categoryColumns])];

      onColumnsChange(newColumns);
    },
    [visibleColumns, onColumnsChange]
  );

  /**
   * Show all columns
   */
  const showAll = useCallback(() => {
    const allColumns = Object.values(COLUMN_CATEGORIES).flatMap(
      (cat) => cat.columns
    );
    onColumnsChange([...new Set(allColumns)]);
  }, [onColumnsChange]);

  /**
   * Hide all columns (except ticker)
   */
  const hideAll = useCallback(() => {
    onColumnsChange(["ticker"]);
  }, [onColumnsChange]);

  /**
   * Reset to default columns
   */
  const resetToDefault = useCallback(() => {
    onColumnsChange(DEFAULT_VISIBLE_COLUMNS);
  }, [onColumnsChange]);

  /**
   * Toggle category expansion
   */
  const toggleCategoryExpansion = useCallback((categoryKey: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(categoryKey)) {
        next.delete(categoryKey);
      } else {
        next.add(categoryKey);
      }
      return next;
    });
  }, []);

  /**
   * Get count of visible columns in a category
   */
  const getCategoryVisibleCount = useCallback(
    (categoryKey: keyof typeof COLUMN_CATEGORIES): number => {
      return COLUMN_CATEGORIES[categoryKey].columns.filter((col) =>
        visibleColumns.includes(col)
      ).length;
    },
    [visibleColumns]
  );

  /**
   * Get total visible column count
   */
  const totalVisibleCount = visibleColumns.length;

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 h-10 px-3 text-sm font-medium rounded-lg",
          "bg-background-secondary border border-border",
          "hover:bg-background-tertiary hover:border-border-hover",
          "focus:outline-none focus:ring-1 focus:ring-accent",
          "transition-colors",
          isOpen && "bg-background-tertiary border-accent"
        )}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <ColumnsIcon />
        <span className="hidden sm:inline">Columns</span>
        <span className="text-xs text-foreground-muted">
          ({totalVisibleCount})
        </span>
        <ChevronIcon direction={isOpen ? "up" : "down"} />
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div
          className={cn(
            "absolute right-0 top-full mt-2 z-50",
            "w-80 max-h-[60vh] overflow-hidden",
            "bg-background-secondary border border-border rounded-lg shadow-lg",
            "flex flex-col"
          )}
          role="menu"
        >
          {/* Header with Quick Actions */}
          <div className="flex items-center justify-between p-3 border-b border-border">
            <span className="text-sm font-medium">Column Visibility</span>
            <div className="flex items-center gap-1">
              <button
                onClick={showAll}
                className="px-2 py-1 text-xs text-foreground-muted hover:text-foreground hover:bg-background-tertiary rounded transition-colors"
              >
                Show All
              </button>
              <span className="text-foreground-muted">|</span>
              <button
                onClick={hideAll}
                className="px-2 py-1 text-xs text-foreground-muted hover:text-foreground hover:bg-background-tertiary rounded transition-colors"
              >
                Hide All
              </button>
            </div>
          </div>

          {/* Column Categories */}
          <div className="flex-1 overflow-y-auto">
            {Object.entries(COLUMN_CATEGORIES).map(([key, category]) => {
              const categoryKey = key as keyof typeof COLUMN_CATEGORIES;
              const isExpanded = expandedCategories.has(key);
              const visibleCount = getCategoryVisibleCount(categoryKey);
              const totalCount = category.columns.length;
              const allVisible = visibleCount === totalCount;

              return (
                <div key={key} className="border-b border-border last:border-b-0">
                  {/* Category Header */}
                  <div
                    className={cn(
                      "flex items-center justify-between w-full px-3 py-2",
                      "hover:bg-background-tertiary transition-colors"
                    )}
                  >
                    <button
                      onClick={() => toggleCategoryExpansion(key)}
                      className="flex items-center gap-2 flex-1 text-left"
                      aria-expanded={isExpanded}
                    >
                      <ChevronIcon
                        direction={isExpanded ? "up" : "down"}
                        className="text-foreground-muted"
                      />
                      <span className="text-sm font-medium">{category.label}</span>
                    </button>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-foreground-muted">
                        {visibleCount}/{totalCount}
                      </span>
                      <button
                        onClick={() => toggleCategory(categoryKey)}
                        className={cn(
                          "w-4 h-4 rounded border flex items-center justify-center",
                          "transition-colors",
                          allVisible
                            ? "bg-accent border-accent text-white"
                            : visibleCount > 0
                            ? "bg-accent/30 border-accent/50"
                            : "border-border hover:border-accent"
                        )}
                        aria-label={`Toggle all ${category.label} columns`}
                      >
                        {(allVisible || visibleCount > 0) && (
                          <CheckIcon className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Column Checkboxes */}
                  {isExpanded && (
                    <div className="pb-2">
                      {category.columns.map((columnId) => {
                        const isVisible = visibleColumns.includes(columnId);
                        const label =
                          COLUMN_LABELS[columnId] || columnId;

                        return (
                          <label
                            key={columnId}
                            className={cn(
                              "flex items-center gap-3 px-3 py-1.5 pl-9 cursor-pointer",
                              "hover:bg-background-tertiary transition-colors"
                            )}
                          >
                            <div
                              className={cn(
                                "w-4 h-4 rounded border flex items-center justify-center flex-shrink-0",
                                "transition-colors",
                                isVisible
                                  ? "bg-accent border-accent text-white"
                                  : "border-border"
                              )}
                            >
                              {isVisible && <CheckIcon className="w-3 h-3" />}
                            </div>
                            <input
                              type="checkbox"
                              checked={isVisible}
                              onChange={() => toggleColumn(columnId)}
                              className="sr-only"
                            />
                            <span className="text-sm">{label}</span>
                          </label>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-border">
            <button
              onClick={resetToDefault}
              className={cn(
                "w-full px-3 py-2 text-sm font-medium rounded",
                "bg-background-tertiary border border-border",
                "hover:bg-background hover:border-border-hover",
                "transition-colors"
              )}
            >
              Reset to Default
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ColumnSelector;
