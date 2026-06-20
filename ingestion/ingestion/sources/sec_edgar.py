"""SEC EDGAR companyfacts client + annual-financials parser.

Respects SEC fair-access rules: a descriptive User-Agent and a request rate cap.
The parser maps XBRL us-gaap concepts to the human-readable field names the
backend expects in financials_annual.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# us-gaap concept -> human-readable field name. Lists are tried in order; the
# first concept present for a given fiscal year wins (handles taxonomy changes).
CONCEPT_MAP: dict[str, list[str]] = {
    "Total Revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "Gross Profit": ["GrossProfit"],
    "Operating Income": ["OperatingIncomeLoss"],
    "Net Income": ["NetIncomeLoss"],
    "EPS Basic": ["EarningsPerShareBasic"],
    "EPS Diluted": ["EarningsPerShareDiluted"],
    "Operating Cash Flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "Investing Cash Flow": ["NetCashProvidedByUsedInInvestingActivities"],
    "Financing Cash Flow": ["NetCashProvidedByUsedInFinancingActivities"],
    "Capital Expenditures": ["PaymentsToAcquirePropertyPlantAndEquipment"],
    "Total Assets": ["Assets"],
    "Current Assets": ["AssetsCurrent"],
    "Total Liabilities": ["Liabilities"],
    "Current Liabilities": ["LiabilitiesCurrent"],
    "Total Stockholders Equity": ["StockholdersEquity"],
    "Long-Term Debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "Cash and Cash Equivalents": ["CashAndCashEquivalentsAtCarryingValue"],
    "Stock Repurchases": ["PaymentsForRepurchaseOfCommonStock"],
    "Dividends Paid": ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"],
    "R&D Expense": ["ResearchAndDevelopmentExpense"],
    "SG&A Expense": ["SellingGeneralAndAdministrativeExpense"],
    "Depreciation": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
    ],
    "Stock-Based Compensation": ["ShareBasedCompensation"],
    "Weighted Avg Shares Diluted": ["WeightedAverageNumberOfDilutedSharesOutstanding"],
}


class SECEdgarClient:
    """Async client for SEC's companyfacts API with rate limiting."""

    def __init__(
        self,
        user_agent: str,
        *,
        base_url: str = "https://data.sec.gov",
        max_requests_per_second: float = 8.0,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not user_agent:
            raise ValueError("SEC requires a descriptive User-Agent")
        self._ua = user_agent
        self._base_url = base_url.rstrip("/")
        self._min_interval = 1.0 / max_requests_per_second if max_requests_per_second else 0.0
        self._timeout = timeout
        self._external_client = client
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def _throttle(self) -> None:
        async with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()

    async def get_company_facts(self, cik: str) -> dict[str, Any]:
        """Fetch the raw companyfacts document for a zero-padded CIK."""
        url = f"{self._base_url}/api/xbrl/companyfacts/CIK{cik}.json"
        headers = {"User-Agent": self._ua}
        await self._throttle()

        if self._external_client is not None:
            resp = await self._external_client.get(url, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def parse_annual_financials(facts: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map a companyfacts document to {fiscal_year: {field: value, ...}}.

    Only annual (10-K, fp=FY) figures are kept. For each human-readable field the
    first matching concept that has data for a given year is used.
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    by_year: dict[str, dict[str, Any]] = {}

    for field_name, concepts in CONCEPT_MAP.items():
        for concept in concepts:
            node = us_gaap.get(concept)
            if not node:
                continue
            year_values = _annual_values_for_concept(node)
            if not year_values:
                continue
            for year, value in year_values.items():
                bucket = by_year.setdefault(year, {})
                bucket.setdefault("fiscal_year", int(year))
                # Don't overwrite a value already set by an earlier concept.
                bucket.setdefault(field_name, value)
            break  # first concept with any data wins for this field

    return dict(sorted(by_year.items(), reverse=True))


def _annual_values_for_concept(node: dict[str, Any]) -> dict[str, float]:
    """Extract {fiscal_year: value} for annual 10-K facts from a concept node."""
    units = node.get("units", {})
    # Pick the relevant unit: monetary (USD), per-share (USD/shares), or shares.
    unit_key = next(
        (k for k in ("USD", "USD/shares", "shares") if k in units),
        next(iter(units), None),
    )
    if unit_key is None:
        return {}

    result: dict[str, float] = {}
    for entry in units[unit_key]:
        form = str(entry.get("form", ""))
        if not form.startswith("10-K"):
            continue
        if entry.get("fp") != "FY":
            continue
        fy = entry.get("fy")
        val = entry.get("val")
        if fy is None or val is None:
            continue
        # Latest-filed value for a fiscal year wins (restatements).
        result[str(fy)] = val
    return result
