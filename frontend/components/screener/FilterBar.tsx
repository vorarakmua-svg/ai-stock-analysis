"use client";

import React, { useState, useCallback, useMemo, useEffect } from "react";
import { cn } from "@/lib/utils";
import type { StockSummary } from "@/types/stock";

/**
 * Filter state interface
 */
export interface FilterState {
  minMarketCap: string;
  maxMarketCap: string;
  minPE: string;
  maxPE: string;
  minDividendYield: string;
  maxDividendYield: string;
  sector: string;
  industry: string;
}

/**
 * Initial filter state
 */
export const INITIAL_FILTER_STATE: FilterState = {
  minMarketCap: "",
  maxMarketCap: "",
  minPE: "",
  maxPE: "",
  minDividendYield: "",
  maxDividendYield: "",
  sector: "",
  industry: "",
};

/**
 * Props for the FilterBar component
 */
interface FilterBarProps {
  /** Stock data to extract unique sectors/industries */
  stocks: StockSummary[];
  /** Current filter state */
  filters: FilterState;
  /** Callback when filters change */
  onFiltersChange: (filters: FilterState) => void;
  /** Callback to apply filters */
  onApply: () => void;
  /** Callback to clear all filters */
  onClear: () => void;
  /** Whether filters have been applied */
  hasActiveFilters?: boolean;
}

/**
 * Market cap presets in billions
 */
const MARKET_CAP_PRESETS = [
  { label: "Nano (<$50M)", min: "", max: "50000000" },
  { label: "Micro ($50M-$300M)", min: "50000000", max: "300000000" },
  { label: "Small ($300M-$2B)", min: "300000000", max: "2000000000" },
  { label: "Mid ($2B-$10B)", min: "2000000000", max: "10000000000" },
  { label: "Large ($10B-$200B)", min: "10000000000", max: "200000000000" },
  { label: "Mega (>$200B)", min: "200000000000", max: "" },
];

/**
 * Sanitize numeric input - only allow digits, decimal point, and minus sign
 */
function sanitizeNumericInput(value: string): string {
  // Remove any characters that aren't digits, decimal points, or minus signs
  const sanitized = value.replace(/[^\d.\-]/g, "");
  // Ensure only one decimal point
  const parts = sanitized.split(".");
  if (parts.length > 2) {
    return parts[0] + "." + parts.slice(1).join("");
  }
  // Ensure minus sign is only at the start
  if (sanitized.includes("-") && sanitized.indexOf("-") !== 0) {
    return sanitized.replace(/-/g, "");
  }
  return sanitized;
}

/**
 * Input component for numeric range filters
 */
function RangeInput({
  label,
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  placeholder = { min: "Min", max: "Max" },
  prefix = "",
  suffix = "",
}: {
  label: string;
  minValue: string;
  maxValue: string;
  onMinChange: (value: string) => void;
  onMaxChange: (value: string) => void;
  placeholder?: { min: string; max: string };
  prefix?: string;
  suffix?: string;
}): React.ReactElement {
  // Handle input change with validation
  const handleMinChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const sanitized = sanitizeNumericInput(e.target.value);
    onMinChange(sanitized);
  };

  const handleMaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const sanitized = sanitizeNumericInput(e.target.value);
    onMaxChange(sanitized);
  };
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-foreground-muted uppercase tracking-wide">
        {label}
      </label>
      <div className="flex items-center gap-1">
        <div className="relative flex-1">
          {prefix && (
            <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-foreground-muted">
              {prefix}
            </span>
          )}
          <input
            type="text"
            inputMode="decimal"
            pattern="[0-9]*\.?[0-9]*"
            value={minValue}
            onChange={handleMinChange}
            placeholder={placeholder.min}
            className={cn(
              "w-full h-8 px-2 text-sm bg-background-secondary border border-border rounded",
              "focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50",
              "placeholder:text-foreground-muted/50 font-mono tabular-nums",
              prefix && "pl-5"
            )}
          />
        </div>
        <span className="text-xs text-foreground-muted">-</span>
        <div className="relative flex-1">
          {prefix && (
            <span className="absolute left-2 top-1/2 -translate-y-1/2 text-xs text-foreground-muted">
              {prefix}
            </span>
          )}
          <input
            type="text"
            inputMode="decimal"
            pattern="[0-9]*\.?[0-9]*"
            value={maxValue}
            onChange={handleMaxChange}
            placeholder={placeholder.max}
            className={cn(
              "w-full h-8 px-2 text-sm bg-background-secondary border border-border rounded",
              "focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50",
              "placeholder:text-foreground-muted/50 font-mono tabular-nums",
              prefix && "pl-5"
            )}
          />
          {suffix && (
            <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-foreground-muted">
              {suffix}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Select dropdown component
 */
function SelectInput({
  label,
  value,
  onChange,
  options,
  placeholder = "All",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  placeholder?: string;
}): React.ReactElement {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-foreground-muted uppercase tracking-wide">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "h-8 px-2 text-sm bg-background-secondary border border-border rounded",
          "focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50",
          "cursor-pointer appearance-none",
          "bg-[url('data:image/svg+xml;charset=UTF-8,%3csvg%20xmlns%3d%22http%3a%2f%2fwww.w3.org%2f2000%2fsvg%22%20viewBox%3d%220%200%2024%2024%22%20fill%3d%22none%22%20stroke%3d%22%23a1a1aa%22%20stroke-width%3d%222%22%20stroke-linecap%3d%22round%22%20stroke-linejoin%3d%22round%22%3e%3cpolyline%20points%3d%226%209%2012%2015%2018%209%22%3e%3c%2fpolyline%3e%3c%2fsvg%3e')] bg-[length:16px] bg-[right_4px_center] bg-no-repeat pr-6",
          !value && "text-foreground-muted"
        )}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * FilterBar Component
 * Horizontal filter bar for the stock screener
 */
export function FilterBar({
  stocks,
  filters,
  onFiltersChange,
  onApply,
  onClear,
  hasActiveFilters = false,
}: FilterBarProps): React.ReactElement {
  const [localFilters, setLocalFilters] = useState<FilterState>(filters);

  // Sync local state with prop changes
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  /**
   * Extract unique sectors from stocks
   */
  const sectors = useMemo(() => {
    const uniqueSectors = new Set<string>();
    stocks.forEach((stock) => {
      if (stock.sector) uniqueSectors.add(stock.sector);
    });
    return Array.from(uniqueSectors).sort();
  }, [stocks]);

  /**
   * Extract unique industries from stocks, filtered by selected sector
   */
  const industries = useMemo(() => {
    const uniqueIndustries = new Set<string>();
    stocks.forEach((stock) => {
      if (stock.industry) {
        // If sector is selected, only show industries in that sector
        if (!localFilters.sector || stock.sector === localFilters.sector) {
          uniqueIndustries.add(stock.industry);
        }
      }
    });
    return Array.from(uniqueIndustries).sort();
  }, [stocks, localFilters.sector]);

  /**
   * Update a single filter field
   */
  const updateFilter = useCallback(
    <K extends keyof FilterState>(field: K, value: FilterState[K]) => {
      setLocalFilters((prev) => {
        const updated = { ...prev, [field]: value };
        // Reset industry when sector changes
        if (field === "sector") {
          updated.industry = "";
        }
        return updated;
      });
    },
    []
  );

  /**
   * Handle apply button click
   */
  const handleApply = useCallback(() => {
    onFiltersChange(localFilters);
    onApply();
  }, [localFilters, onFiltersChange, onApply]);

  /**
   * Handle clear button click
   */
  const handleClear = useCallback(() => {
    setLocalFilters(INITIAL_FILTER_STATE);
    onFiltersChange(INITIAL_FILTER_STATE);
    onClear();
  }, [onFiltersChange, onClear]);

  /**
   * Handle market cap preset selection
   */
  const handleMarketCapPreset = useCallback(
    (min: string, max: string) => {
      setLocalFilters((prev) => ({
        ...prev,
        minMarketCap: min,
        maxMarketCap: max,
      }));
    },
    []
  );

  /**
   * Check if any local filter is set
   */
  const hasLocalFilters = useMemo(() => {
    return Object.values(localFilters).some((v) => v !== "");
  }, [localFilters]);

  return (
    <div className="bg-background-secondary border border-border rounded-lg p-4">
      {/* Filter Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        {/* Sector Filter */}
        <SelectInput
          label="Sector"
          value={localFilters.sector}
          onChange={(v) => updateFilter("sector", v)}
          options={sectors}
          placeholder="All Sectors"
        />

        {/* Industry Filter */}
        <SelectInput
          label="Industry"
          value={localFilters.industry}
          onChange={(v) => updateFilter("industry", v)}
          options={industries}
          placeholder="All Industries"
        />

        {/* Market Cap Range */}
        <div className="sm:col-span-2">
          <RangeInput
            label="Market Cap"
            minValue={localFilters.minMarketCap}
            maxValue={localFilters.maxMarketCap}
            onMinChange={(v) => updateFilter("minMarketCap", v)}
            onMaxChange={(v) => updateFilter("maxMarketCap", v)}
            placeholder={{ min: "Min ($)", max: "Max ($)" }}
            prefix="$"
          />
        </div>

        {/* P/E Range */}
        <RangeInput
          label="P/E Ratio"
          minValue={localFilters.minPE}
          maxValue={localFilters.maxPE}
          onMinChange={(v) => updateFilter("minPE", v)}
          onMaxChange={(v) => updateFilter("maxPE", v)}
          placeholder={{ min: "0", max: "100" }}
        />

        {/* Dividend Yield Range */}
        <RangeInput
          label="Dividend Yield"
          minValue={localFilters.minDividendYield}
          maxValue={localFilters.maxDividendYield}
          onMinChange={(v) => updateFilter("minDividendYield", v)}
          onMaxChange={(v) => updateFilter("maxDividendYield", v)}
          placeholder={{ min: "0%", max: "10%" }}
          suffix="%"
        />
      </div>

      {/* Market Cap Presets */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-xs text-foreground-muted">Quick Market Cap:</span>
        {MARKET_CAP_PRESETS.map((preset) => (
          <button
            key={preset.label}
            onClick={() => handleMarketCapPreset(preset.min, preset.max)}
            className={cn(
              "px-2 py-1 text-xs rounded border transition-colors",
              localFilters.minMarketCap === preset.min &&
                localFilters.maxMarketCap === preset.max
                ? "bg-accent text-white border-accent"
                : "bg-background-tertiary border-border text-foreground-muted hover:border-accent hover:text-foreground"
            )}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <span className="text-xs text-accent">
              Filters active
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleClear}
            disabled={!hasLocalFilters && !hasActiveFilters}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded transition-colors",
              "border border-border bg-background-tertiary",
              "hover:bg-background hover:border-border-hover",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            Clear All
          </button>
          <button
            onClick={handleApply}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded transition-colors",
              "bg-accent text-white",
              "hover:bg-accent-hover",
              "focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-background"
            )}
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>
  );
}

export default FilterBar;
