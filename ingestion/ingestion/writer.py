"""Atomic, idempotent writers for per-stock JSON, summary CSV, and run manifest."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

# Fields excluded when comparing for idempotency (they change every run).
_VOLATILE_KEYS = {"collected_at"}


def _stable_payload(data: dict[str, Any]) -> str:
    """Serialize a copy without volatile keys, for change detection."""
    comparable = {k: v for k, v in data.items() if k not in _VOLATILE_KEYS}
    return json.dumps(comparable, sort_keys=True, ensure_ascii=False)


def write_stock_json(data: dict[str, Any], json_dir: Path) -> str:
    """Write {TICKER}.json atomically; skip if unchanged. Returns the status.

    Returns "unchanged" when an existing file has identical content (ignoring
    collected_at), else "written".
    """
    json_dir.mkdir(parents=True, exist_ok=True)
    target = json_dir / f"{data['ticker']}.json"

    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
            if _stable_payload(existing) == _stable_payload(data):
                return "unchanged"
        except (json.JSONDecodeError, OSError):
            pass  # corrupt/unreadable -> overwrite

    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, target)  # atomic on the same filesystem
    return "written"


def build_summary_row(data: dict[str, Any]) -> dict[str, Any]:
    """Project a stock data dict to a flat summary.csv row."""
    ci = data.get("company_info", {})
    md = data.get("market_data", {})
    return {
        "ticker": data.get("ticker"),
        "company_name": data.get("company_name"),
        "sector": ci.get("sector"),
        "industry": ci.get("industry"),
        "current_price": md.get("current_price"),
        "market_cap": md.get("market_cap"),
        "beta": md.get("beta"),
    }


def write_summary_csv(rows: list[dict[str, Any]], csv_path: Path) -> None:
    """Write all summary rows (sorted by ticker) to summary.csv atomically."""
    if not rows:
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    rows = sorted(rows, key=lambda r: str(r.get("ticker", "")))

    tmp = csv_path.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, csv_path)


def write_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    """Write the run manifest atomically."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = manifest_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, manifest_path)
