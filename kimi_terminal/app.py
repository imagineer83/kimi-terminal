from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult

from kimi_terminal.config import ConfigManager, WatchlistItem
from kimi_terminal.services.api_client import KimiApiClient
from kimi_terminal.services.cache import Cache
from kimi_terminal.screens.announcement_screen import AnnouncementScreen
from kimi_terminal.screens.dashboard_screen import DashboardScreen
from kimi_terminal.screens.financial_screen import FinancialScreen
from kimi_terminal.screens.quote_screen import QuoteScreen
from kimi_terminal.screens.screener_screen import ScreenerScreen
from kimi_terminal.widgets.command_input import CommandInput


class KimiTerminalApp(App):
    CSS = """
    Screen { align: center middle; }
    """

    def __init__(self, config_dir: str | None = None) -> None:
        super().__init__()
        cfg_path = Path(config_dir) if config_dir else None
        self.config = ConfigManager(config_dir=cfg_path)
        cfg = self.config.load_config()
        self.cache = Cache(cfg.resolved_cache_path())
        self.api = KimiApiClient(self.cache)

    def compose(self) -> ComposeResult:
        yield DashboardScreen(self.config, self.api)

    def on_mount(self) -> None:
        self.title = "Kimi Terminal"

    def handle_command(self, raw: str) -> None:
        cmd = raw.strip()
        if not cmd.startswith(":"):
            cmd = ":" + cmd
        parts = cmd[1:].split(None, 1)
        if not parts:
            return
        verb = parts[0].upper()
        arg = parts[1] if len(parts) > 1 else ""
        if verb in ("Q", "QUIT"):
            self.exit()
        elif verb in ("D", "HOME", "DASH"):
            self.pop_screen_until("dashboard")
        elif verb == "EQ" and arg:
            self.push_screen(QuoteScreen(self.api, arg))
        elif verb == "FA" and arg:
            self.push_screen(FinancialScreen(self.api, arg))
        elif verb == "ANN" and arg:
            self.push_screen(AnnouncementScreen(self.api, arg))
        elif verb == "SCR":
            self.push_screen(ScreenerScreen(self.api, arg))
        elif verb == "ADD" and arg:
            from kimi_terminal.models import Ticker
            try:
                t = Ticker.from_string(arg)
                self.config.add_to_watchlist(WatchlistItem(code=t.symbol, name=t.symbol))
            except Exception as exc:
                self.notify(f"Add failed: {exc}", severity="error")
        elif verb == "DEL" and arg:
            self.config.remove_from_watchlist(arg)
        else:
            self.notify(f"Unknown command: {verb}", severity="warning")

    def pop_screen_until(self, name: str) -> None:
        while len(self.screen_stack) > 1:
            self.pop_screen()

    def action_command(self) -> None:
        self.push_screen(CommandInput(":"), self.handle_command)

    def action_dashboard(self) -> None:
        self.pop_screen_until("dashboard")

    BINDINGS = [
        ("f1", "dashboard", "Dashboard"),
        ("f2", "action_command", "Command"),
        ("q", "quit", "Quit"),
        ("colon", "action_command", "Command"),
    ]
