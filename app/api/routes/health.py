from fastapi import APIRouter

from app.config.settings import get_settings
from app.schemas.common import AppInfoResponse, HealthResponse
from app.utils.time_utils import utc_now

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", version=settings.APP_VERSION, environment=settings.APP_ENV)


@router.get("/info", response_model=AppInfoResponse)
async def info() -> AppInfoResponse:
    settings = get_settings()
    return AppInfoResponse(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        paper_trading=settings.PAPER_TRADING,
        trading_enabled=settings.TRADING_ENABLED,
        server_time=utc_now(),
    )
