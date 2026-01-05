# Role: Senior Frontend Developer (React/Next.js)

**Mission:** Build the User Interface for "ValueInvestAI".

---

## Context

We're building a professional dashboard to visualize 30 years of financial data and AI-powered investment analysis. The UI should be clean, data-dense, and suitable for serious value investors.

**Reference Document:** Use `PROJECT_BLUEPRINT.md` (Section 9: Frontend Architecture).

---

## Tasks

### 1. Project Setup
Initialize Next.js 14 with App Router in `frontend/`:

```bash
npx create-next-app@14 frontend --typescript --tailwind --app --src-dir
```

**Install dependencies:**
```json
{
  "next": "14.1.0",
  "react": "18.2.0",
  "typescript": "5.3.3",
  "tailwindcss": "3.4.1",
  "recharts": "2.10.4",
  "@tanstack/react-query": "5.17.0",
  "zustand": "4.5.0",
  "axios": "1.6.5"
}
```

### 2. Core Components
Build the following components in `frontend/src/components/`:

**FinancialTable.tsx**
- A scrollable table displaying 30 years of financial data
- Columns: Year, Revenue, Net Income, EPS, FCF, etc.
- Horizontal scroll for many years
- Highlight negative values in red
- Support for sorting by column

**DCFChart.tsx**
- Recharts line graph showing:
  - Historical stock price
  - DCF intrinsic value over time
  - Graham Number line
- Interactive tooltips with values
- Legend for each line

**BuffettVerdict.tsx**
- A card displaying the AI's analysis:
  - Large BUY/HOLD/SELL verdict with color coding
    - BUY: Green (#10B981)
    - HOLD: Yellow (#F59E0B)
    - SELL: Red (#EF4444)
  - Confidence percentage with gauge/bar
  - Summary quote in Buffett's voice
  - Expandable pros/cons lists
  - Full analysis in collapsible section

**MoatIndicator.tsx**
- Visual gauge showing moat strength
- Wide/Narrow/None with corresponding colors
- ROIC trend sparkline
- Competitive advantage period display

**StockHeader.tsx**
- Company name and ticker
- Current price with daily change
- Market indicator (US/SET flag)
- Currency symbol ($/฿)

**QuickMetrics.tsx**
- 2-column grid of key statistics:
  - P/E Ratio, P/B Ratio
  - Market Cap, 52-week Range
  - Dividend Yield, EPS Growth

### 3. Pages
Create the dynamic route structure:

**`/` (Home)**
- Market overview
- Trending/recently analyzed stocks
- Quick search bar

**`/stock/[ticker]` (Main Stock Page)**
- StockHeader
- QuickMetrics
- AIVerdictBanner (prominent)
- Tab container with:
  - Overview Tab: PriceChart, KeyStats, MoatIndicator
  - Financials Tab: StatementSelector, FinancialTable, TrendCharts
  - Valuation Tab: DCFCalculator, GrahamNumber, LynchFairValue
  - Health Tab: AltmanZScore, PiotroskiFScore, DebtAnalysis
  - AI Analysis Tab: Full BuffettVerdict with detailed analysis

**`/search`**
- Search results with company cards
- Filter by market (US/SET)
- Filter by sector

### 4. State Management
**React Query setup** (`frontend/src/lib/query-client.ts`):
- Configure stale times for financial data (1 hour)
- Set up prefetching for stock pages

**Custom hooks** (`frontend/src/hooks/`):
- `useFinancials(ticker)` - Fetch financial statements
- `useValuations(ticker)` - Fetch valuation calculations
- `useAIAnalysis(ticker)` - Fetch Buffett AI analysis
- `useStockPrice(ticker)` - Fetch price history

**Zustand store** (`frontend/src/stores/stockStore.ts`):
- Current ticker state
- Currency display preference (native vs USD)
- Theme preferences

---

## Directory Structure to Create

```
frontend/src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx              # Home
│   ├── stock/
│   │   └── [ticker]/
│   │       └── page.tsx      # Stock detail
│   └── search/
│       └── page.tsx
├── components/
│   ├── ui/                   # Base UI components
│   │   ├── Card.tsx
│   │   ├── Button.tsx
│   │   ├── Table.tsx
│   │   └── Tabs.tsx
│   ├── charts/
│   │   ├── DCFChart.tsx
│   │   ├── TrendChart.tsx
│   │   └── PriceChart.tsx
│   ├── stock/
│   │   ├── StockHeader.tsx
│   │   ├── QuickMetrics.tsx
│   │   ├── FinancialTable.tsx
│   │   └── MoatIndicator.tsx
│   └── ai/
│       └── BuffettVerdict.tsx
├── hooks/
│   ├── useFinancials.ts
│   ├── useValuations.ts
│   └── useAIAnalysis.ts
├── stores/
│   └── stockStore.ts
├── lib/
│   ├── api.ts               # Axios instance
│   └── query-client.ts      # React Query config
└── types/
    ├── financials.ts
    ├── valuations.ts
    └── ai-analysis.ts
```

---

## Currency Display Constraint

**Critical:** The UI must support switching currencies visually based on the stock's origin:
- Thai stocks (SET) display in ฿ (Baht)
- US stocks display in $ (Dollar)
- Add a toggle to convert to user's preferred currency
- Format numbers appropriately (e.g., $1,234.56 or ฿45,678.90)

---

## Responsive Design

- Desktop: Full multi-column layouts
- Tablet: Stacked layouts with horizontal scroll for tables
- Mobile: Single column, collapsible sections

---

## Expected Output

A fully functional Next.js 14 application where:
1. Users can search and view any tracked stock
2. 30 years of financial data is displayed in scrollable tables
3. Interactive charts show price vs intrinsic value
4. AI Buffett verdict is prominently displayed
5. All valuation metrics are visualized
6. Currency handling works correctly for US/Thai stocks
7. Responsive design works on all device sizes
