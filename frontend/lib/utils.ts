import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with clsx
 * Handles conditional classes and deduplication
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as currency (USD)
 * @param value - Number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted currency string
 */
export function formatCurrency(
  value: number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format a decimal as percentage
 * @param value - Decimal value (e.g., 0.15 for 15%)
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted percentage string
 */
export function formatPercent(
  value: number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  return new Intl.NumberFormat("en-US", {
    style: "percent",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format large numbers with abbreviations (K, M, B, T)
 * @param value - Number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted string with abbreviation
 */
export function formatLargeNumber(
  value: number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  const absValue = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (absValue >= 1e12) {
    return `${sign}$${(absValue / 1e12).toFixed(decimals)}T`;
  }
  if (absValue >= 1e9) {
    return `${sign}$${(absValue / 1e9).toFixed(decimals)}B`;
  }
  if (absValue >= 1e6) {
    return `${sign}$${(absValue / 1e6).toFixed(decimals)}M`;
  }
  if (absValue >= 1e3) {
    return `${sign}$${(absValue / 1e3).toFixed(decimals)}K`;
  }

  return formatCurrency(value, decimals);
}

/**
 * Format a number with commas for thousands
 * @param value - Number to format
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted number string
 */
export function formatNumber(
  value: number | null | undefined,
  decimals: number = 0
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format a ratio/multiple (e.g., P/E ratio)
 * @param value - Ratio value
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted ratio string with 'x' suffix
 */
export function formatRatio(
  value: number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  return `${value.toFixed(decimals)}x`;
}

/**
 * Get color class for positive/negative values
 * @param value - Number value
 * @param options - Configuration options
 * @returns Tailwind color class
 */
export function getValueColorClass(
  value: number | null | undefined,
  options: {
    positiveClass?: string;
    negativeClass?: string;
    neutralClass?: string;
    invertColors?: boolean;
  } = {}
): string {
  const {
    positiveClass = "text-positive",
    negativeClass = "text-negative",
    neutralClass = "text-foreground-muted",
    invertColors = false,
  } = options;

  if (value === null || value === undefined || isNaN(value)) {
    return neutralClass;
  }

  if (value === 0) {
    return neutralClass;
  }

  const isPositive = invertColors ? value < 0 : value > 0;
  return isPositive ? positiveClass : negativeClass;
}

/**
 * Format a percentage change with + or - prefix
 * @param value - Decimal value representing change
 * @param decimals - Number of decimal places
 * @returns Formatted change string
 */
export function formatChange(
  value: number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${formatPercent(value, decimals)}`;
}

/**
 * Parse a string value to number, handling null/undefined
 * @param value - String or number value
 * @returns Parsed number or null
 */
export function parseNumeric(
  value: string | number | null | undefined
): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const parsed = typeof value === "string" ? parseFloat(value) : value;
  return isNaN(parsed) ? null : parsed;
}

/**
 * Truncate text with ellipsis
 * @param text - Text to truncate
 * @param maxLength - Maximum length before truncation
 * @returns Truncated text
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 3)}...`;
}

/**
 * Format market cap for display (short form)
 * @param value - Market cap in dollars
 * @returns Formatted market cap string
 */
export function formatMarketCap(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  if (value >= 1e12) {
    return `$${(value / 1e12).toFixed(2)}T`;
  }
  if (value >= 1e9) {
    return `$${(value / 1e9).toFixed(2)}B`;
  }
  if (value >= 1e6) {
    return `$${(value / 1e6).toFixed(2)}M`;
  }

  return formatCurrency(value, 0);
}
