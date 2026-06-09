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
