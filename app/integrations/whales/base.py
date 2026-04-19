from __future__ import annotations

from typing import Protocol

from app.schemas.whale import WhaleEventCreate


class WhaleProvider(Protocol):
    async def fetch(self) -> list[WhaleEventCreate]:
        ...
