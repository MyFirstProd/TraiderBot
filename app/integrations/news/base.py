from __future__ import annotations

from typing import Protocol

from app.schemas.news import NewsEventCreate


class NewsProvider(Protocol):
    async def fetch(self) -> list[NewsEventCreate]:
        ...
