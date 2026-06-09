from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Market = Literal["sh", "sz", "bj", "hk", "us"]


@dataclass(frozen=True, slots=True)
class Ticker:
    code: str
    suffix: str

    _PATTERNS = {
        "sh": re.compile(r"^\d{6}\.SH$"),
        "sz": re.compile(r"^\d{6}\.SZ$"),
        "bj": re.compile(r"^\d{6}\.BJ$"),
        "hk": re.compile(r"^\d{4}\.HK$"),
        "us": re.compile(r"^[A-Z]{1,5}\.US$"),
    }

    def __post_init__(self) -> None:
        normalized = f"{self.code}.{self.suffix.upper()}"
        if not any(p.match(normalized) for p in self._PATTERNS.values()):
            raise ValueError(f"Invalid ticker format: {normalized}")

    @property
    def symbol(self) -> str:
        return f"{self.code}.{self.suffix.upper()}"

    @property
    def market(self) -> Market:
        su = self.suffix.upper()
        if su == "SH":
            return "sh"
        if su == "SZ":
            return "sz"
        if su == "BJ":
            return "bj"
        if su == "HK":
            return "hk"
        return "us"

    @classmethod
    def from_string(cls, value: str) -> "Ticker":
        value = value.strip().upper()
        if "." not in value:
            raise ValueError(f"Ticker must contain suffix: {value}")
        code, suffix = value.rsplit(".", 1)
        return cls(code=code, suffix=suffix)

    def supports_tech_indicators(self) -> bool:
        if self.market != "sh" and self.market != "sz":
            return False
        if self.code.startswith("688"):
            return False
        if self.code.startswith("689"):
            return False
        return True

    def supports_announcements(self) -> bool:
        return self.market in ("sh", "sz", "bj")
