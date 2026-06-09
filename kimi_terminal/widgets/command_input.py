from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class CommandInput(ModalScreen[str | None]):
    DEFAULT_CSS = """
    CommandInput {
        align: center middle;
    }
    CommandInput > Horizontal {
        width: 80;
        height: auto;
        background: $surface;
        border: thick $background 80%;
        padding: 1 2;
    }
    """

    def __init__(self, initial: str = "") -> None:
        super().__init__()
        self.initial = initial

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(":")
            yield Input(value=self.initial, placeholder="command")
            yield Button("OK", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        inp = self.query_one(Input)
        self.dismiss(inp.value or None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value or None)

    def key_escape(self) -> None:
        self.dismiss(None)
