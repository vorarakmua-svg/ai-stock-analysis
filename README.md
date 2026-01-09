# Intelligent Investor Pro

A local-first stock analysis web application combining AI-powered data normalization with CFA-grade valuation methodologies. Features a Bloomberg Terminal-style interface with real-time data, interactive charts, and Warren Buffett-style AI analysis.

## Features

- **Stock Screener**: Bloomberg Terminal-style data grid with 80+ financial columns, filtering, and sorting
- **Real-time Prices**: Live stock prices via yfinance with configurable refresh intervals
- **Interactive Charts**: TradingView-style candlestick charts with multiple timeframes (1D, 1W, 1M, 3M, 6M, 1Y, 5Y)
- **AI-Powered Valuation**: DCF analysis with three scenarios (conservative, base, optimistic)
- **Graham Analysis**: Benjamin Graham intrinsic value formulas and defensive investor screen
- **Warren Buffett Memos**: AI-generated investment analysis in Buffett's writing style
- **Column Customization**: Show/hide columns by category with persistent preferences
- **Dark Mode**: Professional Bloomberg-style dark interface optimized for financial data

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **Google Gemini AI** (gemini-2.0-flash) for data extraction and analysis
- **yfinance** for real-time stock data and historical prices
- **Pandas/NumPy** for data processing and calculations
- **diskcache** for persistent caching (7-day TTL for AI analysis)
- **slowapi** for rate limiting

### Frontend
- **Next.js 16** with React 19 and Turbopack
- **TanStack Query** for data fetching and caching
- **AG Grid** for professional data tables
- **Lightweight Charts** for TradingView-style financial charts
- **Tailwind CSS** with custom Bloomberg-style theme
- **TypeScript** for type safety

## Project Structure

```
ai-stock-analysis/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API route handlers
│   │   ├── core/                # Data loading utilities
│   │   ├── models/              # Pydantic schemas
│   │   ├── services/            # Business logic (valuation, AI)
│   │   ├── config.py            # Settings management
│   │   └── main.py              # FastAPI application
│   ├── cache/                   # Persistent cache storage
│   └── requirements.txt
├── frontend/
│   ├── app/                     # Next.js app router pages
│   ├── components/              # React components
│   │   ├── screener/            # DataGrid, ColumnSelector
│   │   ├── stock/               # StockDetail, Charts, Valuation
│   │   └── ui/                  # Shared UI components
│   ├── hooks/                   # Custom React hooks
│   ├── lib/                     # API client, utilities
│   └── types/                   # TypeScript definitions
├── data/
│   └── output/
│       ├── csv/summary.csv      # Stock summary data
│       └── json/{ticker}.json   # Detailed stock data
└── docker-compose.yml
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Google Gemini API key (for AI features)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Open http://localhost:3000 in your browser.

## Environment Variables

### Backend (.env)
```env
APP_ENV=development
DEBUG=false
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash
DATA_DIR=../data
CSV_PATH=../data/output/csv/summary.csv
JSON_DIR=../data/output/json
CORS_ORIGINS=["http://localhost:3000"]
PRICE_CACHE_TTL=30
VALUATION_CACHE_TTL=86400
ANALYSIS_CACHE_TTL=604800
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/stocks` | GET | List all stocks with summary data |
| `/api/v1/stocks/{ticker}` | GET | Get detailed stock data |
| `/api/v1/stocks/{ticker}/price` | GET | Get real-time price |
| `/api/v1/stocks/{ticker}/history` | GET | Get historical OHLCV data |
| `/api/v1/stocks/{ticker}/valuation` | GET | Get DCF and Graham valuation |
| `/api/v1/stocks/{ticker}/valuation/refresh` | POST | Force recalculate valuation |
| `/api/v1/stocks/{ticker}/analysis` | GET | Get AI investment analysis |
| `/api/v1/stocks/{ticker}/analysis/refresh` | POST | Force regenerate AI analysis |

## Available Stocks (100)

**Technology**: AAPL, MSFT, NVDA, AVGO, ORCL, CSCO, IBM, INTC, AMD, QCOM, TXN, ADI, AMAT, LRCX, KLAC, MU, CRM, NOW, INTU, ADBE, PANW, CRWD, ANET, PLTR

**Communication**: GOOG, META, NFLX, DIS, T, VZ, TMUS

**Consumer**: AMZN, TSLA, HD, COST, WMT, MCD, PG, KO, PEP, TJX, LOW

**Financial**: BRK-B, JPM, V, MA, BAC, WFC, GS, MS, BLK, SCHW, C, AXP, COF, BX, KKR, IBKR, SPGI, PGR

**Healthcare**: LLY, UNH, JNJ, ABBV, MRK, PFE, TMO, ABT, AMGN, GILD, ISRG, BSX, SYK, DHR, VRTX, BMY, HCA

**Industrial**: GE, CAT, RTX, HON, UNP, DE, BA, LMT, PH, GEV, APH

**Energy**: XOM, CVX, COP, SCCO, NEM

**Other**: PM, NEE, PLD, WELL, UBER, BKNG, APP

## Docker Deployment

```bash
# Copy environment file
cp .env.example .env
# Add your GOOGLE_API_KEY to .env

# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

## Development

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run lint
npm run build
```

### Code Style
- Backend: Python with type hints, Black formatting
- Frontend: TypeScript with ESLint, Prettier

## Troubleshooting

### "No response received from server"
- Ensure backend is running on port 8000
- Check CORS_ORIGINS includes your frontend URL
- Verify GOOGLE_API_KEY is set for AI features

### API returns 422 for ticker
- Ticker format: 1-10 characters, starts with letter
- Allowed characters: A-Z, 0-9, dots (.), hyphens (-)
- Example valid tickers: AAPL, BRK-B, BRK.A

### AI Analysis slow on first request
- Initial AI analysis generation takes 30-60 seconds
- Subsequent requests use cache (7-day TTL)
- Use `/analysis/refresh` to force regeneration

## License

MIT License
