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
                self._render_table(text)
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
