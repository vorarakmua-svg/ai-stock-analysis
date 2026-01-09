/**
 * Stock Detail Loading State
 */
export default function StockLoading() {
  return (
    <div className="space-y-6">
      {/* Back Button Skeleton */}
      <div className="h-5 w-32 skeleton rounded" />

      {/* Header Skeleton */}
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="h-10 w-24 skeleton rounded" />
            <div className="h-6 w-20 skeleton rounded-full" />
          </div>
          <div className="h-6 w-48 skeleton rounded" />
          <div className="h-4 w-32 skeleton rounded" />
        </div>
        <div className="text-right">
          <div className="h-12 w-32 skeleton rounded" />
          <div className="mt-2 h-5 w-24 skeleton rounded" />
        </div>
      </div>

      {/* Metrics Grid Skeleton */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-5">
        {Array.from({ length: 10 }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border border-border bg-background-secondary p-4"
          >
            <div className="h-3 w-16 skeleton rounded" />
            <div className="mt-2 h-6 w-20 skeleton rounded" />
          </div>
        ))}
      </div>

      {/* Financial Details Skeleton */}
      <div className="grid gap-6 lg:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <div
            key={i}
            className="rounded-lg border border-border bg-background-secondary p-6"
          >
            <div className="mb-4 h-6 w-32 skeleton rounded" />
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, j) => (
                <div key={j} className="flex items-center justify-between">
                  <div className="h-4 w-24 skeleton rounded" />
                  <div className="h-4 w-16 skeleton rounded" />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* 52-Week Range Skeleton */}
      <div className="rounded-lg border border-border bg-background-secondary p-6">
        <div className="mb-4 h-6 w-32 skeleton rounded" />
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="h-4 w-16 skeleton rounded" />
            <div className="h-4 w-16 skeleton rounded" />
          </div>
          <div className="h-2 w-full skeleton rounded-full" />
          <div className="flex items-center justify-between">
            <div className="h-4 w-20 skeleton rounded" />
            <div className="h-4 w-20 skeleton rounded" />
          </div>
        </div>
      </div>
    </div>
  );
}
