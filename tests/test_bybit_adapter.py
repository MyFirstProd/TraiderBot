import pytest

from app.integrations.bybit.client import BybitMarketDataClient


@pytest.mark.asyncio
async def test_bybit_adapter_returns_snapshot():
    client = BybitMarketDataClient()
    snapshot = await client.get_latest_snapshot("BTCUSDT")
    assert snapshot.symbol == "BTCUSDT"
    assert snapshot.price > 0
