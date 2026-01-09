/**
 * Loading Component
 * Displayed while page content is loading
 */
export default function Loading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center space-y-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-border border-t-accent" />
        <p className="text-sm text-foreground-muted">Loading...</p>
      </div>
    </div>
  );
}
