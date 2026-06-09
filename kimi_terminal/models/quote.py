from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class RealtimeQuote:
    ticker: str
    name: str
    price: Optional[float]
    change: Optional[float]
    change_pct: Optional[float]
    volume: Optional[float]
    amount: Optional[float]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    prev_close: Optional[float]
    updated_at: Optional[datetime] = None


@dataclass(frozen=True, slots=True)
class TechIndicator:
    ticker: str
    name: str
    value: Optional[float]
