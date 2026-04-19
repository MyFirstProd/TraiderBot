from __future__ import annotations

from sqlalchemy import select

from app.models.bot_settings import BotSetting
from app.models.strategy_config import StrategyConfig
from app.repositories.base import BaseRepository


class ConfigRepository(BaseRepository):
    async def get_strategy_configs(self) -> list[StrategyConfig]:
        return await self.list_by_stmt(select(StrategyConfig).order_by(StrategyConfig.symbol))

    async def get_strategy_config(self, symbol: str) -> StrategyConfig | None:
        return await self.one_or_none(select(StrategyConfig).where(StrategyConfig.symbol == symbol))

    async def upsert_setting(self, key: str, value: str) -> BotSetting:
        setting = await self.one_or_none(select(BotSetting).where(BotSetting.key == key))
        if setting is None:
            setting = BotSetting(key=key, value=value)
            return await self.add(setting)
        setting.value = value
        await self.session.flush()
        return setting
