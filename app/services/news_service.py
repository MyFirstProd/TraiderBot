from __future__ import annotations

from app.integrations.news.rss import RssNewsProvider
from app.schemas.news import NewsEventCreate


class NewsService:
    def __init__(self) -> None:
        self.provider = RssNewsProvider()

    async def collect(self) -> list[NewsEventCreate]:
        return await self.provider.fetch()

    @staticmethod
    def score_for_symbol(events: list[NewsEventCreate], symbol: str) -> float:
        relevant = [event for event in events if symbol in event.symbol_relevance]
        if not relevant:
            return 0.0
        return max(min(sum(event.sentiment + event.relevance * 0.2 for event in relevant) / len(relevant), 1.0), -1.0)
