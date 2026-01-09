"use client";

/**
 * Global Error Boundary
 * Handles errors in the root layout that error.tsx cannot catch.
 * This is the last line of defense for unhandled errors.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="bg-black text-white">
        <div className="flex min-h-screen items-center justify-center p-4">
          <div className="max-w-lg rounded-lg border border-red-500/50 bg-red-500/10 p-8 text-center">
            <svg
              className="mx-auto h-16 w-16 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h1 className="mt-4 text-2xl font-bold text-red-500">
              Application Error
            </h1>
            <p className="mt-2 text-gray-400">
              A critical error has occurred. Please try refreshing the page.
            </p>
            {error.digest && (
              <p className="mt-2 text-xs text-gray-500">
                Error ID: {error.digest}
              </p>
            )}
            <div className="mt-6 flex justify-center gap-4">
              <button
                onClick={reset}
                className="rounded-lg bg-red-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-600"
              >
                Try Again
              </button>
              <button
                onClick={() => (window.location.href = "/")}
                className="rounded-lg border border-gray-600 px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-800"
              >
                Go Home
              </button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
