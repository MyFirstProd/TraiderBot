import pytest

from app.strategies.scalping import ScalpingStrategy


@pytest.mark.asyncio
async def test_scalping_strategy_generates_signal():
    strategy = ScalpingStrategy("BTCUSDT", {})
    closes = [100 + idx * 0.2 for idx in range(80)]
    market_data = {
        "closes": closes,
        "highs": [value * 1.001 for value in closes],
        "lows": [value * 0.999 for value in closes],
        "current_price": closes[-1],
        "bid": closes[-1] * 0.9999,
        "ask": closes[-1] * 1.0001,
    }
    signal = await strategy.generate_signal(market_data, news_sentiment=0.3, whale_flow=0.2)
    assert signal.confidence >= 0
    assert "rsi14" in signal.indicators_snapshot
