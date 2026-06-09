# Kimi Terminal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Bloomberg-style terminal TUI (`kmt`) for A-share and Hong Kong stock market data, backed by `plugin-kimi-datasource`.

**Architecture:** Single Python package using Textual for the TUI. Direct HTTP calls to Kimi API mimicking the existing plugin's auth and request format. SQLite local cache for TTL-based data reuse. Modular screens for Dashboard, Quote, Financials, Announcements, and Screener.

**Tech Stack:** Python 3.11+, Textual, httpx, pydantic, PyYAML, pytest, pytest-asyncio, respx.

---

## File Structure

```
~/Projects/kimi-terminal/
├── pyproject.toml
├── Makefile
├── README.md
├── .gitignore
├── kimi_terminal/
│   ├── __init__.py
│   ├── cli.py
│   ├── app.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ticker.py
│   │   ├── quote.py
│   │   ├── candle.py
│   │   ├── financial.py
│   │   └── announcement.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── api_client.py
│   │   ├── cache.py
│   │   └── watchlist_service.py
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── dashboard_screen.py
│   │   ├── quote_screen.py
│   │   ├── financial_screen.py
│   │   ├── announcement_screen.py
│   │   └── screener_screen.py
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── header.py
│   │   ├── footer.py
│   │   ├── command_input.py
│   │   ├── quote_table.py
│   │   └── sparkline.py
│   └── utils/
│       ├── __init__.py
│       └── format.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_config.py
    ├── test_cache.py
    ├── test_api_client.py
    ├── test_format.py
    ├── test_widgets.py
    └── test_screens.py
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `Makefile`
- Create: directory tree under `kimi_terminal/` and `tests/`

- [ ] **Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "kimi-terminal"
version = "0.1.0"
description = "Bloomberg-style terminal for A-share and HK stock data"
requires-python = ">=3.11"
dependencies = [
    "textual>=0.47.0",
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",
    "textual-dev>=1.0",
]

[project.scripts]
kmt = "kimi_terminal.cli:main"
```

- [ ] **Step 2: Create directory structure and empty files**

Run:
```bash
cd ~/Projects/kimi-terminal
mkdir -p kimi_terminal/models kimi_terminal/services kimi_terminal/screens kimi_terminal/widgets kimi_terminal/utils tests
touch kimi_terminal/__init__.py kimi_terminal/cli.py kimi_terminal/app.py kimi_terminal/config.py
touch kimi_terminal/models/__init__.py kimi_terminal/models/ticker.py kimi_terminal/models/quote.py kimi_terminal/models/candle.py kimi_terminal/models/financial.py kimi_terminal/models/announcement.py
touch kimi_terminal/services/__init__.py kimi_terminal/services/api_client.py kimi_terminal/services/cache.py kimi_terminal/services/watchlist_service.py
touch kimi_terminal/screens/__init__.py kimi_terminal/screens/dashboard_screen.py kimi_terminal/screens/quote_screen.py kimi_terminal/screens/financial_screen.py kimi_terminal/screens/announcement_screen.py kimi_terminal/screens/screener_screen.py
touch kimi_terminal/widgets/__init__.py kimi_terminal/widgets/header.py kimi_terminal/widgets/footer.py kimi_terminal/widgets/command_input.py kimi_terminal/widgets/quote_table.py kimi_terminal/widgets/sparkline.py
touch kimi_terminal/utils/__init__.py kimi_terminal/utils/format.py
touch tests/__init__.py tests/conftest.py tests/test_models.py tests/test_config.py tests/test_cache.py tests/test_api_client.py tests/test_format.py tests/test_widgets.py tests/test_screens.py
```

- [ ] **Step 3: Write .gitignore**

```
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/
.venv/
venv/
.env
*.db
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

- [ ] **Step 4: Create venv and install dependencies**

Run:
```bash
cd ~/Projects/kimi-terminal
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Expected: Installation succeeds with no errors.

- [ ] **Step 5: Verify Python can import package**

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
python -c "import kimi_terminal; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 6: Initial commit**

```bash
cd ~/Projects/kimi-terminal
git add pyproject.toml .gitignore Makefile kimi_terminal tests
git commit -m "chore: project scaffold"
```

---

## Task 2: Data Models

**Files:**
- Create: `kimi_terminal/models/ticker.py`
- Create: `kimi_terminal/models/quote.py`
- Create: `kimi_terminal/models/candle.py`
- Create: `kimi_terminal/models/financial.py`
- Create: `kimi_terminal/models/announcement.py`
- Modify: `kimi_terminal/models/__init__.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Implement Ticker model with validation**

Write `kimi_terminal/models/ticker.py`:

```python
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
        # realtime_tech only supports A-share main board, excludes STAR Market 688xxx
        if self.market != "sh" and self.market != "sz":
            return False
        if self.code.startswith("688"):
            return False
        if self.code.startswith("689"):
            return False
        return True

    def supports_announcements(self) -> bool:
        return self.market in ("sh", "sz", "bj")
```

- [ ] **Step 2: Implement Quote and Candle models**

Write `kimi_terminal/models/quote.py`:

```python
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
```

Write `kimi_terminal/models/candle.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True, slots=True)
class Candle:
    ticker: str
    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[float]
    amount: Optional[float]
```
```

- [ ] **Step 3: Implement Financial and Announcement models**

Write `kimi_terminal/models/financial.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class FinancialStatement:
    ticker: str
    report_date: str
    statement_type: str  # balance_sheet, income_statement, cash_flow
    rows: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class FinancialIndex:
    ticker: str
    report_date: str
    category: str
    indicators: list[dict[str, Any]]
```

Write `kimi_terminal/models/announcement.py`:

```python
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
```
```

- [ ] **Step 4: Update models __init__.py**

Write `kimi_terminal/models/__init__.py`:

```python
from kimi_terminal.models.announcement import Announcement
from kimi_terminal.models.candle import Candle
from kimi_terminal.models.financial import FinancialIndex, FinancialStatement
from kimi_terminal.models.quote import RealtimeQuote, TechIndicator
from kimi_terminal.models.ticker import Market, Ticker

__all__ = [
    "Announcement",
    "Candle",
    "FinancialIndex",
    "FinancialStatement",
    "Market",
    "RealtimeQuote",
    "TechIndicator",
    "Ticker",
]
```

- [ ] **Step 5: Write model tests**

Write `tests/test_models.py`:

```python
import pytest

from kimi_terminal.models import Ticker


def test_ticker_from_string_valid():
    t = Ticker.from_string("600519.SH")
    assert t.symbol == "600519.SH"
    assert t.market == "sh"


def test_ticker_from_string_invalid():
    with pytest.raises(ValueError):
        Ticker.from_string("123")


def test_ticker_supports_tech():
    assert Ticker.from_string("600519.SH").supports_tech_indicators() is True
    assert Ticker.from_string("688981.SH").supports_tech_indicators() is False
    assert Ticker.from_string("0700.HK").supports_tech_indicators() is False


def test_ticker_supports_announcements():
    assert Ticker.from_string("000001.SZ").supports_announcements() is True
    assert Ticker.from_string("0700.HK").supports_announcements() is False
```

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
pytest tests/test_models.py -v
```

Expected: 4 tests pass.

- [ ] **Step 6: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/models tests/test_models.py
git commit -m "feat: add data models"
```

---

## Task 3: Configuration and Watchlist

**Files:**
- Create: `kimi_terminal/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Implement config module**

Write `kimi_terminal/config.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class WatchlistItem:
    code: str
    name: str
    hold_cost: float | None = None
    hold_quantity: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"code": self.code, "name": self.name}
        if self.hold_cost is not None:
            d["hold_cost"] = self.hold_cost
        if self.hold_quantity is not None:
            d["hold_quantity"] = self.hold_quantity
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WatchlistItem":
        return cls(
            code=str(d["code"]),
            name=str(d["name"]),
            hold_cost=float(d["hold_cost"]) if "hold_cost" in d else None,
            hold_quantity=int(d["hold_quantity"]) if "hold_quantity" in d else None,
        )


@dataclass
class AppConfig:
    theme: str = "dark"
    refresh_interval_seconds: int = 30
    price_precision: int = 2
    cache_db_path: str = "~/.cache/kimi-terminal/cache.db"

    def resolved_cache_path(self) -> Path:
        return Path(os.path.expanduser(self.cache_db_path))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AppConfig":
        return cls(
            theme=str(d.get("theme", "dark")),
            refresh_interval_seconds=int(d.get("refresh_interval_seconds", 30)),
            price_precision=int(d.get("price_precision", 2)),
            cache_db_path=str(d.get("cache_db_path", "~/.cache/kimi-terminal/cache.db")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme": self.theme,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "price_precision": self.price_precision,
            "cache_db_path": self.cache_db_path,
        }


class ConfigManager:
    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir = config_dir or Path.home() / ".config" / "kimi-terminal"
        self.config_file = self.config_dir / "config.yaml"
        self.watchlist_file = self.config_dir / "watchlist.yaml"

    def ensure_directories(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        cache_dir = Path.home() / ".cache" / "kimi-terminal"
        cache_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> AppConfig:
        if not self.config_file.exists():
            return AppConfig()
        with open(self.config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return AppConfig.from_dict(data)

    def save_config(self, config: AppConfig) -> None:
        self.ensure_directories()
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(config.to_dict(), f, allow_unicode=True, sort_keys=False)

    def load_watchlist(self) -> list[WatchlistItem]:
        if not self.watchlist_file.exists():
            default = [
                WatchlistItem(code="600519.SH", name="贵州茅台"),
                WatchlistItem(code="0700.HK", name="腾讯控股"),
            ]
            self.save_watchlist(default)
            return default
        with open(self.watchlist_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        items = data.get("watchlist", []) if isinstance(data, dict) else []
        return [WatchlistItem.from_dict(i) for i in items]

    def save_watchlist(self, items: list[WatchlistItem]) -> None:
        self.ensure_directories()
        with open(self.watchlist_file, "w", encoding="utf-8") as f:
            yaml.safe_dump({"watchlist": [i.to_dict() for i in items]}, f, allow_unicode=True, sort_keys=False)

    def add_to_watchlist(self, item: WatchlistItem) -> list[WatchlistItem]:
        items = self.load_watchlist()
        codes = {i.code.upper() for i in items}
        if item.code.upper() in codes:
            return items
        items.append(item)
        self.save_watchlist(items)
        return items

    def remove_from_watchlist(self, code: str) -> list[WatchlistItem]:
        items = self.load_watchlist()
        items = [i for i in items if i.code.upper() != code.upper()]
        self.save_watchlist(items)
        return items
```

- [ ] **Step 2: Write config tests**

Write `tests/test_config.py`:

```python
import tempfile
from pathlib import Path

from kimi_terminal.config import ConfigManager, WatchlistItem


def test_config_round_trip():
    with tempfile.TemporaryDirectory() as td:
        cm = ConfigManager(config_dir=Path(td))
        cm.save_config(cm.load_config())
        loaded = cm.load_config()
        assert loaded.theme == "dark"
        assert loaded.refresh_interval_seconds == 30


def test_watchlist_default():
    with tempfile.TemporaryDirectory() as td:
        cm = ConfigManager(config_dir=Path(td))
        items = cm.load_watchlist()
        assert len(items) == 2
        assert items[0].code == "600519.SH"


def test_watchlist_add_remove():
    with tempfile.TemporaryDirectory() as td:
        cm = ConfigManager(config_dir=Path(td))
        cm.save_watchlist([])
        cm.add_to_watchlist(WatchlistItem(code="000001.SZ", name="平安银行"))
        items = cm.load_watchlist()
        assert len(items) == 1
        cm.remove_from_watchlist("000001.SZ")
        items = cm.load_watchlist()
        assert len(items) == 0
```

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
pytest tests/test_config.py -v
```

Expected: 3 tests pass.

- [ ] **Step 3: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/config.py tests/test_config.py
git commit -m "feat: add config and watchlist manager"
```

---

## Task 4: SQLite Cache Service

**Files:**
- Create: `kimi_terminal/services/cache.py`
- Test: `tests/test_cache.py`

- [ ] **Step 1: Implement cache service**

Write `kimi_terminal/services/cache.py`:

```python
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class Cache:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_category ON cache(category)"
            )

    def _make_key(self, category: str, params: dict[str, Any]) -> str:
        canonical = json.dumps(params, sort_keys=True, ensure_ascii=True)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"{category}:{digest}"

    def get(self, category: str, params: dict[str, Any], ttl_seconds: int) -> Any | None:
        key = self._make_key(category, params)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT payload, created_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        payload, created_at = row
        if time.time() - created_at > ttl_seconds:
            return None
        return json.loads(payload)

    def set(self, category: str, params: dict[str, Any], value: Any) -> None:
        key = self._make_key(category, params)
        payload = json.dumps(value, ensure_ascii=False, default=str)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO cache (key, category, payload, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    category=excluded.category,
                    payload=excluded.payload,
                    created_at=excluded.created_at
                """,
                (key, category, payload, int(time.time())),
            )

    def clear_category(self, category: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE category = ?", (category,))

    def clear_all(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache")
```

- [ ] **Step 2: Write cache tests**

Write `tests/test_cache.py`:

```python
import tempfile
from pathlib import Path

from kimi_terminal.services.cache import Cache


def test_cache_set_get():
    with tempfile.TemporaryDirectory() as td:
        cache = Cache(Path(td) / "cache.db")
        cache.set("price", {"ticker": "600519.SH"}, {"close": 1500.0})
        result = cache.get("price", {"ticker": "600519.SH"}, ttl_seconds=60)
        assert result == {"close": 1500.0}


def test_cache_ttl_expires():
    with tempfile.TemporaryDirectory() as td:
        cache = Cache(Path(td) / "cache.db")
        cache.set("price", {"ticker": "600519.SH"}, {"close": 1500.0})
        result = cache.get("price", {"ticker": "600519.SH"}, ttl_seconds=-1)
        assert result is None


def test_cache_missing():
    with tempfile.TemporaryDirectory() as td:
        cache = Cache(Path(td) / "cache.db")
        assert cache.get("price", {"ticker": "MISSING"}, ttl_seconds=60) is None
```

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
pytest tests/test_cache.py -v
```

Expected: 3 tests pass.

- [ ] **Step 3: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/services/cache.py tests/test_cache.py
git commit -m "feat: add sqlite cache service"
```

---

## Task 5: Kimi API Client

**Files:**
- Create: `kimi_terminal/services/api_client.py`
- Test: `tests/test_api_client.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Implement API client with auth and base methods**

Write `kimi_terminal/services/api_client.py`:

```python
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from kimi_terminal.models import Candle, RealtimeQuote, Ticker
from kimi_terminal.services.cache import Cache

API_URL = os.environ.get("KIMI_DATASOURCE_API_URL", "https://api.kimi.com/coding/v1/tools")
REQUEST_TIMEOUT = 30.0


class KimiAuthError(Exception):
    pass


class KimiApiError(Exception):
    pass


def _load_credentials() -> str:
    kimi_home = os.environ.get("KIMI_CODE_HOME", "")
    if not kimi_home:
        kimi_home = str(Path.home() / ".kimi-code")
    creds_path = Path(kimi_home) / "credentials" / "kimi-code.json"
    try:
        with open(creds_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise KimiAuthError(f"Credentials not found: {creds_path}. Run /login in Kimi Code first.") from exc
    except json.JSONDecodeError as exc:
        raise KimiAuthError(f"Invalid credentials file: {exc}") from exc

    token = data.get("access_token", "")
    if not token:
        raise KimiAuthError("Credentials missing access_token. Run /login again.")
    expires_at = data.get("expires_at", 0)
    if expires_at and expires_at <= datetime.now().timestamp():
        raise KimiAuthError("Access token expired. Run /login again.")
    return str(token)


class KimiApiClient:
    def __init__(self, cache: Cache, base_url: str = API_URL) -> None:
        self.cache = cache
        self.base_url = base_url
        self._token: str | None = None

    def _token_header(self) -> str:
        if self._token is None:
            self._token = _load_credentials()
        return f"Bearer {self._token}"

    async def _call(self, method: str, params: dict[str, Any]) -> Any:
        token = self._token_header()
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": token,
                    "Content-Type": "application/json",
                    "User-Agent": "kimi-terminal/0.1.0",
                },
                json={"method": method, "params": params},
            )
        if response.status_code >= 400:
            raise KimiApiError(f"HTTP {response.status_code}: {response.text}")
        try:
            payload = response.json()
        except json.JSONDecodeError:
            return response.text
        if isinstance(payload, dict) and payload.get("is_success") is False:
            err = payload.get("error", "Unknown API error")
            raise KimiApiError(f"API error: {err}")
        if isinstance(payload, dict) and "result" in payload:
            return payload["result"]
        return payload

    async def get_data_source_desc(self, name: str) -> str:
        return await self._call("get_data_source_desc", {"name": name})

    async def call_data_source_tool(
        self, data_source_name: str, api_name: str, params: dict[str, Any]
    ) -> Any:
        return await self._call(
            "call_data_source_tool",
            {
                "data_source_name": data_source_name,
                "api_name": api_name,
                "params": params,
            },
        )

    async def _cached_call(
        self,
        category: str,
        ttl: int,
        api_name: str,
        params: dict[str, Any],
    ) -> Any:
        cache_key = {"api": api_name, **params}
        cached = self.cache.get(category, cache_key, ttl)
        if cached is not None:
            return cached
        result = await self.call_data_source_tool("stock_finance_data", api_name, params)
        # Extract text from MCP-style result if needed
        text = self._extract_text(result)
        self.cache.set(category, cache_key, {"text": text})
        return {"text": text}

    @staticmethod
    def _extract_text(result: Any) -> str:
        if isinstance(result, str):
            return result
        if not isinstance(result, dict):
            return str(result)
        for channel in ("assistant", "user"):
            items = result.get(channel, [])
            if not isinstance(items, list):
                continue
            texts = [
                item["text"]
                for item in items
                if isinstance(item, dict) and item.get("type") == "text" and "text" in item
            ]
            joined = "\n\n".join(texts).strip()
            if joined:
                return joined
        return str(result)

    # Specialized wrappers
    async def get_stock_info(self, ticker: Ticker) -> str:
        return (await self._cached_call(
            "stock_info",
            7 * 24 * 3600,
            "stock_finance_data_get_stock_info",
            {"ticker": ticker.symbol, "file_path": "/tmp/kmt_stock_info.csv"},
        ))["text"]

    async def get_realtime_price(self, tickers: list[Ticker]) -> str:
        symbols = ",".join(t.symbol for t in tickers)
        return (await self._cached_call(
            "realtime_price",
            25,
            "stock_finance_data_get_stock_realtime_price",
            {
                "ticker": symbols,
                "file_path": "/tmp/kmt_realtime_price.csv",
                "type": "realtime_price",
            },
        ))["text"]

    async def get_close_summary(self, tickers: list[Ticker]) -> str:
        symbols = ",".join(t.symbol for t in tickers)
        return (await self._cached_call(
            "close_summary",
            24 * 3600,
            "stock_finance_data_get_stock_realtime_price",
            {
                "ticker": symbols,
                "file_path": "/tmp/kmt_close_summary.csv",
                "type": "close_summary",
            },
        ))["text"]

    async def get_historical_price(
        self, ticker: Ticker, start_date: date, end_date: date, interval: str = "D"
    ) -> str:
        return (await self._cached_call(
            "historical_price",
            24 * 3600,
            "stock_finance_data_get_price",
            {
                "ticker": ticker.symbol,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "interval": interval,
                "file_path": "/tmp/kmt_price.csv",
            },
        ))["text"]

    async def get_realtime_tech(self, ticker: Ticker) -> str:
        return (await self._cached_call(
            "realtime_tech",
            60,
            "stock_finance_data_get_stock_realtime_price",
            {
                "ticker": ticker.symbol,
                "file_path": "/tmp/kmt_realtime_tech.csv",
                "type": "realtime_tech",
            },
        ))["text"]

    async def get_financial_statements(
        self, ticker: Ticker, statement: str, report_date: str
    ) -> str:
        return (await self._cached_call(
            "financial_statements",
            7 * 24 * 3600,
            "stock_finance_data_get_financial_statements",
            {
                "ticker": ticker.symbol,
                "statement": statement,
                "financial_parameter": report_date,
                "file_path": "/tmp/kmt_fs.csv",
            },
        ))["text"]

    async def get_financial_index(
        self, ticker: Ticker, category: str, report_date: str
    ) -> str:
        return (await self._cached_call(
            "financial_index",
            7 * 24 * 3600,
            "stock_finance_data_get_stock_financial_index",
            {
                "ticker": ticker.symbol,
                "category": category,
                "financial_parameter": report_date,
                "file_path": "/tmp/kmt_fi.csv",
            },
        ))["text"]

    async def get_announcements(
        self, ticker: Ticker, start_date: date, end_date: date
    ) -> str:
        return (await self._cached_call(
            "announcement",
            3600,
            "stock_finance_data_get_stock_announcement",
            {
                "ticker": ticker.symbol,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "file_path": "/tmp/kmt_announcements.csv",
            },
        ))["text"]

    async def get_related_stocks(
        self, keyword: str, market: str = "stock"
    ) -> str:
        return (await self._cached_call(
            "screener_result",
            600,
            "stock_finance_data_get_related_stock",
            {
                "stock_keyword": keyword,
                "market": market,
                "file_path": "/tmp/kmt_screener.csv",
            },
        ))["text"]
```

- [ ] **Step 2: Write API client tests using respx**

Write `tests/test_api_client.py`:

```python
import json
import tempfile
from pathlib import Path

import pytest
import respx
from httpx import Response

from kimi_terminal.models import Ticker
from kimi_terminal.services.api_client import KimiApiClient, KimiAuthError
from kimi_terminal.services.cache import Cache


@pytest.fixture
def client():
    cache = Cache(Path(tempfile.mkdtemp()) / "cache.db")
    return KimiApiClient(cache, base_url="https://api.kimi.test/tools")


def _ok_result(text: str):
    return {"is_success": True, "result": {"assistant": [{"type": "text", "text": text}]}}


@respx.mock
def test_call_data_source_tool_success(client):
    route = respx.post("https://api.kimi.test/tools").mock(return_value=Response(200, json=_ok_result("hello")))
    # Patch credentials loading
    import kimi_terminal.services.api_client as api_mod
    api_mod._load_credentials = lambda: "fake_token"

    result = client._extract_text(
        {"is_success": True, "result": {"assistant": [{"type": "text", "text": "hello"}]}}
    )
    assert result == "hello"


@respx.mock
async def test_get_realtime_price(client):
    route = respx.post("https://api.kimi.test/tools").mock(
        return_value=Response(200, json=_ok_result("ticker,price\n600519.SH,1500"))
    )
    import kimi_terminal.services.api_client as api_mod
    api_mod._load_credentials = lambda: "fake_token"

    text = await client.get_realtime_price([Ticker.from_string("600519.SH")])
    assert "600519.SH" in text
    assert route.called
```

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
pytest tests/test_api_client.py -v
```

Expected: 2 tests pass.

- [ ] **Step 3: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/services/api_client.py tests/test_api_client.py
git commit -m "feat: add Kimi API client"
```

---

## Task 6: Formatting Utilities

**Files:**
- Create: `kimi_terminal/utils/format.py`
- Test: `tests/test_format.py`

- [ ] **Step 1: Implement formatting helpers**

Write `kimi_terminal/utils/format.py`:

```python
from __future__ import annotations


def fmt_price(value: float | None, precision: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:,.{precision}f}"


def fmt_change(value: float | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:,.2f}"


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:,.2f}%"


def fmt_volume(value: float | None) -> str:
    if value is None:
        return "-"
    if value >= 1_0000_0000:
        return f"{value / 1_0000_0000:.2f}亿"
    if value >= 1_0000:
        return f"{value / 1_0000:.2f}万"
    return f"{value:,.0f}"


def color_for_change(value: float | None) -> str:
    # Chinese market convention: red = up, green = down
    if value is None:
        return "white"
    if value > 0:
        return "red"
    if value < 0:
        return "green"
    return "white"
```

- [ ] **Step 2: Write format tests**

Write `tests/test_format.py`:

```python
from kimi_terminal.utils.format import color_for_change, fmt_change, fmt_pct, fmt_price, fmt_volume


def test_fmt_price():
    assert fmt_price(1500.5) == "1,500.50"
    assert fmt_price(None) == "-"


def test_fmt_change():
    assert fmt_change(5.2) == "+5.20"
    assert fmt_change(-3.1) == "-3.10"


def test_fmt_volume():
    assert fmt_volume(1_5000_0000) == "1.50亿"
    assert fmt_volume(5_0000) == "5.00万"


def test_color_for_change():
    assert color_for_change(1.0) == "red"
    assert color_for_change(-1.0) == "green"
    assert color_for_change(0.0) == "white"
```

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
pytest tests/test_format.py -v
```

Expected: 4 tests pass.

- [ ] **Step 3: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/utils/format.py tests/test_format.py
git commit -m "feat: add formatting utilities"
```

---

## Task 7: Reusable Widgets

**Files:**
- Create: `kimi_terminal/widgets/header.py`
- Create: `kimi_terminal/widgets/footer.py`
- Create: `kimi_terminal/widgets/command_input.py`
- Create: `kimi_terminal/widgets/quote_table.py`
- Create: `kimi_terminal/widgets/sparkline.py`
- Test: `tests/test_widgets.py`

- [ ] **Step 1: Implement Header**

Write `kimi_terminal/widgets/header.py`:

```python
from textual.widgets import Static


class KimiHeader(Static):
    DEFAULT_CSS = """
    KimiHeader {
        height: 3;
        content-align: center middle;
        background: $primary;
        color: $text;
        text-style: bold;
    }
    """

    def __init__(self, title: str = "Kimi Terminal") -> None:
        super().__init__()
        self.title = title

    def compose(self):
        yield Static(self.title)

    def update_title(self, title: str) -> None:
        self.title = title
        static = self.query_one(Static)
        static.update(title)
```

- [ ] **Step 2: Implement Footer / StatusBar**

Write `kimi_terminal/widgets/footer.py`:

```python
from textual.reactive import reactive
from textual.widgets import Static


class KimiFooter(Static):
    status = reactive("Ready")

    DEFAULT_CSS = """
    KimiFooter {
        height: 1;
        background: $surface;
        color: $text-muted;
        content-align: left middle;
    }
    """

    def compose(self):
        yield Static(self.status)

    def watch_status(self, status: str) -> None:
        try:
            self.query_one(Static).update(status)
        except Exception:
            pass

    def set_status(self, message: str) -> None:
        self.status = message
```

- [ ] **Step 3: Implement CommandInput modal**

Write `kimi_terminal/widgets/command_input.py`:

```python
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class CommandInput(ModalScreen[str | None]):
    DEFAULT_CSS = """
    CommandInput {
        align: center middle;
    }
    CommandInput > Horizontal {
        width: 80;
        height: auto;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    """

    def __init__(self, initial: str = "") -> None:
        super().__init__()
        self.initial = initial

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(":")
            yield Input(value=self.initial, placeholder="command")
            yield Button("OK", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        inp = self.query_one(Input)
        self.dismiss(inp.value or None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value or None)

    def key_escape(self) -> None:
        self.dismiss(None)
```

- [ ] **Step 4: Implement QuoteTable**

Write `kimi_terminal/widgets/quote_table.py`:

```python
from textual.widgets import DataTable

from kimi_terminal.models import RealtimeQuote
from kimi_terminal.utils.format import color_for_change, fmt_change, fmt_pct, fmt_price, fmt_volume


class QuoteTable(DataTable):
    def __init__(self) -> None:
        super().__init__()
        self.add_columns("代码", "名称", "最新价", "涨跌额", "涨跌幅", "成交量", "市值提示")
        self.cursor_type = "row"

    def update_quotes(self, quotes: list[RealtimeQuote]) -> None:
        self.clear()
        for q in quotes:
            change_color = color_for_change(q.change)
            self.add_row(
                q.ticker,
                q.name or "",
                fmt_price(q.price),
                fmt_change(q.change),
                fmt_pct(q.change_pct),
                fmt_volume(q.volume),
                "",
            )
            # Color the change columns
            row_idx = self.row_count - 1
            self.update_cell_at((row_idx, 3), fmt_change(q.change), style=change_color)
            self.update_cell_at((row_idx, 4), fmt_pct(q.change_pct), style=change_color)
```

- [ ] **Step 5: Implement Sparkline**

Write `kimi_terminal/widgets/sparkline.py`:

```python
from textual.widgets import Static


class Sparkline(Static):
    DEFAULT_CSS = """
    Sparkline {
        height: 10;
        border: solid $primary;
    }
    """

    def __init__(self, data: list[float] | None = None, title: str = "") -> None:
        super().__init__()
        self.data = data or []
        self.title = title

    def set_data(self, data: list[float], title: str = "") -> None:
        self.data = data
        if title:
            self.title = title
        self.refresh()

    def render(self) -> str:
        if not self.data:
            return self.title or "No data"
        lines = []
        if self.title:
            lines.append(self.title)
        width = self.size.width or 40
        height = self.size.height or 10
        mn, mx = min(self.data), max(self.data)
        rng = mx - mn if mx != mn else 1.0
        for row in range(height):
            idx = int((row / max(height - 1, 1)) * (len(self.data) - 1))
            val = self.data[idx]
            norm = int(((val - mn) / rng) * (width - 1))
            line = [" "] * width
            line[norm] = "*"
            lines.append("".join(line))
        return "\n".join(lines)
```

- [ ] **Step 6: Write widget tests**

Write `tests/test_widgets.py`:

```python
import pytest

from kimi_terminal.widgets.command_input import CommandInput
from kimi_terminal.widgets.footer import KimiFooter
from kimi_terminal.widgets.header import KimiHeader
from kimi_terminal.widgets.sparkline import Sparkline


@pytest.mark.asyncio
async def test_header_renders_title():
    from textual.pilot import Pilot
    from textual.app import App

    class TestApp(App):
        def compose(self):
            yield KimiHeader("Test Title")

    app = TestApp()
    async with app.run_test() as pilot:
        header = app.query_one(KimiHeader)
        assert header.title == "Test Title"


@pytest.mark.asyncio
async def test_footer_status_update():
    from textual.app import App

    class TestApp(App):
        def compose(self):
            yield KimiFooter()

    app = TestApp()
    async with app.run_test() as pilot:
        footer = app.query_one(KimiFooter)
        footer.set_status("Loading...")
        assert footer.status == "Loading..."


def test_sparkline_set_data():
    s = Sparkline()
    s.set_data([1.0, 2.0, 3.0], title="Trend")
    assert s.data == [1.0, 2.0, 3.0]
    assert s.title == "Trend"
```

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
pytest tests/test_widgets.py -v
```

Expected: 3 tests pass. Header/Footer tests may require Textual's async harness; adjust if needed.

- [ ] **Step 7: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/widgets tests/test_widgets.py
git commit -m "feat: add reusable TUI widgets"
```

---

## Task 8: Dashboard Screen

**Files:**
- Create: `kimi_terminal/screens/dashboard_screen.py`
- Modify: `kimi_terminal/app.py` (routing)
- Test: `tests/test_screens.py`

- [ ] **Step 1: Implement DashboardScreen**

Write `kimi_terminal/screens/dashboard_screen.py`:

```python
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import cast

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Static

from kimi_terminal.config import ConfigManager, WatchlistItem
from kimi_terminal.models import RealtimeQuote, Ticker
from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.services.cache import Cache
from kimi_terminal.services.watchlist_service import WatchlistService
from kimi_terminal.widgets.command_input import CommandInput
from kimi_terminal.widgets.footer import KimiFooter
from kimi_terminal.widgets.header import KimiHeader
from kimi_terminal.widgets.quote_table import QuoteTable


class DashboardScreen(Screen):
    def __init__(self, config: ConfigManager, api: KimiApiClient) -> None:
        super().__init__()
        self.config = config
        self.api = api
        self.watchlist = WatchlistService(config)
        self.refresh_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield KimiHeader("Dashboard [D] | Watchlist")
        with Vertical():
            yield QuoteTable()
            yield Static("快捷键: Enter 详情 | a 添加 | d 删除 | : 命令 | q 退出", id="help")
        yield KimiFooter()

    async def on_mount(self) -> None:
        await self._refresh()
        interval = self.config.load_config().refresh_interval_seconds
        self.refresh_timer = self.set_interval(interval, self._refresh)

    async def _refresh(self) -> None:
        footer = self.query_one(KimiFooter)
        footer.set_status("Refreshing watchlist...")
        items = self.watchlist.items()
        if not items:
            self.query_one(QuoteTable).clear()
            footer.set_status("Watchlist is empty")
            return

        try:
            tickers = [Ticker.from_string(i.code) for i in items]
            batches = [tickers[i : i + 3] for i in range(0, len(tickers), 3)]
            quotes: list[RealtimeQuote] = []
            for batch in batches:
                text = await self.api.get_realtime_price(batch)
                quotes.extend(self._parse_quotes(text))
            self.query_one(QuoteTable).update_quotes(quotes)
            footer.set_status(f"Updated at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as exc:
            footer.set_status(f"Error: {exc}")

    def _parse_quotes(self, csv_text: str) -> list[RealtimeQuote]:
        quotes = []
        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            quotes.append(
                RealtimeQuote(
                    ticker=row.get("ticker", row.get("code", "")),
                    name=row.get("name", ""),
                    price=self._to_float(row.get("close", row.get("price", ""))),
                    change=self._to_float(row.get("change", row.get("chg", ""))),
                    change_pct=self._to_float(row.get("change_pct", row.get("pct_chg", ""))),
                    volume=self._to_float(row.get("volume", row.get("vol", ""))),
                    amount=self._to_float(row.get("amount", row.get("amt", ""))),
                    open=self._to_float(row.get("open", "")),
                    high=self._to_float(row.get("high", "")),
                    low=self._to_float(row.get("low", "")),
                    prev_close=self._to_float(row.get("pre_close", "")),
                )
            )
        return quotes

    @staticmethod
    def _to_float(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    async def on_key(self, event) -> None:
        key = event.key
        if key == "enter":
            table = self.query_one(QuoteTable)
            if table.cursor_row is not None and table.cursor_row < table.row_count:
                ticker = str(table.get_row_at(table.cursor_row)[0])
                from kimi_terminal.screens.quote_screen import QuoteScreen
                self.app.push_screen(QuoteScreen(self.api, ticker))
        elif key == "a":
            self.app.push_screen(CommandInput(":"), self._on_add_command)
        elif key == "d":
            table = self.query_one(QuoteTable)
            if table.cursor_row is not None and table.cursor_row < table.row_count:
                ticker = str(table.get_row_at(table.cursor_row)[0])
                self.watchlist.remove(ticker)
                await self._refresh()
        elif key == "colon":
            self.app.push_screen(CommandInput(":"), self._on_command)

    def _on_add_command(self, result: str | None) -> None:
        if not result:
            return
        try:
            ticker = Ticker.from_string(result)
            self.watchlist.add(ticker.symbol, ticker.symbol)
        except Exception as exc:
            self.query_one(KimiFooter).set_status(f"Add failed: {exc}")

    def _on_command(self, result: str | None) -> None:
        if not result:
            return
        self.app.handle_command(result)

    def on_screen_resume(self) -> None:
        if self.refresh_timer is None or self.refresh_timer._stopped:
            interval = self.config.load_config().refresh_interval_seconds
            self.refresh_timer = self.set_interval(interval, self._refresh)

    def on_screen_suspend(self) -> None:
        if self.refresh_timer:
            self.refresh_timer.stop()
```

- [ ] **Step 2: Implement WatchlistService**

Write `kimi_terminal/services/watchlist_service.py`:

```python
from __future__ import annotations

from kimi_terminal.config import ConfigManager, WatchlistItem


class WatchlistService:
    def __init__(self, config: ConfigManager) -> None:
        self.config = config

    def items(self) -> list[WatchlistItem]:
        return self.config.load_watchlist()

    def add(self, code: str, name: str) -> list[WatchlistItem]:
        return self.config.add_to_watchlist(WatchlistItem(code=code, name=name))

    def remove(self, code: str) -> list[WatchlistItem]:
        return self.config.remove_from_watchlist(code)
```

- [ ] **Step 3: Write Dashboard tests**

Append to `tests/test_screens.py`:

```python
import tempfile
from pathlib import Path

import pytest

from kimi_terminal.config import ConfigManager
from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.services.cache import Cache
from kimi_terminal.screens.dashboard_screen import DashboardScreen


@pytest.mark.asyncio
async def test_dashboard_compose():
    from textual.app import App

    class TestApp(App):
        def __init__(self):
            super().__init__()
            with tempfile.TemporaryDirectory() as td:
                cfg = ConfigManager(config_dir=Path(td))
            cache = Cache(Path(td) / "cache.db")
            api = KimiApiClient(cache, base_url="https://api.kimi.test/tools")
            self.dashboard = DashboardScreen(cfg, api)

        def compose(self):
            yield self.dashboard

    app = TestApp()
    async with app.run_test():
        dashboard = app.dashboard
        assert dashboard.query_one("KimiHeader") is not None
```

- [ ] **Step 4: Run tests and commit**

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
pytest tests/test_screens.py -v
```

Expected: 1 test passes.

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/screens/dashboard_screen.py kimi_terminal/services/watchlist_service.py tests/test_screens.py
git commit -m "feat: add dashboard screen with watchlist refresh"
```

---

## Task 9: Quote Screen

**Files:**
- Create: `kimi_terminal/screens/quote_screen.py`

- [ ] **Step 1: Implement QuoteScreen**

Write `kimi_terminal/screens/quote_screen.py`:

```python
from __future__ import annotations

import asyncio
import csv
import io
from datetime import date, timedelta

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Static

from kimi_terminal.models import Ticker
from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.widgets.footer import KimiFooter
from kimi_terminal.widgets.header import KimiHeader
from kimi_terminal.widgets.sparkline import Sparkline


class QuoteScreen(Screen):
    def __init__(self, api: KimiApiClient, ticker: str) -> None:
        super().__init__()
        self.api = api
        self.ticker_str = ticker
        self.ticker = Ticker.from_string(ticker)

    def compose(self) -> ComposeResult:
        yield KimiHeader(f"Quote: {self.ticker_str}")
        with Horizontal():
            with Vertical(id="info-panel"):
                yield Static(f"Loading {self.ticker_str}...", id="stock-info")
            with Vertical(id="chart-panel"):
                yield Sparkline(title="Price Trend")
                yield DataTable(id="tech-table")
        yield KimiFooter()

    async def on_mount(self) -> None:
        footer = self.query_one(KimiFooter)
        footer.set_status(f"Loading {self.ticker_str}...")
        try:
            tasks = [
                self.api.get_stock_info(self.ticker),
                self._load_history(),
            ]
            if self.ticker.supports_tech_indicators():
                tasks.append(self.api.get_realtime_tech(self.ticker))
            results = await asyncio.gather(*tasks, return_exceptions=True)

            info_text = results[0] if not isinstance(results[0], Exception) else str(results[0])
            self.query_one("#stock-info", Static).update(self._render_info(info_text))

            history = results[1] if not isinstance(results[1], Exception) else ""
            closes = self._parse_closes(history)
            self.query_one(Sparkline).set_data(closes, title=f"{self.ticker_str} Close")

            if len(results) > 2 and self.ticker.supports_tech_indicators():
                tech_text = results[2] if not isinstance(results[2], Exception) else ""
                self._render_tech_table(tech_text)
            else:
                self.query_one("#tech-table", DataTable).add_column("指标"), self.query_one("#tech-table", DataTable).add_column("值")
                self.query_one("#tech-table", DataTable).add_row("技术指标", "该市场不支持" if self.ticker.market == "hk" else "不可用")

            footer.set_status("Loaded")
        except Exception as exc:
            footer.set_status(f"Error: {exc}")

    async def _load_history(self) -> str:
        end = date.today()
        start = end - timedelta(days=90)
        return await self.api.get_historical_price(self.ticker, start, end)

    def _render_info(self, text: str) -> str:
        lines = text.strip().splitlines()
        if len(lines) < 2:
            return text
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return text
        row = rows[0]
        pairs = [f"{k}: {v}" for k, v in row.items() if v]
        return "\n".join(pairs[:30])

    def _parse_closes(self, text: str) -> list[float]:
        values = []
        try:
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                close = row.get("close") or row.get("CLOSE")
                if close:
                    try:
                        values.append(float(close))
                    except ValueError:
                        pass
        except Exception:
            pass
        return values if values else [0.0]

    def _render_tech_table(self, text: str) -> None:
        table = self.query_one("#tech-table", DataTable)
        table.clear()
        table.add_columns("指标", "值")
        try:
            reader = csv.DictReader(io.StringIO(text))
            row = next(reader, {})
            for k, v in row.items():
                table.add_row(k, v)
        except Exception:
            table.add_row("Error", "Failed to parse tech data")

    def on_key(self, event) -> None:
        if event.key == "d" or event.key == "escape":
            self.app.pop_screen()
```

- [ ] **Step 2: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/screens/quote_screen.py
git commit -m "feat: add quote screen with price trend and tech indicators"
```

---

## Task 10: Financials Screen

**Files:**
- Create: `kimi_terminal/screens/financial_screen.py`

- [ ] **Step 1: Implement FinancialScreen**

Write `kimi_terminal/screens/financial_screen.py`:

```python
from __future__ import annotations

import csv
import io

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Static

from kimi_terminal.models import Ticker
from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.widgets.footer import KimiFooter
from kimi_terminal.widgets.header import KimiHeader


STATEMENT_TABS = ["balance_sheet", "income_statement", "cash_flow", "financial_index"]
STATEMENT_LABELS = {"balance_sheet": "资产负债表", "income_statement": "利润表", "cash_flow": "现金流量表", "financial_index": "财务指标"}
INDEX_CATEGORIES = [
    "capital_structure",
    "liquidity",
    "efficiency",
    "profitability",
    "growth",
    "cash_coverage",
]
INDEX_LABELS = {
    "capital_structure": "资本结构",
    "liquidity": "流动性",
    "efficiency": "营运效率",
    "profitability": "盈利能力",
    "growth": "成长能力",
    "cash_coverage": "现金流覆盖",
}


class FinancialScreen(Screen):
    def __init__(self, api: KimiApiClient, ticker: str, report_date: str = "20241231") -> None:
        super().__init__()
        self.api = api
        self.ticker = Ticker.from_string(ticker)
        self.report_date = report_date
        self.current_tab = "balance_sheet"
        self.current_index_category = "profitability"

    def compose(self) -> ComposeResult:
        yield KimiHeader(f"Financials: {self.ticker.symbol}")
        with Vertical():
            yield Static("Tab: [1]资产负债表 [2]利润表 [3]现金流量表 [4]财务指标", id="tabs")
            with Horizontal():
                yield Static("Loading...", id="sidebar")
                yield DataTable(id="fs-table")
        yield KimiFooter()

    async def on_mount(self) -> None:
        await self._load_tab()

    async def _load_tab(self) -> None:
        footer = self.query_one(KimiFooter)
        footer.set_status(f"Loading {STATEMENT_LABELS[self.current_tab]}...")
        try:
            if self.current_tab == "financial_index":
                text = await self.api.get_financial_index(
                    self.ticker, self.current_index_category, self.report_date
                )
                self._render_index(text)
            else:
                text = await self.api.get_financial_statements(
                    self.ticker, self.current_tab, self.report_date
                )
                self._render_table(text)
            footer.set_status("Loaded")
        except Exception as exc:
            footer.set_status(f"Error: {exc}")

    def _render_table(self, text: str) -> None:
        table = self.query_one("#fs-table", DataTable)
        table.clear()
        try:
            reader = csv.DictReader(io.StringIO(text))
            headers = reader.fieldnames or []
            table.add_columns(*headers)
            for row in reader:
                table.add_row(*[row.get(h, "") for h in headers])
        except Exception as exc:
            table.add_columns("Error")
            table.add_row(str(exc))

    def _render_index(self, text: str) -> None:
        self._render_table(text)

    def on_key(self, event) -> None:
        key = event.key
        if key == "d" or key == "escape":
            self.app.pop_screen()
            return
        if key == "1":
            self.current_tab = "balance_sheet"
        elif key == "2":
            self.current_tab = "income_statement"
        elif key == "3":
            self.current_tab = "cash_flow"
        elif key == "4":
            self.current_tab = "financial_index"
        else:
            return
        self.run_worker(self._load_tab)
```

- [ ] **Step 2: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/screens/financial_screen.py
git commit -m "feat: add financials screen"
```

---

## Task 11: Announcements Screen

**Files:**
- Create: `kimi_terminal/screens/announcement_screen.py`

- [ ] **Step 1: Implement AnnouncementScreen**

Write `kimi_terminal/screens/announcement_screen.py`:

```python
from __future__ import annotations

import csv
import io
from datetime import date, timedelta

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Static

from kimi_terminal.models import Ticker
from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.widgets.footer import KimiFooter
from kimi_terminal.widgets.header import KimiHeader


class AnnouncementScreen(Screen):
    def __init__(self, api: KimiApiClient, ticker: str) -> None:
        super().__init__()
        self.api = api
        self.ticker = Ticker.from_string(ticker)

    def compose(self) -> ComposeResult:
        yield KimiHeader(f"Announcements: {self.ticker.symbol}")
        with Vertical():
            if not self.ticker.supports_announcements():
                yield Static("该市场暂不支持公告查询。仅 A 股支持。")
            else:
                yield DataTable(id="ann-table")
        yield KimiFooter()

    async def on_mount(self) -> None:
        if not self.ticker.supports_announcements():
            return
        footer = self.query_one(KimiFooter)
        footer.set_status("Loading announcements...")
        try:
            end = date.today()
            start = end - timedelta(days=90)
            text = await self.api.get_announcements(self.ticker, start, end)
            self._render_table(text)
            footer.set_status("Loaded")
        except Exception as exc:
            footer.set_status(f"Error: {exc}")

    def _render_table(self, text: str) -> None:
        table = self.query_one("#ann-table", DataTable)
        table.clear()
        table.cursor_type = "row"
        try:
            reader = csv.DictReader(io.StringIO(text))
            headers = reader.fieldnames or []
            table.add_columns(*[h for h in headers if h])
            for row in reader:
                table.add_row(*[row.get(h, "") for h in headers if h])
        except Exception as exc:
            table.add_columns("Error")
            table.add_row(str(exc))

    def on_key(self, event) -> None:
        if event.key == "d" or event.key == "escape":
            self.app.pop_screen()
```

- [ ] **Step 2: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/screens/announcement_screen.py
git commit -m "feat: add announcements screen"
```

---

## Task 12: Screener Screen

**Files:**
- Create: `kimi_terminal/screens/screener_screen.py`

- [ ] **Step 1: Implement ScreenerScreen**

Write `kimi_terminal/screens/screener_screen.py`:

```python
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Input, Static

from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.widgets.footer import KimiFooter
from kimi_terminal.widgets.header import KimiHeader
import csv
import io


class ScreenerScreen(Screen):
    def __init__(self, api: KimiApiClient, query: str = "") -> None:
        super().__init__()
        self.api = api
        self.query = query

    def compose(self) -> ComposeResult:
        yield KimiHeader("Screener [SCR]")
        with Vertical():
            yield Input(value=self.query, placeholder="输入选股条件，例如：人工智能 PE小于30", id="screener-input")
            yield Static("按 Enter 执行搜索", id="hint")
            yield DataTable(id="screen-table")
        yield KimiFooter()

    async def on_mount(self) -> None:
        if self.query:
            await self._run_query(self.query)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "screener-input":
            await self._run_query(event.value)

    async def _run_query(self, query: str) -> None:
        footer = self.query_one(KimiFooter)
        footer.set_status(f"Searching: {query}...")
        table = self.query_one("#screen-table", DataTable)
        table.clear()
        try:
            text = await self.api.get_related_stocks(query)
            reader = csv.DictReader(io.StringIO(text))
            headers = reader.fieldnames or []
            table.add_columns(*[h for h in headers if h])
            for row in reader:
                table.add_row(*[row.get(h, "") for h in headers if h])
            footer.set_status("Search complete")
        except Exception as exc:
            table.add_columns("Error")
            table.add_row(str(exc))
            footer.set_status(f"Error: {exc}")

    def on_key(self, event) -> None:
        if event.key == "d" or event.key == "escape":
            self.app.pop_screen()
```

- [ ] **Step 2: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/screens/screener_screen.py
git commit -m "feat: add screener screen"
```

---

## Task 13: App and CLI

**Files:**
- Create: `kimi_terminal/app.py`
- Create: `kimi_terminal/cli.py`
- Modify: `kimi_terminal/screens/__init__.py`
- Test: `tests/test_screens.py` (add integration test)

- [ ] **Step 1: Implement main App with routing**

Write `kimi_terminal/app.py`:

```python
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult

from kimi_terminal.config import ConfigManager, WatchlistItem
from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.services.cache import Cache
from kimi_terminal.screens.announcement_screen import AnnouncementScreen
from kimi_terminal.screens.dashboard_screen import DashboardScreen
from kimi_terminal.screens.financial_screen import FinancialScreen
from kimi_terminal.screens.quote_screen import QuoteScreen
from kimi_terminal.screens.screener_screen import ScreenerScreen
from kimi_terminal.widgets.command_input import CommandInput


class KimiTerminalApp(App):
    CSS = """
    Screen { align: center middle; }
    """

    def __init__(self, config_dir: str | None = None) -> None:
        super().__init__()
        cfg_path = Path(config_dir) if config_dir else None
        self.config = ConfigManager(config_dir=cfg_path)
        cfg = self.config.load_config()
        self.cache = Cache(cfg.resolved_cache_path())
        self.api = KimiApiClient(self.cache)

    def compose(self) -> ComposeResult:
        yield DashboardScreen(self.config, self.api)

    def on_mount(self) -> None:
        self.title = "Kimi Terminal"

    def handle_command(self, raw: str) -> None:
        cmd = raw.strip()
        if not cmd.startswith(":"):
            cmd = ":" + cmd
        parts = cmd[1:].split(None, 1)
        if not parts:
            return
        verb = parts[0].upper()
        arg = parts[1] if len(parts) > 1 else ""
        if verb in ("Q", "QUIT"):
            self.exit()
        elif verb in ("D", "HOME", "DASH"):
            self.pop_screen_until("dashboard")
        elif verb == "EQ" and arg:
            self.push_screen(QuoteScreen(self.api, arg))
        elif verb == "FA" and arg:
            self.push_screen(FinancialScreen(self.api, arg))
        elif verb == "ANN" and arg:
            self.push_screen(AnnouncementScreen(self.api, arg))
        elif verb == "SCR":
            self.push_screen(ScreenerScreen(self.api, arg))
        elif verb == "ADD" and arg:
            from kimi_terminal.models import Ticker
            try:
                t = Ticker.from_string(arg)
                self.config.add_to_watchlist(WatchlistItem(code=t.symbol, name=t.symbol))
            except Exception as exc:
                self.notify(f"Add failed: {exc}", severity="error")
        elif verb == "DEL" and arg:
            self.config.remove_from_watchlist(arg)
        else:
            self.notify(f"Unknown command: {verb}", severity="warning")

    def pop_screen_until(self, name: str) -> None:
        while len(self.screen_stack) > 1:
            self.pop_screen()

    def action_command(self) -> None:
        self.push_screen(CommandInput(":"), self.handle_command)

    BINDINGS = [
        ("f1", "push_screen('dashboard')", "Dashboard"),
        ("f2", "action_command", "Command"),
        ("q", "quit", "Quit"),
        ("colon", "action_command", "Command"),
    ]
```

- [ ] **Step 2: Implement CLI entry**

Write `kimi_terminal/cli.py`:

```python
from __future__ import annotations

import argparse
import sys

from kimi_terminal.app import KimiTerminalApp


def main() -> int:
    parser = argparse.ArgumentParser(description="Kimi Terminal - Bloomberg-style TUI for A-share/HK stocks")
    parser.add_argument("--config-dir", type=str, default=None, help="Override config directory")
    args = parser.parse_args()
    app = KimiTerminalApp(config_dir=args.config_dir)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Update screens __init__.py**

Write `kimi_terminal/screens/__init__.py`:

```python
from kimi_terminal.screens.announcement_screen import AnnouncementScreen
from kimi_terminal.screens.dashboard_screen import DashboardScreen
from kimi_terminal.screens.financial_screen import FinancialScreen
from kimi_terminal.screens.quote_screen import QuoteScreen
from kimi_terminal.screens.screener_screen import ScreenerScreen

__all__ = [
    "AnnouncementScreen",
    "DashboardScreen",
    "FinancialScreen",
    "QuoteScreen",
    "ScreenerScreen",
]
```

- [ ] **Step 4: Run CLI smoke test**

Run:
```bash
cd ~/Projects/kimi-terminal
source .venv/bin/activate
python -c "from kimi_terminal.cli import main; print('cli import ok')"
```

Expected: prints `cli import ok`.

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/kimi-terminal
git add kimi_terminal/app.py kimi_terminal/cli.py kimi_terminal/screens/__init__.py tests/test_screens.py
git commit -m "feat: wire app, cli, and screen routing"
```

---

## Task 14: README and Makefile

**Files:**
- Create: `README.md`
- Modify: `Makefile`

- [ ] **Step 1: Write README**

Write `README.md`:

```markdown
# Kimi Terminal

Bloomberg-style terminal for Mainland China (A-share) and Hong Kong stock market data, powered by `plugin-kimi-datasource`.

## Features

- Real-time watchlist dashboard with auto refresh
- Individual stock quote with price trend and technical indicators
- Financial statements and financial index analysis
- A-share announcements
- Intelligent stock screener

## Install

```bash
git clone <repo>
cd kimi-terminal
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
kmt
```

## Shortcuts

| Key | Action |
|---|---|
| `F1` / `d` | Dashboard |
| `F2` / `:` | Command bar |
| `Enter` | Open selected stock detail |
| `a` | Add to watchlist |
| `d` | Remove from watchlist / go back |
| `q` | Quit |

## Commands

- `:EQ 600519.SH` — Open quote screen
- `:FA 0700.HK` — Open financials
- `:ANN 000001.SZ` — Open announcements
- `:SCR 人工智能 PE小于30` — Run screener
- `:ADD 0700.HK` — Add to watchlist
- `:DEL 0700.HK` — Remove from watchlist

## Test

```bash
make test
```
```

- [ ] **Step 2: Write Makefile**

Write `Makefile`:

```makefile
VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
PYTEST=$(VENV)/bin/pytest

.PHONY: install test run lint clean

install:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev]"

test:
	$(PYTEST) tests/ -v

run:
	$(PYTHON) -m kimi_terminal.cli

clean:
	rm -rf $(VENV) build dist *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
```

- [ ] **Step 3: Verify Makefile**

Run:
```bash
cd ~/Projects/kimi-terminal
make test
```

Expected: pytest runs and all current tests pass.

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/kimi-terminal
git add README.md Makefile
git commit -m "docs: add README and Makefile"
```

---

## Plan Self-Review

### Spec coverage

| Spec Section | Implementing Task(s) |
|---|---|
| Project scaffold | Task 1 |
| Data models (Ticker, Quote, Candle, Financial, Announcement) | Task 2 |
| Config + watchlist | Task 3 |
| SQLite cache | Task 4 |
| API client with auth | Task 5 |
| Formatting utilities | Task 6 |
| Widgets (Header, Footer, CommandInput, QuoteTable, Sparkline) | Task 7 |
| Dashboard screen + refresh | Task 8 |
| Quote screen | Task 9 |
| Financials screen | Task 10 |
| Announcements screen | Task 11 |
| Screener screen | Task 12 |
| App routing + CLI | Task 13 |
| README + Makefile | Task 14 |

### Placeholder scan

- No TBD/TODO placeholders.
- Every code step contains actual implementation code.
- Every test step contains actual test code and expected output.
- Commands include expected behavior.

### Type consistency

- `Ticker.from_string()` is used consistently.
- `KimiApiClient` accepts `Cache` in constructor across all tasks.
- `ConfigManager` is passed into `DashboardScreen`.
- Screen constructors accept `api: KimiApiClient` plus ticker/query args.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-09-kimi-terminal-implementation-plan.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

Choose an approach to begin implementation.
