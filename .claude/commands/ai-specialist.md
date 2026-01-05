# Role: AI Integration Engineer

**Mission:** Build the "Buffett AI" Analyst for "ValueInvestAI".

---

## Context

We need an AI agent that analyzes financial JSON data and outputs an investment opinion in the style of Warren Buffett. The AI should be skeptical, focused on economic moats and margin of safety, and cite specific numbers from the provided data.

**Reference Document:** Use `PROJECT_BLUEPRINT.md` (Section 7: Buffett AI Integration).

---

## Tasks

### 1. Data Aggregation Helper
Create `backend/app/ai/data_aggregator.py`:

Implement `summarize_for_ai(ticker: str) -> FinancialSummary`:
- Aggregates the last 10 years of DB data into a clean JSON context
- Returns a Pydantic model with all relevant financial metrics

**FinancialSummary should include:**
- Company info (ticker, name, market, sector, currency)
- Revenue & profitability trends (10 years)
- Free cash flow history
- Margin histories (gross, operating, net)
- Balance sheet strength (D/E, current ratio, interest coverage)
- Returns (ROIC, ROE over 10 years)
- Current valuation metrics (P/E, P/B, P/S, EV/EBITDA)
- Our calculated values (DCF, Graham, Lynch, Z-Score, F-Score, Moat Rating)

### 2. Gemini Client
Implement `backend/app/ai/gemini_client.py` using `google-generativeai` SDK:

```python
class GeminiAnalyzer:
    def __init__(self, api_key: str):
        # Configure Gemini Pro with JSON output mode

    async def analyze_stock(
        self,
        summary: FinancialSummary,
        system_prompt: str,
        user_prompt: str
    ) -> AIAnalysisResult:
        # Send to Gemini and parse structured response
```

**Configuration:**
- Model: `gemini-1.5-pro`
- Temperature: 0.7 (balanced creativity)
- Response format: JSON mode (`response_mime_type="application/json"`)
- Max tokens: 4096

### 3. Prompt Engineering
Implement prompts in `backend/app/ai/prompts.py`:

**BUFFETT_SYSTEM_PROMPT:**
- Persona: Warren Buffett, skeptical value investor
- Core Principles:
  1. Circle of Competence - Only invest in understood businesses
  2. Economic Moat - Durable competitive advantages
  3. Quality Management - Integrity and capital allocation
  4. Margin of Safety - Never pay full price
  5. Long-term Thinking - Buy businesses, not stocks

- Analysis Framework:
  - Is this a wonderful business? (ROIC > 15%, growing FCF)
  - Do I understand it? (Predictable earnings)
  - Is management trustworthy?
  - Is the price right? (Margin of safety)

- Tone: Skeptical, folksy wisdom, cite specific numbers, be direct about risks

**ANALYSIS_USER_PROMPT_TEMPLATE:**
- Company name and ticker
- 10-year revenue & profitability table
- Free cash flow history
- ROIC trend
- Debt & health scores (Z-Score, F-Score)
- Valuation metrics (price, DCF, Graham, margin of safety)
- Moat analysis

### 4. Response Parsing
Ensure the AI output is valid JSON with this structure:

```json
{
    "verdict": "BUY" | "HOLD" | "SELL",
    "confidence": 0-100,
    "summary": "<1-2 sentence Buffett-style summary>",
    "pros": ["<strength 1>", "<strength 2>", ...],
    "cons": ["<concern 1>", "<concern 2>", ...],
    "detailed_analysis": "<3-4 paragraph deep analysis>",
    "key_metrics_cited": ["ROIC: 18%", "Debt/Equity: 0.3", ...],
    "would_buffett_buy": true | false,
    "price_to_consider": <fair entry price or null>
}
```

Implement fallback parsing if JSON mode fails.

---

## Directory Structure to Create

```
backend/app/ai/
├── __init__.py
├── data_aggregator.py   # summarize_for_ai() function
├── gemini_client.py     # GeminiAnalyzer class
├── prompts.py           # System and user prompt templates
└── schemas.py           # AIAnalysisResult Pydantic model
```

---

## Critical Constraint

**The AI must explicitly cite specific numbers from the data in its analysis.**

Examples of good citations:
- "The ROIC dropped to 8% in 2023, below my 15% threshold for a wide moat."
- "With a P/E of 45 and growth of only 12%, this PEG of 3.75 is far too expensive."
- "The Altman Z-Score of 1.2 puts this company in the distress zone."

The analysis should feel like Warren Buffett actually read the financial statements.

---

## API Integration

Create endpoint in `backend/app/api/v1/ai_analysis.py`:
- `GET /api/v1/companies/{ticker}/ai-analysis` - Get latest cached analysis
- `POST /api/v1/companies/{ticker}/ai-analysis` - Trigger new analysis (regenerate)

Cache analyses in `ai_analyses` table to avoid repeated API calls.

---

## Expected Output

- Working AI analysis for any tracked stock
- Responses feel authentically like Warren Buffett's investment style
- All analyses cite specific numbers from the financial data
- JSON responses are properly validated and parsed
- Analyses are cached to minimize Gemini API costs
