from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from random import Random

import httpx

from app.config.settings import get_settings
from app.core.exceptions import ExternalServiceError
from app.utils.time_utils import utc_now


@dataclass(slots=True)
class InstrumentSnapshot:
    symbol: str
    price: float
    bid: float
    ask: float
    high: float
    low: float
    volume: float
    orderbook_imbalance: float
    trade_imbalance: float
    volatility_bps: float
    observed_at: object
    synthetic: bool = False


class BybitMarketDataClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = httpx.AsyncClient(base_url=self.settings.bybit_base_url, timeout=self.settings.BYBIT_TIMEOUT_SECONDS)
        self._random = Random(42)  # nosec B311 - synthetic fallback data only
        self._synthetic_state = {"BTCUSDT": 84000.0, "ETHUSDT": 1600.0, "TONUSDT": 4.8}

    async def get_latest_snapshot(self, symbol: str) -> InstrumentSnapshot:
        try:
            response = await self._client.get(
                "/v5/market/tickers",
                params={"category": self.settings.BYBIT_CATEGORY, "symbol": symbol},
            )
            response.raise_for_status()
            payload = response.json()
            result = payload["result"]["list"][0]
            last_price = float(result["lastPrice"])
            bid = float(result["bid1Price"] or last_price)
            ask = float(result["ask1Price"] or last_price)
            high = float(result["highPrice24h"] or last_price)
            low = float(result["lowPrice24h"] or last_price)
            volume = float(result["volume24h"] or 0.0)
            spread = max(ask - bid, last_price * 0.00005)
            orderbook_imbalance = await self._get_orderbook_imbalance(symbol)
            trade_imbalance = await self._get_trade_imbalance(symbol)
            return InstrumentSnapshot(
                symbol=symbol,
                price=last_price,
                bid=bid,
                ask=ask,
                high=high,
                low=low,
                volume=volume,
                orderbook_imbalance=orderbook_imbalance,
                trade_imbalance=trade_imbalance,
                volatility_bps=(spread / last_price) * 10_000,
                observed_at=utc_now(),
                synthetic=False,
            )
        except Exception:
            return self._synthetic_snapshot(symbol)

    def _synthetic_snapshot(self, symbol: str) -> InstrumentSnapshot:
        base = self._synthetic_state[symbol]
        drift = (self._random.random() - 0.48) * base * 0.003
        price = max(base + drift, base * 0.8)
        self._synthetic_state[symbol] = price
        spread = max(price * 0.00012, 0.0001)
        return InstrumentSnapshot(
            symbol=symbol,
            price=price,
            bid=price - spread / 2,
            ask=price + spread / 2,
            high=price * 1.001,
            low=price * 0.999,
            volume=100 + self._random.random() * 500,
            orderbook_imbalance=(self._random.random() - 0.5) * 0.8,
            trade_imbalance=(self._random.random() - 0.5) * 0.8,
            volatility_bps=20 + self._random.random() * 50,
            observed_at=utc_now(),
            synthetic=True,
        )

    async def get_recent_candles(self, symbol: str, limit: int = 80) -> dict[str, list[float]]:
        try:
            response = await self._client.get(
                "/v5/market/kline",
                params={
                    "category": self.settings.BYBIT_CATEGORY,
                    "symbol": symbol,
                    "interval": "1",
                    "limit": limit,
                },
            )
            response.raise_for_status()
            raw_rows = response.json()["result"]["list"]
            rows = sorted(raw_rows, key=lambda item: int(item[0]))
            if len(rows) < 20:
                raise ValueError("Not enough kline rows")
            return {
                "timestamps": [utc_now() if not row[0] else _from_millis(int(row[0])) for row in rows],
                "opens": [float(row[1]) for row in rows],
                "closes": [float(row[4]) for row in rows],
                "highs": [float(row[2]) for row in rows],
                "lows": [float(row[3]) for row in rows],
                "volumes": [float(row[5]) for row in rows],
            }
        except Exception:
            now = utc_now()
            base = self._synthetic_state.get(symbol, 100.0)
            closes = [base * (1 + ((idx - limit) / 1000)) for idx in range(limit)]
            opens = [c * (1 + (self._random.random() - 0.5) * 0.001) for c in closes]
            highs = [value * 1.001 for value in closes]
            lows = [value * 0.999 for value in closes]
            volumes = [100 + idx for idx in range(limit)]
            return {
                "timestamps": [now - timedelta(minutes=limit - idx) for idx in range(limit)],
                "opens": opens,
                "closes": closes,
                "highs": highs,
                "lows": lows,
                "volumes": volumes,
            }

    async def _get_orderbook_imbalance(self, symbol: str) -> float:
        try:
            response = await self._client.get(
                "/v5/market/orderbook",
                params={"category": self.settings.BYBIT_CATEGORY, "symbol": symbol, "limit": 10},
            )
            response.raise_for_status()
            result = response.json()["result"]
            bids = sum(float(item[1]) for item in result.get("b", []))
            asks = sum(float(item[1]) for item in result.get("a", []))
            total = bids + asks
            if total <= 0:
                return 0.0
            return (bids - asks) / total
        except Exception:
            return 0.0

    async def _get_trade_imbalance(self, symbol: str) -> float:
        try:
            response = await self._client.get(
                "/v5/market/recent-trade",
                params={"category": self.settings.BYBIT_CATEGORY, "symbol": symbol, "limit": 20},
            )
            response.raise_for_status()
            trades = response.json()["result"]["list"]
            buy_qty = sum(float(item["size"]) for item in trades if item.get("side") == "Buy")
            sell_qty = sum(float(item["size"]) for item in trades if item.get("side") == "Sell")
            total = buy_qty + sell_qty
            if total <= 0:
                return 0.0
            return (buy_qty - sell_qty) / total
        except Exception:
            return 0.0


def _from_millis(timestamp_ms: int):
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=utc_now().tzinfo)
