from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, instance):
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def list_by_stmt(self, stmt: Select):
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def one_or_none(self, stmt: Select):
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
