import pytest

from kimi_terminal.models import Ticker


def test_ticker_from_string_valid():
    t = Ticker.from_string("600519.SH")
    assert t.symbol == "600519.SH"
    assert t.market == "sh"


def test_ticker_from_string_invalid():
    with pytest.raises(ValueError):
        Ticker.from_string("123")


def test_ticker_supports_tech():
    assert Ticker.from_string("600519.SH").supports_tech_indicators() is True
    assert Ticker.from_string("688981.SH").supports_tech_indicators() is False
    assert Ticker.from_string("0700.HK").supports_tech_indicators() is False


def test_ticker_supports_announcements():
    assert Ticker.from_string("000001.SZ").supports_announcements() is True
    assert Ticker.from_string("0700.HK").supports_announcements() is False
