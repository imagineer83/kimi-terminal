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
