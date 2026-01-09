"use client";

import React, { useState, useCallback, useMemo, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useStocks } from "@/hooks/useStocks";
import {
  DataGrid,
  FilterBar,
  SearchInput,
  ColumnSelector,
  DEFAULT_VISIBLE_COLUMNS,
  INITIAL_FILTER_STATE,
} from "@/components/screener";
import type { FilterState } from "@/components/screener";
import type { StockSummary } from "@/types/stock";
import { cn } from "@/lib/utils";

/**
 * Filter icon SVG component
 */
function FilterIcon({ className }: { className?: string }): React.ReactElement {
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
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
    </svg>
  );
}

/**
 * Loading skeleton for the screener
 */
function ScreenerSkeleton(): React.ReactElement {
  return (
    <div className="space-y-4">
      {/* Header skeleton */}
      <div className="flex flex-col gap-2">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="h-4 w-96 skeleton rounded" />
      </div>

      {/* Toolbar skeleton */}
      <div className="flex items-center gap-4">
        <div className="h-10 w-64 skeleton rounded-lg" />
        <div className="h-10 w-24 skeleton rounded-lg" />
        <div className="h-10 w-24 skeleton rounded-lg" />
      </div>

      {/* Table skeleton */}
      <div className="rounded-lg border border-border overflow-hidden">
        <div className="h-12 bg-background-secondary" />
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className="flex h-12 items-center border-t border-border px-4 gap-4"
          >
            <div className="h-4 w-16 skeleton rounded" />
            <div className="h-4 w-40 skeleton rounded" />
            <div className="h-4 w-24 skeleton rounded" />
            <div className="ml-auto h-4 w-20 skeleton rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Parse URL search params into FilterState
 */
function parseFiltersFromParams(searchParams: URLSearchParams): FilterState {
  return {
    minMarketCap: searchParams.get("minMarketCap") || "",
    maxMarketCap: searchParams.get("maxMarketCap") || "",
    minPE: searchParams.get("minPE") || "",
    maxPE: searchParams.get("maxPE") || "",
    minDividendYield: searchParams.get("minDividendYield") || "",
    maxDividendYield: searchParams.get("maxDividendYield") || "",
    sector: searchParams.get("sector") || "",
    industry: searchParams.get("industry") || "",
  };
}

/**
 * Convert FilterState to URL search params string
 */
function filtersToParamsString(filters: FilterState, search: string): string {
  const params = new URLSearchParams();

  if (search) params.set("search", search);
  if (filters.sector) params.set("sector", filters.sector);
  if (filters.industry) params.set("industry", filters.industry);
  if (filters.minMarketCap) params.set("minMarketCap", filters.minMarketCap);
  if (filters.maxMarketCap) params.set("maxMarketCap", filters.maxMarketCap);
  if (filters.minPE) params.set("minPE", filters.minPE);
  if (filters.maxPE) params.set("maxPE", filters.maxPE);
  if (filters.minDividendYield) params.set("minDividendYield", filters.minDividendYield);
  if (filters.maxDividendYield) params.set("maxDividendYield", filters.maxDividendYield);

  const paramsString = params.toString();
  return paramsString ? `?${paramsString}` : "";
}

/**
 * Apply filters to stock data client-side
 */
function applyFilters(
  stocks: StockSummary[],
  filters: FilterState,
  searchText: string
): StockSummary[] {
  return stocks.filter((stock) => {
    // Search filter
    if (searchText) {
      const lowerSearch = searchText.toLowerCase();
      if (
        !stock.ticker.toLowerCase().includes(lowerSearch) &&
        !stock.company_name.toLowerCase().includes(lowerSearch)
      ) {
        return false;
      }
    }

    // Sector filter
    if (filters.sector && stock.sector !== filters.sector) {
      return false;
    }

    // Industry filter
    if (filters.industry && stock.industry !== filters.industry) {
      return false;
    }

    // Market cap filters
    if (filters.minMarketCap) {
      const min = parseFloat(filters.minMarketCap);
      if (!isNaN(min) && (stock.market_cap === null || stock.market_cap < min)) {
        return false;
      }
    }
    if (filters.maxMarketCap) {
      const max = parseFloat(filters.maxMarketCap);
      if (!isNaN(max) && (stock.market_cap === null || stock.market_cap > max)) {
        return false;
      }
    }

    // P/E filters
    if (filters.minPE) {
      const min = parseFloat(filters.minPE);
      if (!isNaN(min) && (stock.pe_trailing === null || stock.pe_trailing < min)) {
        return false;
      }
    }
    if (filters.maxPE) {
      const max = parseFloat(filters.maxPE);
      if (!isNaN(max) && (stock.pe_trailing === null || stock.pe_trailing > max)) {
        return false;
      }
    }

    // Dividend yield filters (convert from percentage input)
    if (filters.minDividendYield) {
      const min = parseFloat(filters.minDividendYield) / 100;
      if (
        !isNaN(min) &&
        (stock.dividend_yield === null || stock.dividend_yield < min)
      ) {
        return false;
      }
    }
    if (filters.maxDividendYield) {
      const max = parseFloat(filters.maxDividendYield) / 100;
      if (
        !isNaN(max) &&
        (stock.dividend_yield === null || stock.dividend_yield > max)
      ) {
        return false;
      }
    }

    return true;
  });
}

/**
 * Main Screener Content Component (uses useSearchParams)
 */
function ScreenerContent(): React.ReactElement {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Fetch all stocks
  const { data: stocks, isLoading, error, isError } = useStocks();

  // Filter state - initialized from URL params
  const [filters, setFilters] = useState<FilterState>(() =>
    parseFiltersFromParams(searchParams)
  );
  const [appliedFilters, setAppliedFilters] = useState<FilterState>(() =>
    parseFiltersFromParams(searchParams)
  );

  // Search state - initialized from URL params
  const [searchText, setSearchText] = useState(
    () => searchParams.get("search") || ""
  );

  // Column visibility state
  const [visibleColumns, setVisibleColumns] = useState<string[]>(
    DEFAULT_VISIBLE_COLUMNS
  );

  // Filter panel visibility
  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);

  /**
   * Sync filters from URL params on initial load
   */
  useEffect(() => {
    const urlFilters = parseFiltersFromParams(searchParams);
    const urlSearch = searchParams.get("search") || "";

    setFilters(urlFilters);
    setAppliedFilters(urlFilters);
    setSearchText(urlSearch);

    // Open filter panel if filters are present in URL
    const hasUrlFilters = Object.values(urlFilters).some((v) => v !== "");
    if (hasUrlFilters) {
      setIsFilterPanelOpen(true);
    }
  }, [searchParams]);

  /**
   * Update URL when filters are applied
   */
  const updateURL = useCallback(
    (newFilters: FilterState, newSearch: string) => {
      const paramsString = filtersToParamsString(newFilters, newSearch);
      router.push(`/${paramsString}`, { scroll: false });
    },
    [router]
  );

  /**
   * Handle filter changes (local state only)
   */
  const handleFiltersChange = useCallback((newFilters: FilterState) => {
    setFilters(newFilters);
  }, []);

  /**
   * Handle apply filters
   */
  const handleApplyFilters = useCallback(() => {
    setAppliedFilters(filters);
    updateURL(filters, searchText);
  }, [filters, searchText, updateURL]);

  /**
   * Handle clear filters
   */
  const handleClearFilters = useCallback(() => {
    setFilters(INITIAL_FILTER_STATE);
    setAppliedFilters(INITIAL_FILTER_STATE);
    updateURL(INITIAL_FILTER_STATE, searchText);
  }, [searchText, updateURL]);

  /**
   * Handle search change
   */
  const handleSearchChange = useCallback(
    (value: string) => {
      setSearchText(value);
      updateURL(appliedFilters, value);
    },
    [appliedFilters, updateURL]
  );

  /**
   * Handle column visibility change
   */
  const handleColumnsChange = useCallback((columns: string[]) => {
    setVisibleColumns(columns);
  }, []);

  /**
   * Check if any filters are active
   */
  const hasActiveFilters = useMemo(() => {
    return Object.values(appliedFilters).some((v) => v !== "");
  }, [appliedFilters]);

  /**
   * Apply filters to stock data
   */
  const filteredStocks = useMemo(() => {
    if (!stocks) return [];
    return applyFilters(stocks, appliedFilters, searchText);
  }, [stocks, appliedFilters, searchText]);

  /**
   * Count of filtered stocks
   */
  const filteredCount = filteredStocks.length;
  const totalCount = stocks?.length || 0;

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Stock Screener
          </h1>
          <p className="text-foreground-muted text-sm sm:text-base">
            Analyze top stocks with CFA-grade valuations and AI-powered insights
          </p>
        </div>

        {/* Stats Badge */}
        {!isLoading && !isError && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-foreground-muted">
              Showing{" "}
              <span className="font-mono tabular-nums text-foreground">
                {filteredCount}
              </span>{" "}
              of{" "}
              <span className="font-mono tabular-nums text-foreground">
                {totalCount}
              </span>{" "}
              stocks
            </span>
          </div>
        )}
      </div>

      {/* Error State */}
      {isError && (
        <div className="rounded-lg border border-negative/50 bg-negative/10 p-4">
          <h3 className="font-semibold text-negative">Error Loading Stocks</h3>
          <p className="mt-1 text-sm text-foreground-muted">
            {error?.message || "Failed to fetch stock data. Please try again."}
          </p>
          <p className="mt-2 text-xs text-foreground-muted">
            Make sure the backend server is running at http://localhost:8000
          </p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && <ScreenerSkeleton />}

      {/* Main Screener UI */}
      {!isLoading && !isError && stocks && (
        <>
          {/* Toolbar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {/* Search Input */}
            <SearchInput
              value={searchText}
              onChange={handleSearchChange}
              className="w-full sm:w-80"
            />

            {/* Filter Toggle Button */}
            <button
              onClick={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
              className={cn(
                "flex items-center gap-2 h-10 px-4 text-sm font-medium rounded-lg",
                "border transition-colors",
                isFilterPanelOpen || hasActiveFilters
                  ? "bg-accent/10 border-accent text-accent"
                  : "bg-background-secondary border-border hover:bg-background-tertiary hover:border-border-hover"
              )}
            >
              <FilterIcon />
              <span>Filters</span>
              {hasActiveFilters && (
                <span className="flex items-center justify-center w-5 h-5 text-xs bg-accent text-white rounded-full">
                  {Object.values(appliedFilters).filter((v) => v !== "").length}
                </span>
              )}
            </button>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Column Selector */}
            <ColumnSelector
              visibleColumns={visibleColumns}
              onColumnsChange={handleColumnsChange}
            />
          </div>

          {/* Filter Panel (Collapsible) */}
          {isFilterPanelOpen && (
            <FilterBar
              stocks={stocks}
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onApply={handleApplyFilters}
              onClear={handleClearFilters}
              hasActiveFilters={hasActiveFilters}
            />
          )}

          {/* Data Grid */}
          <DataGrid
            stocks={filteredStocks}
            visibleColumns={visibleColumns}
            searchText=""
            isLoading={isLoading}
          />

          {/* Footer Stats */}
          {stocks.length > 0 && (
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs text-foreground-muted pt-2 border-t border-border">
              <span>
                Data as of{" "}
                {stocks[0]?.collected_at
                  ? new Date(stocks[0].collected_at).toLocaleString()
                  : "N/A"}
              </span>
              <span>
                Click on any row to view detailed stock analysis
              </span>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!isLoading && !isError && filteredStocks.length === 0 && stocks && stocks.length > 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-background-secondary p-12">
          <p className="text-lg font-medium">No stocks match your criteria</p>
          <p className="mt-2 text-sm text-foreground-muted">
            Try adjusting your filters or search terms
          </p>
          <button
            onClick={handleClearFilters}
            className="mt-4 px-4 py-2 text-sm font-medium bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors"
          >
            Clear All Filters
          </button>
        </div>
      )}
    </div>
  );
}

/**
 * Home Page - Stock Screener
 * Main page component with Suspense boundary for useSearchParams
 */
export default function HomePage(): React.ReactElement {
  return (
    <Suspense fallback={<ScreenerSkeleton />}>
      <ScreenerContent />
    </Suspense>
  );
}
