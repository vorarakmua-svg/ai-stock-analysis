import Link from "next/link";

/**
 * 404 Not Found Page
 */
export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-foreground-muted">404</h1>
        <h2 className="mt-4 text-xl font-semibold">Page Not Found</h2>
        <p className="mt-2 text-foreground-muted">
          The page you are looking for does not exist.
        </p>
        <Link
          href="/"
          className="mt-6 inline-block rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
        >
          Back to Home
        </Link>
      </div>
    </div>
  );
}
