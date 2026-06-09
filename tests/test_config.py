import tempfile
from pathlib import Path

from kimi_terminal.config import ConfigManager, WatchlistItem


def test_config_round_trip():
    with tempfile.TemporaryDirectory() as td:
        cm = ConfigManager(config_dir=Path(td))
        cm.save_config(cm.load_config())
        loaded = cm.load_config()
        assert loaded.theme == "dark"
        assert loaded.refresh_interval_seconds == 30


def test_watchlist_default():
    with tempfile.TemporaryDirectory() as td:
        cm = ConfigManager(config_dir=Path(td))
        items = cm.load_watchlist()
        assert len(items) == 2
        assert items[0].code == "600519.SH"


def test_watchlist_add_remove():
    with tempfile.TemporaryDirectory() as td:
        cm = ConfigManager(config_dir=Path(td))
        cm.save_watchlist([])
        cm.add_to_watchlist(WatchlistItem(code="000001.SZ", name="平安银行"))
        items = cm.load_watchlist()
        assert len(items) == 1
        cm.remove_from_watchlist("000001.SZ")
        items = cm.load_watchlist()
        assert len(items) == 0
