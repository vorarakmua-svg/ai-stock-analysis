"""Version-controlled data pipeline for ai-stock-analysis.

Produces the per-stock JSON files the backend consumes, from SEC EDGAR
(fundamentals) and yfinance (market data). Replaces the previous off-repo
collection process so data refresh is reproducible, validated, and observable.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
