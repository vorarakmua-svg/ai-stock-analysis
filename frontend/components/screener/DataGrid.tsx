"use client";

import React, { useMemo, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { AgGridReact } from "ag-grid-react";
import type {
  ColDef,
  ValueFormatterParams,
  CellClassParams,
  GridReadyEvent,
  RowClickedEvent,
  GridApi,
  SortChangedEvent,
} from "ag-grid-community";
import { themeQuartz } from "ag-grid-community";

import type { StockSummary } from "@/types/stock";
import {
  formatCurrency,
  formatPercent,
  formatMarketCap,
  formatRatio,
  cn,
} from "@/lib/utils";

/**
 * Props for the DataGrid component
 */
interface DataGridProps {
  /** Array of stock data to display */
  stocks: StockSummary[];
  /** Columns to show (by field name) */
  visibleColumns?: string[];
  /** Search filter text */
  searchText?: string;
  /** Callback when sort changes */
  onSortChange?: (sortBy: string, sortOrder: "asc" | "desc") => void;
  /** Loading state */
  isLoading?: boolean;
}

/**
 * Column category definitions for organization
 */
export const COLUMN_CATEGORIES = {
  identifiers: {
    label: "Identifiers",
    columns: ["ticker", "cik", "company_name", "sector", "industry", "country", "website"],
  },
  marketData: {
    label: "Market Data",
    columns: ["current_price", "market_cap", "volume", "shares_outstanding", "float_shares"],
  },
  valuation: {
    label: "Valuation",
    columns: ["pe_trailing", "pe_forward", "peg_ratio", "price_to_book"],
  },
  earnings: {
    label: "Earnings",
    columns: ["eps_trailing", "eps_forward"],
  },
  profitability: {
    label: "Profitability",
    columns: ["profit_margin", "operating_margin", "return_on_equity", "return_on_assets", "calc_roic"],
  },
  dividends: {
    label: "Dividends",
    columns: ["dividend_yield"],
  },
  incomeStatement: {
    label: "Income Statement",
    columns: ["total_revenue", "net_income", "ebitda", "calc_ebitda"],
  },
  balanceSheet: {
    label: "Balance Sheet",
    columns: ["total_cash", "total_debt", "calc_net_debt", "debt_to_equity"],
  },
  cashFlow: {
    label: "Cash Flow",
    columns: ["free_cash_flow", "calc_fcf"],
  },
  calculatedMetrics: {
    label: "Calculated Metrics",
    columns: ["calc_ev", "calc_ev_to_ebitda", "calc_interest_coverage"],
  },
  risk: {
    label: "Risk Metrics",
    columns: ["beta", "annual_volatility", "max_drawdown", "sharpe_ratio", "risk_free_rate_10y"],
  },
  technicals: {
    label: "Technicals",
    columns: ["52_week_high", "52_week_low", "ma_50", "ma_200"],
  },
  performance: {
    label: "Performance",
    columns: ["cagr_5y", "total_return_5y", "revenue_growth"],
  },
  ownership: {
    label: "Ownership",
    columns: ["insider_percent", "institutional_percent", "short_ratio"],
  },
  companyInfo: {
    label: "Company Info",
    columns: ["employees"],
  },
  secFilings: {
    label: "SEC Filings",
    columns: ["sec_fiscal_year", "sec_revenue", "sec_net_income", "sec_operating_cash_flow", "sec_stockholders_equity", "sec_total_assets", "sec_total_liabilities"],
  },
  metadata: {
    label: "Metadata",
    columns: ["collected_at", "data_sources", "treasury_yield_source", "error_count", "warning_count"],
  },
} as const;

/**
 * Default visible columns
 */
export const DEFAULT_VISIBLE_COLUMNS = [
  "ticker",
  "company_name",
  "sector",
  "current_price",
  "market_cap",
  "pe_trailing",
  "dividend_yield",
  "profit_margin",
  "return_on_equity",
  "beta",
  "cagr_5y",
];

/**
 * Custom cell class for positive/negative values
 */
function getValueCellClass(params: CellClassParams): string {
  const value = params.value as number | null | undefined;
  if (value === null || value === undefined || isNaN(value)) {
    return "text-foreground-muted";
  }
  if (value > 0) return "text-positive";
  if (value < 0) return "text-negative";
  return "text-foreground-muted";
}

/**
 * Custom cell class for percentage values (always show color)
 */
function getPercentCellClass(params: CellClassParams): string {
  const value = params.value as number | null | undefined;
  if (value === null || value === undefined || isNaN(value)) {
    return "text-foreground-muted";
  }
  if (value > 0) return "text-positive";
  if (value < 0) return "text-negative";
  return "text-foreground";
}

/**
 * Bloomberg Terminal-style dark theme for AG Grid
 */
const bloombergTheme = themeQuartz.withParams({
  accentColor: "#3b82f6",
  backgroundColor: "#0a0a0a",
  borderColor: "#27272a",
  borderRadius: 0,
  browserColorScheme: "dark",
  cellHorizontalPaddingScale: 0.8,
  chromeBackgroundColor: "#1a1a1a",
  columnBorder: true,
  fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontSize: 13,
  foregroundColor: "#fafafa",
  headerBackgroundColor: "#1a1a1a",
  headerFontSize: 12,
  headerFontWeight: 600,
  headerTextColor: "#a1a1aa",
  headerVerticalPaddingScale: 0.9,
  oddRowBackgroundColor: "#0f0f0f",
  rowBorder: true,
  rowVerticalPaddingScale: 0.8,
  selectedRowBackgroundColor: "#2a2a2a",
  spacing: 6,
  wrapperBorder: true,
  wrapperBorderRadius: 8,
});

/**
 * DataGrid Component
 * AG Grid implementation with Bloomberg Terminal styling for stock screening
 */
export function DataGrid({
  stocks,
  visibleColumns = DEFAULT_VISIBLE_COLUMNS,
  searchText = "",
  onSortChange,
  isLoading = false,
}: DataGridProps): React.ReactElement {
  const router = useRouter();
  const gridRef = useRef<AgGridReact<StockSummary>>(null);
  const gridApiRef = useRef<GridApi<StockSummary> | null>(null);

  /**
   * Currency formatter for price columns
   */
  const currencyFormatter = useCallback(
    (params: ValueFormatterParams): string => {
      return formatCurrency(params.value, 2);
    },
    []
  );

  /**
   * Market cap formatter with abbreviations
   */
  const marketCapFormatter = useCallback(
    (params: ValueFormatterParams): string => {
      return formatMarketCap(params.value);
    },
    []
  );

  /**
   * Percentage formatter
   */
  const percentFormatter = useCallback(
    (params: ValueFormatterParams): string => {
      return formatPercent(params.value, 2);
    },
    []
  );

  /**
   * Ratio formatter with 'x' suffix
   */
  const ratioFormatter = useCallback(
    (params: ValueFormatterParams): string => {
      return formatRatio(params.value, 2);
    },
    []
  );

  /**
   * Volume formatter with commas
   */
  const volumeFormatter = useCallback(
    (params: ValueFormatterParams): string => {
      const value = params.value as number | null | undefined;
      if (value === null || value === undefined || isNaN(value)) {
        return "N/A";
      }
      return new Intl.NumberFormat("en-US").format(value);
    },
    []
  );

  /**
   * Large number formatter (cash, debt)
   */
  const largeNumberFormatter = useCallback(
    (params: ValueFormatterParams): string => {
      const value = params.value as number | null | undefined;
      if (value === null || value === undefined || isNaN(value)) {
        return "N/A";
      }
      const absValue = Math.abs(value);
      const sign = value < 0 ? "-" : "";
      if (absValue >= 1e12) return `${sign}$${(absValue / 1e12).toFixed(1)}T`;
      if (absValue >= 1e9) return `${sign}$${(absValue / 1e9).toFixed(1)}B`;
      if (absValue >= 1e6) return `${sign}$${(absValue / 1e6).toFixed(1)}M`;
      if (absValue >= 1e3) return `${sign}$${(absValue / 1e3).toFixed(1)}K`;
      return formatCurrency(value, 0);
    },
    []
  );

  /**
   * Column definitions for AG Grid
   */
  const columnDefs: ColDef<StockSummary>[] = useMemo(
    () => [
      // === Identifiers ===
      {
        field: "ticker",
        headerName: "Ticker",
        width: 90,
        pinned: "left",
        sortable: true,
        filter: true,
        cellClass: "font-mono font-semibold text-accent",
      },
      {
        field: "company_name",
        headerName: "Company",
        minWidth: 180,
        flex: 1,
        sortable: true,
        filter: true,
        cellClass: "truncate",
      },
      {
        field: "sector",
        headerName: "Sector",
        width: 140,
        sortable: true,
        filter: true,
        cellClass: "text-foreground-muted",
      },
      {
        field: "industry",
        headerName: "Industry",
        width: 160,
        sortable: true,
        filter: true,
        cellClass: "text-foreground-muted truncate",
      },

      // === Market Data ===
      {
        field: "current_price",
        headerName: "Price",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: currencyFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "market_cap",
        headerName: "Market Cap",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: marketCapFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "volume",
        headerName: "Volume",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: volumeFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },

      // === Valuation Ratios ===
      {
        field: "pe_trailing",
        headerName: "P/E (TTM)",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: ratioFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "pe_forward",
        headerName: "P/E (Fwd)",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: ratioFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "peg_ratio",
        headerName: "PEG",
        width: 80,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: ratioFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "price_to_book",
        headerName: "P/B",
        width: 80,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: ratioFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },

      // === Dividends ===
      {
        field: "dividend_yield",
        headerName: "Div Yield",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) => {
          const value = params.value as number | null;
          return cn(
            "font-mono tabular-nums text-right",
            value && value > 0 ? "text-positive" : "text-foreground-muted"
          );
        },
      },

      // === Profitability ===
      {
        field: "profit_margin",
        headerName: "Profit Margin",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getPercentCellClass(params)),
      },
      {
        field: "operating_margin",
        headerName: "Op Margin",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getPercentCellClass(params)),
      },
      {
        field: "return_on_equity",
        headerName: "ROE",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getPercentCellClass(params)),
      },
      {
        field: "return_on_assets",
        headerName: "ROA",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getPercentCellClass(params)),
      },

      // === Risk Metrics ===
      {
        field: "beta",
        headerName: "Beta",
        width: 80,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: (params: ValueFormatterParams): string => {
          const value = params.value as number | null;
          if (value === null || value === undefined) return "N/A";
          return value.toFixed(2);
        },
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "annual_volatility",
        headerName: "Volatility",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "sharpe_ratio",
        headerName: "Sharpe",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: (params: ValueFormatterParams): string => {
          const value = params.value as number | null;
          if (value === null || value === undefined) return "N/A";
          return value.toFixed(2);
        },
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getValueCellClass(params)),
      },

      // === Technicals - 52 Week Range ===
      {
        field: "52_week_high",
        headerName: "52W High",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: currencyFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "52_week_low",
        headerName: "52W Low",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: currencyFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "ma_50",
        headerName: "MA 50",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: currencyFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "ma_200",
        headerName: "MA 200",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: currencyFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },

      // === Performance ===
      {
        field: "cagr_5y",
        headerName: "5Y CAGR",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getPercentCellClass(params)),
      },
      {
        field: "total_return_5y",
        headerName: "5Y Return",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getPercentCellClass(params)),
      },
      {
        field: "revenue_growth",
        headerName: "Rev Growth",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getPercentCellClass(params)),
      },

      // === Balance Sheet ===
      {
        field: "debt_to_equity",
        headerName: "D/E",
        width: 80,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: ratioFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "total_cash",
        headerName: "Cash",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "total_debt",
        headerName: "Debt",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "calc_net_debt",
        headerName: "Net Debt",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: (params: CellClassParams) => {
          const value = params.value as number | null;
          return cn(
            "font-mono tabular-nums text-right",
            value && value < 0 ? "text-positive" : "text-foreground-muted"
          );
        },
      },

      // === Additional Identifiers ===
      {
        field: "cik",
        headerName: "CIK",
        width: 100,
        sortable: true,
        filter: true,
        cellClass: "font-mono text-foreground-muted",
      },
      {
        field: "country",
        headerName: "Country",
        width: 120,
        sortable: true,
        filter: true,
        cellClass: "text-foreground-muted",
      },
      {
        field: "website",
        headerName: "Website",
        width: 180,
        sortable: true,
        filter: true,
        cellClass: "text-accent truncate",
        valueFormatter: (params: ValueFormatterParams): string => {
          const value = params.value as string | null;
          if (!value) return "N/A";
          return value.replace(/^https?:\/\//, "");
        },
      },

      // === Earnings ===
      {
        field: "eps_trailing",
        headerName: "EPS (TTM)",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: currencyFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "eps_forward",
        headerName: "EPS (Fwd)",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: currencyFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },

      // === Income Statement ===
      {
        field: "total_revenue",
        headerName: "Revenue",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "net_income",
        headerName: "Net Income",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getValueCellClass(params)),
      },
      {
        field: "ebitda",
        headerName: "EBITDA",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "calc_ebitda",
        headerName: "EBITDA (Calc)",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },

      // === Cash Flow ===
      {
        field: "free_cash_flow",
        headerName: "FCF",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getValueCellClass(params)),
      },
      {
        field: "calc_fcf",
        headerName: "FCF (Calc)",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getValueCellClass(params)),
      },

      // === Calculated Metrics ===
      {
        field: "calc_ev",
        headerName: "EV",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "calc_ev_to_ebitda",
        headerName: "EV/EBITDA",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: ratioFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "calc_interest_coverage",
        headerName: "Int. Coverage",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: ratioFormatter,
        cellClass: "font-mono tabular-nums text-right",
      },
      {
        field: "calc_roic",
        headerName: "ROIC",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getPercentCellClass(params)),
      },

      // === Additional Risk Metrics ===
      {
        field: "max_drawdown",
        headerName: "Max Drawdown",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: "font-mono tabular-nums text-right text-negative",
      },
      {
        field: "risk_free_rate_10y",
        headerName: "Risk-Free Rate",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },

      // === Shares & Ownership ===
      {
        field: "shares_outstanding",
        headerName: "Shares Out",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: (params: ValueFormatterParams): string => {
          const value = params.value as number | null;
          if (value === null || value === undefined) return "N/A";
          if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
          if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
          return new Intl.NumberFormat("en-US").format(value);
        },
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "float_shares",
        headerName: "Float",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: (params: ValueFormatterParams): string => {
          const value = params.value as number | null;
          if (value === null || value === undefined) return "N/A";
          if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
          if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
          return new Intl.NumberFormat("en-US").format(value);
        },
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "insider_percent",
        headerName: "Insider %",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "institutional_percent",
        headerName: "Inst. %",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: percentFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "short_ratio",
        headerName: "Short Ratio",
        width: 100,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: ratioFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },

      // === Company Info ===
      {
        field: "employees",
        headerName: "Employees",
        width: 110,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: (params: ValueFormatterParams): string => {
          const value = params.value as number | null;
          if (value === null || value === undefined) return "N/A";
          return new Intl.NumberFormat("en-US").format(value);
        },
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },

      // === SEC Filing Data ===
      {
        field: "sec_fiscal_year",
        headerName: "SEC FY",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "sec_revenue",
        headerName: "SEC Revenue",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "sec_net_income",
        headerName: "SEC Net Inc",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: (params: CellClassParams) =>
          cn("font-mono tabular-nums text-right", getValueCellClass(params)),
      },
      {
        field: "sec_operating_cash_flow",
        headerName: "SEC Op CF",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "sec_stockholders_equity",
        headerName: "SEC Equity",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "sec_total_assets",
        headerName: "SEC Assets",
        width: 120,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },
      {
        field: "sec_total_liabilities",
        headerName: "SEC Liabilities",
        width: 130,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        valueFormatter: largeNumberFormatter,
        cellClass: "font-mono tabular-nums text-right text-foreground-muted",
      },

      // === Metadata ===
      {
        field: "collected_at",
        headerName: "Collected At",
        width: 160,
        sortable: true,
        filter: true,
        valueFormatter: (params: ValueFormatterParams): string => {
          const value = params.value as string | null;
          if (!value) return "N/A";
          return new Date(value).toLocaleString();
        },
        cellClass: "text-foreground-muted text-xs",
      },
      {
        field: "data_sources",
        headerName: "Data Sources",
        width: 140,
        sortable: true,
        filter: true,
        cellClass: "text-foreground-muted text-xs truncate",
      },
      {
        field: "treasury_yield_source",
        headerName: "Yield Source",
        width: 110,
        sortable: true,
        filter: true,
        cellClass: "text-foreground-muted text-xs",
      },
      {
        field: "error_count",
        headerName: "Errors",
        width: 80,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        cellClass: (params: CellClassParams) => {
          const value = params.value as number | null;
          return cn(
            "font-mono tabular-nums text-right",
            value && value > 0 ? "text-negative" : "text-foreground-muted"
          );
        },
      },
      {
        field: "warning_count",
        headerName: "Warnings",
        width: 90,
        sortable: true,
        filter: "agNumberColumnFilter",
        type: "numericColumn",
        cellClass: (params: CellClassParams) => {
          const value = params.value as number | null;
          return cn(
            "font-mono tabular-nums text-right",
            value && value > 0 ? "text-yellow-500" : "text-foreground-muted"
          );
        },
      },
    ],
    [
      currencyFormatter,
      marketCapFormatter,
      percentFormatter,
      ratioFormatter,
      volumeFormatter,
      largeNumberFormatter,
    ]
  );

  /**
   * Filter column definitions based on visibleColumns prop
   */
  const filteredColumnDefs = useMemo(() => {
    return columnDefs.map((col) => ({
      ...col,
      hide: !visibleColumns.includes(col.field as string),
    }));
  }, [columnDefs, visibleColumns]);

  /**
   * Filter row data based on search text
   */
  const filteredRowData = useMemo(() => {
    if (!searchText.trim()) return stocks;

    const lowerSearch = searchText.toLowerCase().trim();
    return stocks.filter(
      (stock) =>
        stock.ticker.toLowerCase().includes(lowerSearch) ||
        stock.company_name.toLowerCase().includes(lowerSearch)
    );
  }, [stocks, searchText]);

  /**
   * Handle grid ready event
   */
  const onGridReady = useCallback((event: GridReadyEvent<StockSummary>) => {
    gridApiRef.current = event.api;
  }, []);

  /**
   * Handle row click - navigate to stock detail page
   */
  const onRowClicked = useCallback(
    (event: RowClickedEvent<StockSummary>) => {
      if (event.data) {
        router.push(`/stocks/${event.data.ticker}`);
      }
    },
    [router]
  );

  /**
   * Handle sort change
   */
  const onSortChanged = useCallback(
    (event: SortChangedEvent<StockSummary>) => {
      if (!onSortChange) return;

      const sortModel = event.api.getColumnState().filter((col) => col.sort);
      if (sortModel.length > 0) {
        const { colId, sort } = sortModel[0];
        if (colId && sort) {
          onSortChange(colId, sort as "asc" | "desc");
        }
      }
    },
    [onSortChange]
  );

  /**
   * Default column properties
   */
  const defaultColDef: ColDef = useMemo(
    () => ({
      sortable: true,
      resizable: true,
      suppressMovable: false,
    }),
    []
  );

  return (
    <div className="w-full h-[calc(100vh-280px)] min-h-[400px]">
      <AgGridReact<StockSummary>
        ref={gridRef}
        theme={bloombergTheme}
        rowData={filteredRowData}
        columnDefs={filteredColumnDefs}
        defaultColDef={defaultColDef}
        onGridReady={onGridReady}
        onRowClicked={onRowClicked}
        onSortChanged={onSortChanged}
        rowSelection="single"
        animateRows={true}
        suppressCellFocus={true}
        enableCellTextSelection={true}
        loading={isLoading}
        overlayLoadingTemplate='<div class="text-foreground-muted">Loading stocks...</div>'
        overlayNoRowsTemplate='<div class="text-foreground-muted">No stocks match your criteria</div>'
        getRowId={(params) => params.data.ticker}
        rowClass="cursor-pointer hover:bg-background-tertiary transition-colors"
      />
    </div>
  );
}

export default DataGrid;
