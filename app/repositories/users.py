from __future__ import annotations

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.one_or_none(select(User).where(User.telegram_id == telegram_id))

    async def upsert_telegram_user(self, telegram_id: int, username: str | None, first_name: str | None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(telegram_id=telegram_id, username=username, first_name=first_name, is_active=True)
            return await self.add(user)
        user.username = username
        user.first_name = first_name
        user.is_active = True
        await self.session.flush()
        return user
