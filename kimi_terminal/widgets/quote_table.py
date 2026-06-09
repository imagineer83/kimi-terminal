from rich.text import Text
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
            row_idx = self.row_count - 1
            self.update_cell_at(
                (row_idx, 3), Text(fmt_change(q.change), style=change_color)
            )
            self.update_cell_at(
                (row_idx, 4), Text(fmt_pct(q.change_pct), style=change_color)
            )
