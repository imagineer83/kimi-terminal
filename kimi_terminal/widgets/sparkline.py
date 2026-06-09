from textual.widgets import Static


class Sparkline(Static):
    DEFAULT_CSS = """
    Sparkline {
        height: 10;
        border: solid $primary;
    }
    """

    def __init__(self, data: list[float] | None = None, title: str = "") -> None:
        super().__init__()
        self.data = data or []
        self.title = title

    def set_data(self, data: list[float], title: str = "") -> None:
        self.data = data
        if title:
            self.title = title
        self.refresh()

    def render(self) -> str:
        if not self.data:
            return self.title or "No data"
        lines = []
        if self.title:
            lines.append(self.title)
        width = self.size.width or 40
        height = self.size.height or 10
        if width <= 0 or height <= 0:
            return self.title or "No data"
        mn, mx = min(self.data), max(self.data)
        rng = mx - mn if mx != mn else 1.0
        for row in range(height):
            idx = int((row / max(height - 1, 1)) * (len(self.data) - 1))
            val = self.data[idx]
            norm = int(((val - mn) / rng) * (width - 1))
            line = [" "] * width
            if 0 <= norm < width:
                line[norm] = "*"
            lines.append("".join(line))
        return "\n".join(lines)
