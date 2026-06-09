import pytest

from kimi_terminal.widgets.command_input import CommandInput
from kimi_terminal.widgets.footer import KimiFooter
from kimi_terminal.widgets.header import KimiHeader
from kimi_terminal.widgets.sparkline import Sparkline


@pytest.mark.asyncio
async def test_header_renders_title():
    from textual.app import App

    class TestApp(App):
        def compose(self):
            yield KimiHeader("Test Title")

    app = TestApp()
    async with app.run_test() as pilot:
        header = app.query_one(KimiHeader)
        assert header.title == "Test Title"


@pytest.mark.asyncio
async def test_footer_status_update():
    from textual.app import App

    class TestApp(App):
        def compose(self):
            yield KimiFooter()

    app = TestApp()
    async with app.run_test() as pilot:
        footer = app.query_one(KimiFooter)
        footer.set_status("Loading...")
        assert footer.status == "Loading..."


def test_sparkline_set_data():
    s = Sparkline()
    s.set_data([1.0, 2.0, 3.0], title="Trend")
    assert s.data == [1.0, 2.0, 3.0]
    assert s.title == "Trend"
