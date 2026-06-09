from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class Announcement:
    ticker: str
    seq: str
    title: str
    publish_time: Optional[datetime]
    pdf_url: Optional[str]
