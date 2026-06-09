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

    def __init__(self) -> None:
        super().__init__("Ready")

    def watch_status(self, status: str) -> None:
        self.update(status)

    def set_status(self, message: str) -> None:
        self.status = message
