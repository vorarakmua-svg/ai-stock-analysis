"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from "@tanstack/react-query";
import { getValuation, refreshValuation } from "@/lib/api";
import type { ValuationResult } from "@/types/valuation";

/**
 * Query Keys for Valuation React Query cache management
 */
export const valuationQueryKeys = {
  all: ["valuations"] as const,
  detail: (ticker: string) => [...valuationQueryKeys.all, ticker] as const,
};

/**
 * Cache Configuration for Valuation Data
 * Valuation calculations are expensive and don't change rapidly
 */
const VALUATION_CACHE_CONFIG = {
  /** 5 minutes - valuation doesn't change rapidly */
  staleTime: 5 * 60 * 1000,
  /** 30 minutes - keep in cache for longer */
  gcTime: 30 * 60 * 1000,
};

/**
 * Hook to fetch valuation data for a stock
 *
 * @param ticker - Stock ticker symbol (e.g., 'AAPL')
 * @param enabled - Whether to enable the query (default: true)
 * @returns Query result with valuation data including DCF and Graham analysis
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useValuation('AAPL');
 *
 * if (isLoading) return <ValuationSkeleton />;
 * if (error) return <ErrorMessage error={error} />;
 *
 * return <ValuationCard valuation={data} />;
 * ```
 */
export function useValuation(
  ticker: string,
  enabled: boolean = true
): UseQueryResult<ValuationResult, Error> {
  return useQuery({
    queryKey: valuationQueryKeys.detail(ticker),
    queryFn: () => getValuation(ticker),
    enabled: !!ticker && enabled,
    staleTime: VALUATION_CACHE_CONFIG.staleTime,
    gcTime: VALUATION_CACHE_CONFIG.gcTime,
    // Retry failed requests with exponential backoff
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
}

/**
 * Hook to force refresh valuation calculation
 *
 * @returns Mutation result with refresh function
 *
 * @example
 * ```tsx
 * const { mutate: refreshValuation, isPending } = useRefreshValuation();
 *
 * <Button onClick={() => refreshValuation('AAPL')} disabled={isPending}>
 *   {isPending ? 'Refreshing...' : 'Refresh Valuation'}
 * </Button>
 * ```
 */
export function useRefreshValuation(): UseMutationResult<
  ValuationResult,
  Error,
  string,
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticker: string) => refreshValuation(ticker),
    onSuccess: (data, ticker) => {
      // Update the cache with fresh data
      queryClient.setQueryData(valuationQueryKeys.detail(ticker), data);
    },
    onError: (error) => {
      console.error("Failed to refresh valuation:", error);
    },
  });
}

/**
 * Hook to prefetch valuation data
 * Useful for hover prefetching on stock list
 */
export function usePrefetchValuation(): (ticker: string) => void {
  const queryClient = useQueryClient();

  return (ticker: string) => {
    queryClient.prefetchQuery({
      queryKey: valuationQueryKeys.detail(ticker),
      queryFn: () => getValuation(ticker),
      staleTime: VALUATION_CACHE_CONFIG.staleTime,
    });
  };
}

/**
 * Hook to invalidate valuation cache
 * Forces refetch on next access
 */
export function useInvalidateValuation(): (ticker: string) => Promise<void> {
  const queryClient = useQueryClient();

  return async (ticker: string) => {
    await queryClient.invalidateQueries({
      queryKey: valuationQueryKeys.detail(ticker),
    });
  };
}

export default useValuation;
