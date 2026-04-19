from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.container import ServiceContainer, get_container


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


def get_services() -> ServiceContainer:
    return get_container()
