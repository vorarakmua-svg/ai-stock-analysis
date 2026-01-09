import type { Metadata } from "next";
import { QueryProvider } from "@/providers/query-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Intelligent Investor Pro",
  description:
    "Bloomberg Terminal-style stock analysis with AI-powered valuations and Warren Buffett-style investment memos",
  keywords: [
    "stock analysis",
    "valuation",
    "DCF",
    "Graham Number",
    "Warren Buffett",
    "investing",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        {/* Preconnect to Google Fonts for JetBrains Mono */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <QueryProvider>
          {/* Skip to main content link for accessibility */}
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-background"
          >
            Skip to main content
          </a>

          {/* Header */}
          <header className="sticky top-0 z-50 border-b border-border bg-background-secondary/95 backdrop-blur supports-[backdrop-filter]:bg-background-secondary/60">
            <div className="container mx-auto flex h-14 items-center px-4">
              <div className="flex items-center space-x-4">
                <a href="/" className="flex items-center space-x-2">
                  <span className="text-xl font-bold tracking-tight text-foreground">
                    Intelligent Investor Pro
                  </span>
                </a>
              </div>
              <nav className="ml-auto flex items-center space-x-6">
                <a
                  href="/"
                  className="text-sm font-medium text-foreground-muted transition-colors hover:text-foreground"
                >
                  Screener
                </a>
              </nav>
            </div>
          </header>

          {/* Main Content */}
          <main id="main-content" className="container mx-auto px-4 py-6">{children}</main>

          {/* Footer */}
          <footer className="border-t border-border bg-background-secondary py-4">
            <div className="container mx-auto px-4 text-center text-xs text-foreground-muted">
              <p>
                Intelligent Investor Pro - AI-Powered Stock Analysis
              </p>
              <p className="mt-1">
                Data for educational purposes only. Not financial advice.
              </p>
            </div>
          </footer>
        </QueryProvider>
      </body>
    </html>
  );
}
