"use client";

import { useEffect } from "react";
import Link from "next/link";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

/**
 * Stock Detail Page Error Boundary
 * Displayed when an error occurs while loading stock data
 */
export default function StockDetailError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error("Stock detail error:", error);
  }, [error]);

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

      {/* Error Card */}
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="max-w-md rounded-lg border border-negative/50 bg-negative/10 p-8 text-center">
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
          <h2 className="mt-4 text-xl font-semibold text-negative">
            Failed to Load Stock Data
          </h2>
          <p className="mt-2 text-foreground-muted">
            Unable to fetch stock information. Please try again.
          </p>
          {/* Only show error details in development */}
          {process.env.NODE_ENV === "development" && (
            <details className="mt-4 text-left">
              <summary className="cursor-pointer text-xs text-foreground-muted/60">
                Debug Info (Dev Only)
              </summary>
              <pre className="mt-2 overflow-auto rounded bg-background-tertiary p-2 text-xs">
                {error.message}
                {error.digest && `\nDigest: ${error.digest}`}
              </pre>
            </details>
          )}
          <div className="mt-6 flex justify-center gap-3">
            <button
              onClick={reset}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
            >
              Try Again
            </button>
            <Link
              href="/"
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground-muted transition-colors hover:bg-background-tertiary"
            >
              Return to Screener
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
