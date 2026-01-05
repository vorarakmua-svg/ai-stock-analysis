# Role: Quantitative Finance Developer

**Mission:** Build the Valuation Engine for "ValueInvestAI".

---

## Context

We need to value stocks using specific financial formulas. This is pure mathematical logic - you do NOT need to touch the database or API. Focus on clean, testable Python code.

**Reference Document:** Use `PROJECT_BLUEPRINT.md` (Section 6: Financial Modeling Engine).

---

## Tasks

### 1. DCF Calculator
Create `backend/app/financial_models/dcf.py`:

**Implement a 2-stage DCF model:**
- **Stage 1:** Growth period (default 10 years) with declining growth rate
- **Stage 2:** Terminal value using Gordon Growth Model

**Input:**
- `current_fcf` - Most recent Free Cash Flow (TTM)
- `shares_outstanding` - Current diluted shares
- `current_price` - Current stock price
- `net_debt` - Total debt minus cash

**Output (DCFResult dataclass):**
- `intrinsic_value_per_share`
- `intrinsic_value_with_margin` (after 25% margin of safety)
- `upside_percentage`
- `is_undervalued` (boolean)
- `projected_fcf` (list of projected cash flows)
- `terminal_value`
- `assumptions` (DCFAssumptions dataclass)

**Also implement:**
- `auto_estimate_growth_rate()` - Estimate from historical FCF/revenue using geometric mean, capped at 25%

### 2. Moat Analyzer
Create `backend/app/financial_models/moat_analysis.py`:

**Calculate ROIC (Return on Invested Capital) for the last 10 years:**
```
ROIC = NOPAT / Invested Capital
Where:
- NOPAT = Operating Income * (1 - Tax Rate)
- Invested Capital = Total Equity + Total Debt - Cash
```

**Determine Moat Rating:**
- **Wide:** ROIC avg >= 15% AND 8+ years above cost of capital (10%)
- **Narrow:** ROIC avg >= 10% AND 6+ years above cost of capital
- **None:** Otherwise

**Output (MoatMetrics dataclass):**
- `roic_values` (list of percentages)
- `roic_average`
- `roic_trend` ("Improving", "Stable", "Declining")
- `roic_consistency` (standard deviation)
- `moat_rating` (MoatRating enum)
- `competitive_advantage_period` (years above hurdle rate)

### 3. Financial Health Analyzer
Create `backend/app/financial_models/financial_health.py`:

**Altman Z-Score (bankruptcy prediction):**
```
Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5

X1 = Working Capital / Total Assets
X2 = Retained Earnings / Total Assets
X3 = EBIT / Total Assets
X4 = Market Cap / Total Liabilities
X5 = Revenue / Total Assets

Interpretation:
- Z > 2.99: "Safe"
- 1.81 <= Z <= 2.99: "Grey Zone"
- Z < 1.81: "Distress"
```

**Piotroski F-Score (financial strength 0-9):**

Profitability (4 points):
1. Positive Net Income
2. Positive Operating Cash Flow
3. ROA improving vs prior year
4. OCF > Net Income (quality of earnings)

Leverage/Liquidity (3 points):
5. Long-term debt decreasing
6. Current ratio improving
7. No new share issuance (dilution)

Operating Efficiency (2 points):
8. Gross margin improving
9. Asset turnover improving

**Rating:**
- F-Score >= 7: "Strong"
- F-Score 4-6: "Moderate"
- F-Score < 4: "Weak"

### 4. Classic Valuations
Create `backend/app/financial_models/classic_valuations.py`:

**Graham Number:**
```
Graham Number = sqrt(22.5 * EPS * Book Value Per Share)
```
This represents max price a defensive investor should pay (P/E 15, P/B 1.5).

**Peter Lynch Fair Value:**
```
PEG = P/E / (Growth Rate + Dividend Yield)
Fair Value = EPS * (Growth Rate % + Dividend Yield %)

Rating:
- PEG < 1: "Undervalued"
- PEG 1-1.5: "Fair"
- PEG > 1.5: "Overvalued"
```

### 5. Testing
Create `backend/tests/test_financial_models/`:
- `test_dcf.py` - Test DCF calculations with known inputs
- `test_moat.py` - Test ROIC and moat rating logic
- `test_health.py` - Test Z-Score and F-Score calculations
- `test_classic.py` - Test Graham and Lynch formulas

Use pytest with dummy data. Ensure all edge cases are covered.

---

## Directory Structure to Create

```
backend/app/financial_models/
├── __init__.py
├── dcf.py              # DCF Calculator
├── moat_analysis.py    # ROIC and moat rating
├── financial_health.py # Z-Score and F-Score
└── classic_valuations.py # Graham and Lynch

backend/tests/test_financial_models/
├── __init__.py
├── test_dcf.py
├── test_moat.py
├── test_health.py
└── test_classic.py
```

---

## Edge Case Handling Constraint

**Critical:** Your code must handle edge cases without crashing:
- Negative earnings (EPS < 0)
- Zero or negative equity
- Missing data (None values)
- Division by zero scenarios
- Negative free cash flow
- Extremely high growth rates (cap at reasonable limits)

Return sensible defaults or special result objects when calculations cannot be performed.

---

## Expected Output

- All financial models as pure Python classes/functions
- No database or API dependencies
- 100% unit test coverage for core formulas
- Clear documentation in docstrings
- Type hints throughout
