from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models.strategy_config import StrategyConfig
from app.repositories.config import ConfigRepository
from app.schemas.config import StrategyConfigUpdate


class ConfigService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ConfigRepository(session)

    async def ensure_defaults(self) -> None:
        settings = get_settings()
        for symbol in settings.TRADING_SYMBOLS:
            existing = await self.repo.get_strategy_config(symbol)
            if existing is None:
                await self.repo.add(StrategyConfig(symbol=symbol))

    async def list_configs(self) -> list[StrategyConfig]:
        return await self.repo.get_strategy_configs()

    async def update_config(self, symbol: str, payload: StrategyConfigUpdate) -> StrategyConfig:
        config = await self.repo.get_strategy_config(symbol)
        if config is None:
            config = await self.repo.add(StrategyConfig(symbol=symbol))
        for key, value in payload.model_dump(exclude_none=True).items():
            setattr(config, key, value)
        await self.repo.session.flush()
        return config
