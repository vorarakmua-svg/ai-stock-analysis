"""Ticker universe and ticker -> CIK resolution (from SEC's company_tickers map)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# The default coverage universe (committed source of truth). Extend as needed.
DEFAULT_UNIVERSE: list[str] = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "NVDA",
    "TSLA",
    "JPM",
    "V",
    "JNJ",
    "WMT",
    "PG",
    "XOM",
    "KO",
    "PEP",
]


@lru_cache(maxsize=1)
def _load_cik_index(cik_map_path: str) -> dict[str, str]:
    """Build a ticker -> zero-padded 10-digit CIK index from SEC's map file."""
    raw = json.loads(Path(cik_map_path).read_text(encoding="utf-8"))
    index: dict[str, str] = {}
    # SEC format: {"0": {"cik_str": 320193, "ticker": "AAPL", ...}, ...}
    for entry in raw.values():
        ticker = str(entry.get("ticker", "")).upper().strip()
        cik = entry.get("cik_str")
        if ticker and cik is not None:
            index[ticker] = f"{int(cik):010d}"
    return index


def resolve_cik(ticker: str, cik_map_path: str | Path) -> str:
    """Return the zero-padded CIK for a ticker, or raise KeyError."""
    index = _load_cik_index(str(cik_map_path))
    key = ticker.upper().strip()
    if key not in index:
        raise KeyError(f"No CIK found for ticker {key!r} in {cik_map_path}")
    return index[key]
