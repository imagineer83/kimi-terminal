from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class FinancialStatement:
    ticker: str
    report_date: str
    statement_type: str
    rows: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class FinancialIndex:
    ticker: str
    report_date: str
    category: str
    indicators: list[dict[str, Any]]
