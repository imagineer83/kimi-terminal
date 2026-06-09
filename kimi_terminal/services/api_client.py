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
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, trust_env=False) as client:
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
