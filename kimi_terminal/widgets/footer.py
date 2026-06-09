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
