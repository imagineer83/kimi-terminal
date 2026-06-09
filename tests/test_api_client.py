import tempfile
from pathlib import Path

import pytest
import respx
from httpx import Response

from kimi_terminal.models import Ticker
from kimi_terminal.services.api_client import KimiApiClient, KimiAuthError
from kimi_terminal.services.cache import Cache


@pytest.fixture
def client():
    cache = Cache(Path(tempfile.mkdtemp()) / "cache.db")
    return KimiApiClient(cache, base_url="https://api.kimi.test/tools")


def _ok_result(text: str):
    return {"is_success": True, "result": {"assistant": [{"type": "text", "text": text}]}}


@respx.mock
@pytest.mark.asyncio
async def test_call_data_source_tool_success(client):
    route = respx.post("https://api.kimi.test/tools").mock(return_value=Response(200, json=_ok_result("hello")))
    import kimi_terminal.services.api_client as api_mod
    api_mod._load_credentials = lambda: "fake_token"

    result = await client.call_data_source_tool("stock_finance_data", "test_api", {"foo": "bar"})
    assert client._extract_text(result) == "hello"
    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_get_realtime_price(client):
    route = respx.post("https://api.kimi.test/tools").mock(
        return_value=Response(200, json=_ok_result("ticker,price\n600519.SH,1500"))
    )
    import kimi_terminal.services.api_client as api_mod
    api_mod._load_credentials = lambda: "fake_token"

    text = await client.get_realtime_price([Ticker.from_string("600519.SH")])
    assert "600519.SH" in text
    assert route.called
