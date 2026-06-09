import tempfile
from pathlib import Path

from kimi_terminal.services.cache import Cache


def test_cache_set_get():
    with tempfile.TemporaryDirectory() as td:
        cache = Cache(Path(td) / "cache.db")
        cache.set("price", {"ticker": "600519.SH"}, {"close": 1500.0})
        result = cache.get("price", {"ticker": "600519.SH"}, ttl_seconds=60)
        assert result == {"close": 1500.0}


def test_cache_ttl_expires():
    with tempfile.TemporaryDirectory() as td:
        cache = Cache(Path(td) / "cache.db")
        cache.set("price", {"ticker": "600519.SH"}, {"close": 1500.0})
        result = cache.get("price", {"ticker": "600519.SH"}, ttl_seconds=-1)
        assert result is None


def test_cache_missing():
    with tempfile.TemporaryDirectory() as td:
        cache = Cache(Path(td) / "cache.db")
        assert cache.get("price", {"ticker": "MISSING"}, ttl_seconds=60) is None
