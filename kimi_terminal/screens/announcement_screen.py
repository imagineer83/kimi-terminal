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
