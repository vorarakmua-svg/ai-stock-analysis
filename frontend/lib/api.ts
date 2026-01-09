import axios, { AxiosInstance, AxiosError, AxiosResponse } from "axios";
import {
  StockSummary,
  StockDetail,
  RealTimePrice,
  HistoricalDataPoint,
  ChartPeriod,
} from "@/types/stock";
import { ValuationResult } from "@/types/valuation";
import { WarrenBuffettAnalysis } from "@/types/analysis";

/**
 * API Configuration
 */
const getApiBaseUrl = (): string => {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    // In production, throw error if API URL is not configured
    if (process.env.NODE_ENV === "production") {
      throw new Error(
        "NEXT_PUBLIC_API_URL must be configured in production environment"
      );
    }
    // In development, fallback to localhost
    return "http://localhost:8000";
  }
  return url;
};

const API_BASE_URL = getApiBaseUrl();
const API_PREFIX = "/api/v1";

/**
 * Create Axios instance with default configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Response interceptor for error handling
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      console.error(
        `API Error: ${error.response.status} - ${error.response.statusText}`
      );
    } else if (error.request) {
      // Request made but no response received
      console.error("API Error: No response received from server");
    } else {
      // Error setting up request
      console.error(`API Error: ${error.message}`);
    }
    return Promise.reject(error);
  }
);

/**
 * Stock Screener Filters
 */
export interface StockFilters {
  sector?: string;
  industry?: string;
  minMarketCap?: number;
  maxMarketCap?: number;
  minPE?: number;
  maxPE?: number;
  minDividendYield?: number;
  maxDividendYield?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

/**
 * API Response Types
 */
export interface StocksResponse {
  stocks: StockSummary[];
  total: number;
}

export interface StockResponse {
  stock: StockDetail;
}

export interface PriceResponse {
  ticker: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  bid: number | null;
  ask: number | null;
  high: number | null;
  low: number | null;
  open: number | null;
  previous_close: number | null;
  timestamp: string;
  market_state: "PRE" | "REGULAR" | "POST" | "CLOSED";
}


/**
 * Fetch all stocks with optional filters
 * @param filters - Optional filtering and sorting parameters
 * @returns Promise with array of stock summaries
 */
export async function getStocks(
  filters?: StockFilters
): Promise<StockSummary[]> {
  const params = new URLSearchParams();

  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        params.append(key, String(value));
      }
    });
  }

  const response = await apiClient.get<StocksResponse>("/stocks", {
    params,
  });

  // Normalize dividend_yield from percentage form (0.4 = 0.4%) to decimal form (0.004)
  // yfinance returns dividend_yield in percentage form while other ratios are in decimal form
  return response.data.stocks.map((stock) => ({
    ...stock,
    dividend_yield: stock.dividend_yield ? stock.dividend_yield / 100 : null,
  }));
}

/**
 * Backend response structure for stock detail
 */
interface BackendStockResponse {
  ticker: string;
  data: {
    ticker?: string;
    cik?: string;
    company_name?: string;
    collected_at?: string;
    data_sources?: string;
    company_info?: {
      name?: string;
      sector?: string;
      industry?: string;
      country?: string;
      website?: string;
      full_time_employees?: number;
    };
    market_data?: {
      current_price?: number;
      market_cap?: number;
      volume?: number;
      beta?: number;
      fifty_two_week_high?: number;
      fifty_two_week_low?: number;
      fifty_day_average?: number;
      two_hundred_day_average?: number;
      ma_50?: number;
      ma_200?: number;
    };
    valuation?: {
      pe_trailing?: number;
      pe_forward?: number;
      peg_ratio?: number;
      price_to_book?: number;
      eps_trailing?: number;
      eps_forward?: number;
      dividend_yield?: number;
      dividend_rate?: number;
      total_revenue?: number;
      net_income?: number;
      ebitda?: number;
      total_cash?: number;
      total_debt?: number;
      profit_margin?: number;
      operating_margin?: number;
      return_on_equity?: number;
      return_on_assets?: number;
      revenue_growth?: number;
      debt_to_equity?: number;
      free_cash_flow?: number;
      operating_cash_flow?: number;
      enterprise_value?: number;
      ev_to_ebitda?: number;
    };
    shareholders?: {
      shares_outstanding?: number;
      float_shares?: number;
      insider_percent?: number;
      institutional_percent?: number;
      short_ratio?: number;
    };
    calculated_metrics?: {
      calc_ebitda?: number;
      calc_ev?: number;
      calc_ev_to_ebitda?: number;
      calc_fcf?: number;
      calc_interest_coverage?: number;
      calc_net_debt?: number;
      calc_roic?: number;
    };
    performance?: {
      cagr_5y?: number;
      total_return_5y?: number;
      annual_volatility?: number;
      max_drawdown?: number;
      sharpe_ratio?: number;
    };
    [key: string]: unknown;
  };
}

/**
 * Transform backend response to StockDetail format
 * @throws Error if response structure is invalid
 */
function transformStockResponse(response: BackendStockResponse): StockDetail {
  // Validate required response structure
  if (!response || typeof response !== "object") {
    throw new Error("Invalid API response: response is null or not an object");
  }

  const { ticker, data } = response;

  if (!ticker || typeof ticker !== "string") {
    throw new Error("Invalid API response: missing or invalid ticker");
  }

  if (!data || typeof data !== "object") {
    throw new Error(`Invalid API response: missing data for ticker ${ticker}`);
  }

  // Safely extract nested objects with defaults
  const company = data.company_info || {};
  const market = data.market_data || {};
  const valuation = data.valuation || {};
  const shareholders = data.shareholders || {};
  const calculated = data.calculated_metrics || {};
  const performance = data.performance || {};

  return {
    // Identifiers
    ticker: data.ticker || ticker,
    cik: data.cik || "",
    company_name: data.company_name || company.name || ticker,

    // Classification
    sector: company.sector || "Unknown",
    industry: company.industry || "Unknown",
    country: company.country || "US",
    website: company.website || null,

    // Price & Market Data
    current_price: market.current_price || 0,
    market_cap: market.market_cap || 0,
    volume: market.volume || 0,
    shares_outstanding: shareholders.shares_outstanding || 0,
    float_shares: shareholders.float_shares || null,

    // Valuation Ratios
    pe_trailing: valuation.pe_trailing || null,
    pe_forward: valuation.pe_forward || null,
    peg_ratio: valuation.peg_ratio || null,
    price_to_book: valuation.price_to_book || null,

    // Earnings
    eps_trailing: valuation.eps_trailing || null,
    eps_forward: valuation.eps_forward || null,

    // Dividends - dividend_yield is in percentage (0.76 = 0.76%), convert if needed
    dividend_yield: valuation.dividend_yield ? valuation.dividend_yield / 100 : null,

    // Risk Metrics
    beta: market.beta || null,
    annual_volatility: performance.annual_volatility || null,
    max_drawdown: performance.max_drawdown || null,
    sharpe_ratio: performance.sharpe_ratio || null,
    risk_free_rate_10y: null,

    // Income Statement (from valuation section)
    total_revenue: valuation.total_revenue || null,
    net_income: valuation.net_income || null,
    ebitda: valuation.ebitda || calculated.calc_ebitda || null,
    profit_margin: valuation.profit_margin || null,
    operating_margin: valuation.operating_margin || null,
    revenue_growth: valuation.revenue_growth || null,

    // Balance Sheet (from valuation section)
    total_cash: valuation.total_cash || null,
    total_debt: valuation.total_debt || null,
    debt_to_equity: valuation.debt_to_equity || null,

    // Profitability Ratios (from valuation section)
    return_on_equity: valuation.return_on_equity || null,
    return_on_assets: valuation.return_on_assets || null,

    // 52-Week Range (field names are fifty_two_week_high, not 52_week_high)
    "52_week_high": market.fifty_two_week_high || null,
    "52_week_low": market.fifty_two_week_low || null,

    // Moving Averages
    ma_50: market.ma_50 || market.fifty_day_average || null,
    ma_200: market.ma_200 || market.two_hundred_day_average || null,

    // Performance
    cagr_5y: performance.cagr_5y || null,
    total_return_5y: performance.total_return_5y || null,

    // Ownership (from shareholders section)
    insider_percent: shareholders.insider_percent || null,
    institutional_percent: shareholders.institutional_percent || null,
    short_ratio: shareholders.short_ratio || null,

    // Employees
    employees: company.full_time_employees || null,

    // Calculated Metrics
    calc_ebitda: calculated.calc_ebitda || valuation.ebitda || null,
    calc_ev: calculated.calc_ev || valuation.enterprise_value || null,
    calc_ev_to_ebitda: calculated.calc_ev_to_ebitda || valuation.ev_to_ebitda || null,
    calc_fcf: calculated.calc_fcf || valuation.free_cash_flow || null,
    calc_interest_coverage: calculated.calc_interest_coverage || null,
    calc_net_debt: calculated.calc_net_debt || null,
    calc_roic: calculated.calc_roic || null,
    free_cash_flow: valuation.free_cash_flow || calculated.calc_fcf || null,

    // SEC Filing Data (not always present)
    sec_fiscal_year: null,
    sec_net_income: null,
    sec_operating_cash_flow: null,
    sec_revenue: null,
    sec_stockholders_equity: null,
    sec_total_assets: null,
    sec_total_liabilities: null,

    // Metadata
    collected_at: data.collected_at || new Date().toISOString(),
    data_sources: data.data_sources || "API",
    treasury_yield_source: null,
    error_count: 0,
    warning_count: 0,
  };
}

/**
 * Fetch single stock by ticker
 * @param ticker - Stock ticker symbol (e.g., 'AAPL')
 * @returns Promise with stock detail data
 * @throws Error if API request fails or response is invalid
 */
export async function getStock(ticker: string): Promise<StockDetail> {
  try {
    const response = await apiClient.get<BackendStockResponse>(`/stocks/${ticker}`);
    return transformStockResponse(response.data);
  } catch (error) {
    // Re-throw axios errors as-is (they have proper error messages)
    if (error instanceof AxiosError) {
      throw error;
    }
    // Wrap transformation errors with context
    throw new Error(`Failed to process stock data for ${ticker}: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}

/**
 * Fetch real-time price for a stock
 * @param ticker - Stock ticker symbol
 * @returns Promise with current price data
 */
export async function getStockPrice(ticker: string): Promise<RealTimePrice> {
  const response = await apiClient.get<RealTimePrice>(
    `/stocks/${ticker}/price`
  );
  return response.data;
}

/**
 * Fetch historical OHLCV data for a stock
 * @param ticker - Stock ticker symbol
 * @param period - Time period for historical data
 * @returns Promise with historical data array
 */
export async function getStockHistory(
  ticker: string,
  period: ChartPeriod
): Promise<HistoricalDataPoint[]> {
  const response = await apiClient.get<HistoricalDataPoint[]>(
    `/stocks/${ticker}/history`,
    { params: { period } }
  );
  return response.data;
}

/**
 * Fetch valuation data for a stock
 * @param ticker - Stock ticker symbol
 * @returns Promise with valuation result including DCF and Graham analysis
 */
export async function getValuation(ticker: string): Promise<ValuationResult> {
  const response = await apiClient.get<ValuationResult>(
    `/stocks/${ticker}/valuation`,
    { timeout: 60000 } // 60 seconds for valuation calculation
  );
  return response.data;
}

/**
 * Force refresh valuation calculation for a stock
 * Bypasses cache and recalculates all valuation metrics
 * @param ticker - Stock ticker symbol
 * @returns Promise with fresh valuation result
 */
export async function refreshValuation(ticker: string): Promise<ValuationResult> {
  const response = await apiClient.post<ValuationResult>(
    `/stocks/${ticker}/valuation/refresh`,
    undefined,
    { timeout: 60000 } // 60 seconds for valuation calculation
  );
  return response.data;
}

/**
 * Fetch AI analysis for a stock
 * Returns a Warren Buffett-style investment memo generated by AI.
 * @param ticker - Stock ticker symbol
 * @returns Promise with AI analysis data
 */
export async function getAnalysis(ticker: string): Promise<WarrenBuffettAnalysis> {
  const response = await apiClient.get<WarrenBuffettAnalysis>(
    `/stocks/${ticker}/analysis`,
    { timeout: 120000 } // 2 minutes - AI analysis can take time on first request
  );
  return response.data;
}

/**
 * Force refresh AI analysis for a stock
 * Triggers a new AI analysis generation, bypassing the cache.
 * This is an expensive operation that may take 30-60 seconds.
 * @param ticker - Stock ticker symbol
 * @returns Promise with fresh AI analysis data
 */
export async function refreshAnalysis(ticker: string): Promise<WarrenBuffettAnalysis> {
  const response = await apiClient.post<WarrenBuffettAnalysis>(
    `/stocks/${ticker}/analysis/refresh`,
    undefined,
    { timeout: 120000 } // 2 minutes for AI generation
  );
  return response.data;
}

/**
 * Legacy alias for getAnalysis
 * @deprecated Use getAnalysis instead
 */
export const getAIAnalysis = getAnalysis;

export default apiClient;
