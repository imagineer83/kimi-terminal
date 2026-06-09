from __future__ import annotations

from kimi_terminal.config import ConfigManager, WatchlistItem


class WatchlistService:
    def __init__(self, config: ConfigManager) -> None:
        self.config = config

    def items(self) -> list[WatchlistItem]:
        return self.config.load_watchlist()

    def add(self, code: str, name: str) -> list[WatchlistItem]:
        return self.config.add_to_watchlist(WatchlistItem(code=code, name=name))

    def remove(self, code: str) -> list[WatchlistItem]:
        return self.config.remove_from_watchlist(code)
