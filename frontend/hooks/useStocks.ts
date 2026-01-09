"use client";

import { useQuery, useQueryClient, UseQueryResult } from "@tanstack/react-query";
import {
  getStocks,
  getStock,
  getStockPrice,
  getStockHistory,
  StockFilters,
} from "@/lib/api";
import type {
  StockSummary,
  StockDetail,
  RealTimePrice,
  HistoricalDataPoint,
  ChartPeriod,
} from "@/types/stock";

/**
 * Query Keys for React Query cache management
 */
export const stockQueryKeys = {
  all: ["stocks"] as const,
  lists: () => [...stockQueryKeys.all, "list"] as const,
  list: (filters?: StockFilters) =>
    [...stockQueryKeys.lists(), filters] as const,
  details: () => [...stockQueryKeys.all, "detail"] as const,
  detail: (ticker: string) => [...stockQueryKeys.details(), ticker] as const,
  prices: () => [...stockQueryKeys.all, "price"] as const,
  price: (ticker: string) => [...stockQueryKeys.prices(), ticker] as const,
  history: () => [...stockQueryKeys.all, "history"] as const,
  historyPeriod: (ticker: string, period: ChartPeriod) =>
    [...stockQueryKeys.history(), ticker, period] as const,
};

/**
 * Hook to fetch all stocks with optional filters
 * @param filters - Optional filtering and sorting parameters
 * @returns Query result with stocks array
 */
export function useStocks(
  filters?: StockFilters
): UseQueryResult<StockSummary[], Error> {
  return useQuery({
    queryKey: stockQueryKeys.list(filters),
    queryFn: () => getStocks(filters),
    // Stock list data is relatively stable
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to fetch a single stock by ticker
 * @param ticker - Stock ticker symbol (e.g., 'AAPL')
 * @returns Query result with stock detail
 */
export function useStock(
  ticker: string
): UseQueryResult<StockDetail, Error> {
  // Normalize ticker to uppercase for consistent caching
  const normalizedTicker = ticker.toUpperCase().trim();
  return useQuery({
    queryKey: stockQueryKeys.detail(normalizedTicker),
    queryFn: () => getStock(normalizedTicker),
    enabled: !!normalizedTicker, // Only fetch if ticker is provided
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to fetch real-time price for a stock
 * Automatically refetches every 30 seconds
 * @param ticker - Stock ticker symbol
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with real-time price data
 */
export function useRealTimePrice(
  ticker: string,
  enabled: boolean = true
): UseQueryResult<RealTimePrice, Error> {
  // Normalize ticker to uppercase for consistent caching
  const normalizedTicker = ticker.toUpperCase().trim();
  return useQuery({
    queryKey: stockQueryKeys.price(normalizedTicker),
    queryFn: () => getStockPrice(normalizedTicker),
    enabled: !!normalizedTicker && enabled,
    // Price data needs to be fresh
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    // Auto-refetch every 30 seconds
    refetchInterval: 30 * 1000,
    // Only refetch when window is focused
    refetchIntervalInBackground: false,
  });
}

/**
 * Hook to fetch historical OHLCV data for a stock
 * @param ticker - Stock ticker symbol
 * @param period - Time period for historical data
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with historical data array
 */
export function useStockHistory(
  ticker: string,
  period: ChartPeriod,
  enabled: boolean = true
): UseQueryResult<HistoricalDataPoint[], Error> {
  // Normalize ticker to uppercase for consistent caching
  const normalizedTicker = ticker.toUpperCase().trim();
  return useQuery({
    queryKey: stockQueryKeys.historyPeriod(normalizedTicker, period),
    queryFn: () => getStockHistory(normalizedTicker, period),
    enabled: !!normalizedTicker && enabled,
    // Historical data is relatively stable
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    // Keep previous data while fetching new period
    placeholderData: (previousData) => previousData,
  });
}

/**
 * Hook to prefetch stock data
 * Useful for hover prefetching on stock list
 */
export function usePrefetchStock(): (ticker: string) => void {
  const queryClient = useQueryClient();

  return (ticker: string) => {
    // Normalize ticker to uppercase for consistent caching
    const normalizedTicker = ticker.toUpperCase().trim();
    queryClient.prefetchQuery({
      queryKey: stockQueryKeys.detail(normalizedTicker),
      queryFn: () => getStock(normalizedTicker),
      staleTime: 60 * 1000,
    });
  };
}

export default useStocks;
