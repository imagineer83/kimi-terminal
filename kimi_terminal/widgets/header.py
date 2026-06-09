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
        super().__init__(title)
        self.title = title

    def update_title(self, title: str) -> None:
        self.title = title
        self.update(title)
