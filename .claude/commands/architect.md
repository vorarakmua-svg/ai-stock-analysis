# Role: Senior Backend Architect

**Mission:** Build the Core Infrastructure for "ValueInvestAI".

---

## Context

We are building a stock analysis platform using FastAPI, PostgreSQL, and Docker. This is the foundational layer that all other agents will build upon.

**Reference Document:** Use `PROJECT_BLUEPRINT.md` (specifically Section 2: Tech Stack Strategy and Section 5: Database Design).

---

## Tasks

### 1. Infrastructure Setup
Create `docker-compose.yml` with the following services:
- **FastAPI backend** (port 8000)
- **PostgreSQL 16** with persistent volume
- **Redis 7** for caching and rate limiting

Ensure proper networking between services and environment variable configuration.

### 2. Database Models
Write SQLAlchemy models in `backend/app/models/` exactly as defined in the Blueprint:
- `Company` - Master table for US and Thai stocks
- `IncomeStatement` - 30 years of income data
- `BalanceSheet` - Assets, liabilities, equity history
- `CashFlowStatement` - Operating, investing, financing flows
- `StockPrice` - Daily price data (partitioned)
- `Valuation` - Cached calculation results
- `AIAnalysis` - Buffett AI verdicts
- `DataFetchLog` - API cost tracking

**Critical Constraint:** The `companies` table must handle both US (`AAPL`) and Thai (`PTT.BK`) ticker formats. Include:
- `ticker` (unique, handles both formats)
- `market` (US or SET)
- `currency` (USD or THB)

### 3. API Shell
Create the main FastAPI entry point (`backend/app/main.py`) with:
- Health check endpoint at `/health`
- API versioning at `/api/v1`
- Empty router shells (controllers) for:
  - `/companies` - Company CRUD operations
  - `/financials` - Financial statement queries
  - `/valuations` - Valuation calculations
  - `/ai-analysis` - Buffett AI endpoints

### 4. Database Migration
- Initialize Alembic in `backend/alembic/`
- Generate the first migration script for all models
- Ensure migrations run automatically on container startup

---

## Directory Structure to Create

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings with pydantic-settings
│   ├── database.py          # SQLAlchemy async engine
│   ├── models/
│   │   ├── __init__.py
│   │   ├── company.py
│   │   ├── financials.py
│   │   └── valuations.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── companies.py
│   │       ├── financials.py
│   │       └── valuations.py
│   └── services/
│       └── __init__.py
├── alembic/
│   └── versions/
├── alembic.ini
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Expected Output

A working Docker environment where:
1. `docker-compose up` starts all services successfully
2. PostgreSQL database has all tables created via migration
3. Redis is running and accessible
4. FastAPI `/health` endpoint returns `{"status": "healthy"}`
5. OpenAPI docs are available at `/docs`

---

## Technical Specifications

### Dependencies (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
pydantic-settings==2.1.0
python-dotenv==1.0.0
redis==5.0.1
httpx==0.26.0
```

### Docker Compose Ports
- Backend: 8000
- PostgreSQL: 5432
- Redis: 6379
