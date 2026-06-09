from __future__ import annotations

from textual.screen import Screen

from kimi_terminal.services.api_client import KimiApiClient


class QuoteScreen(Screen):
    def __init__(self, api: KimiApiClient, ticker: str) -> None:
        super().__init__()
        self.api = api
        self.ticker = ticker
