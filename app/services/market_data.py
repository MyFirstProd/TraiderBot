from __future__ import annotations

from app.integrations.bybit.client import BybitMarketDataClient


class MarketDataService:
    def __init__(self) -> None:
        self.client = BybitMarketDataClient()

    async def get_symbol_state(self, symbol: str) -> dict:
        snapshot = await self.client.get_latest_snapshot(symbol)
        candles = await self.client.get_recent_candles(symbol)
        return {
            **candles,
            "symbol": symbol,
            "current_price": snapshot.price,
            "bid": snapshot.bid,
            "ask": snapshot.ask,
            "high": snapshot.high,
            "low": snapshot.low,
            "volume": snapshot.volume,
            "volatility_bps": snapshot.volatility_bps,
            "orderbook_imbalance": snapshot.orderbook_imbalance,
            "trade_imbalance": snapshot.trade_imbalance,
            "observed_at": snapshot.observed_at,
            "synthetic": snapshot.synthetic,
        }
