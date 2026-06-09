import tempfile
from pathlib import Path

import pytest

from kimi_terminal.config import ConfigManager
from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.services.cache import Cache
from kimi_terminal.screens.dashboard_screen import DashboardScreen


@pytest.mark.asyncio
async def test_dashboard_compose():
    from textual.app import App

    class TestApp(App):
        def __init__(self):
            super().__init__()
            with tempfile.TemporaryDirectory() as td:
                cfg = ConfigManager(config_dir=Path(td))
            cache = Cache(Path(td) / "cache.db")
            api = KimiApiClient(cache, base_url="https://api.kimi.test/tools")
            self.dashboard = DashboardScreen(cfg, api)

        def compose(self):
            yield self.dashboard

    app = TestApp()
    async with app.run_test():
        dashboard = app.dashboard
        assert dashboard.query_one("KimiHeader") is not None
