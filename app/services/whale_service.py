from __future__ import annotations

from app.integrations.whales.providers import BlockchainWhaleProvider
from app.schemas.whale import WhaleEventCreate


class WhaleService:
    def __init__(self) -> None:
        self.provider = BlockchainWhaleProvider()

    async def collect(self) -> list[WhaleEventCreate]:
        return await self.provider.fetch()

    @staticmethod
    def score_for_symbol(events: list[WhaleEventCreate], symbol: str) -> float:
        asset = symbol.replace("USDT", "")
        relevant = [event for event in events if event.asset == asset]
        if not relevant:
            return 0.0
        signed = [(-event.significance_score if event.to_type == "exchange" else event.significance_score) for event in relevant]
        return max(min(sum(signed) / len(signed), 1.0), -1.0)
