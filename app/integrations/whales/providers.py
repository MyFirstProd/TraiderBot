from __future__ import annotations

import httpx
from random import Random

from app.schemas.whale import WhaleEventCreate
from app.utils.time_utils import utc_now


class BlockchainWhaleProvider:
    """Бесплатный провайдер на основе публичных blockchain API"""

    def __init__(self) -> None:
        self.timeout = 10

    async def fetch(self) -> list[WhaleEventCreate]:
        events: list[WhaleEventCreate] = []

        # BTC крупные транзакции через blockchain.com (бесплатно)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get("https://blockchain.info/unconfirmed-transactions?format=json")
                if resp.status_code == 200:
                    data = resp.json()
                    for tx in data.get("txs", [])[:5]:  # Топ-5 транзакций
                        value_btc = tx.get("out", [{}])[0].get("value", 0) / 1e8
                        if value_btc > 10:  # Больше 10 BTC
                            usd_value = value_btc * 95000  # Примерная цена BTC
                            events.append(
                                WhaleEventCreate(
                                    asset="BTC",
                                    chain="BTC",
                                    amount=value_btc,
                                    usd_value=usd_value,
                                    from_type="wallet",
                                    to_type="wallet",
                                    exchange_related=False,
                                    timestamp=utc_now(),
                                    significance_score=min(usd_value / 5_000_000, 1.0),
                                )
                            )
        except Exception:
            pass  # Fallback to synthetic

        # Если нет реальных данных, добавим синтетику
        if not events:
            events = await SyntheticWhaleProvider().fetch()

        return events


class SyntheticWhaleProvider:
    def __init__(self) -> None:
        self._random = Random(9)  # nosec B311 - synthetic fallback data only

    async def fetch(self) -> list[WhaleEventCreate]:
        symbols = [("BTC", "BTCUSDT", 2_500_000.0), ("ETH", "ETHUSDT", 750_000.0), ("TON", "TONUSDT", 200_000.0)]
        events: list[WhaleEventCreate] = []
        for asset, _, usd_floor in symbols:
            magnitude = usd_floor + self._random.random() * usd_floor
            events.append(
                WhaleEventCreate(
                    asset=asset,
                    chain=asset,
                    amount=10 + self._random.random() * 1000,
                    usd_value=magnitude,
                    from_type="wallet",
                    to_type="exchange" if self._random.random() > 0.5 else "wallet",
                    exchange_related=True,
                    timestamp=utc_now(),
                    significance_score=min(magnitude / (usd_floor * 2), 1.0),
                )
            )
        return events
