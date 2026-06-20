"""Ingestion configuration (paths, SEC fair-access settings)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Repo root = two levels up from this file (ingestion/ingestion/config.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class IngestionConfig:
    """Runtime configuration for a pipeline run."""

    # SEC requires a descriptive User-Agent (it rejects requests without one).
    sec_user_agent: str = field(
        default_factory=lambda: os.environ.get(
            "INGESTION_SEC_USER_AGENT",
            os.environ.get("SEC_USER_AGENT", ""),
        )
    )
    sec_base_url: str = "https://data.sec.gov"
    # SEC publishes a ~10 req/s fair-access limit; stay comfortably under it.
    sec_max_requests_per_second: float = 8.0
    request_timeout_seconds: float = 30.0

    output_dir: Path = field(default_factory=lambda: _REPO_ROOT / "data" / "output")
    cik_map_path: Path = field(
        default_factory=lambda: _REPO_ROOT / "data" / "cache" / "company_tickers.json"
    )

    @property
    def json_dir(self) -> Path:
        return self.output_dir / "json"

    @property
    def csv_path(self) -> Path:
        return self.output_dir / "csv" / "summary.csv"

    @property
    def manifest_path(self) -> Path:
        return self.output_dir / "_manifest.json"

    def require_sec_user_agent(self) -> str:
        """Return the SEC User-Agent or fail fast with guidance."""
        if not self.sec_user_agent:
            raise ValueError(
                "SEC requires a descriptive User-Agent. Set INGESTION_SEC_USER_AGENT, "
                'e.g. "Intelligent Investor Pro contact@example.com".'
            )
        return self.sec_user_agent
