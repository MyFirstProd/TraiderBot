from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.dependencies import get_services, get_session
from app.core.security import require_admin
from app.models.audit_log import AuditLog
from app.repositories.analytics import AnalyticsRepository
from app.schemas.common import MessageResponse
from app.schemas.config import RuntimeConfigResponse, StrategyConfigRead, StrategyConfigUpdate
from app.services.config_service import ConfigService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/config", response_model=RuntimeConfigResponse)
async def current_runtime_config() -> RuntimeConfigResponse:
    settings = get_settings()
    return RuntimeConfigResponse(
        symbols=settings.TRADING_SYMBOLS,
        paper_trading=settings.PAPER_TRADING,
        trading_enabled=settings.TRADING_ENABLED,
        risk_per_trade_pct=settings.RISK_PER_TRADE_PCT,
        max_daily_loss_pct=settings.MAX_DAILY_LOSS_PCT,
        max_concurrent_positions=settings.MAX_CONCURRENT_POSITIONS,
    )


@router.get("/strategies", response_model=list[StrategyConfigRead])
async def list_strategies(session: AsyncSession = Depends(get_session)) -> list[StrategyConfigRead]:
    service = ConfigService(session)
    await service.ensure_defaults()
    return await service.list_configs()


@router.put("/strategies/{symbol}", response_model=StrategyConfigRead)
async def update_strategy(
    symbol: str,
    payload: StrategyConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> StrategyConfigRead:
    service = ConfigService(session)
    await service.ensure_defaults()
    return await service.update_config(symbol, payload)


@router.post("/strategy/enable", response_model=MessageResponse)
async def enable_strategy(services=Depends(get_services)) -> MessageResponse:
    services.runtime.trading_enabled = True
    return MessageResponse(message="Торговля включена")


@router.post("/strategy/disable", response_model=MessageResponse)
async def disable_strategy(services=Depends(get_services)) -> MessageResponse:
    services.runtime.trading_enabled = False
    return MessageResponse(message="Торговля отключена")


@router.post("/model/train", response_model=dict)
async def train_model(session: AsyncSession = Depends(get_session), services=Depends(get_services)) -> dict:
    result = await services.ml.train(get_settings().TRADING_SYMBOLS, session=session)
    repo = AnalyticsRepository(session)
    await repo.create_audit_log(
        AuditLog(
            actor="admin_api",
            action="model_trained",
            target="gbdt",
            details=result,
        )
    )
    return result
