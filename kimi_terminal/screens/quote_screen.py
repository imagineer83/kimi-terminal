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
                table = self.query_one("#tech-table", DataTable)
                table.add_column("指标")
                table.add_column("值")
                table.add_row("技术指标", "该市场不支持" if self.ticker.market == "hk" else "不可用")

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
