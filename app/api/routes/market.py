from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_services, get_session
from app.indicators.ma import EMA, SMA, WMA
from app.indicators.rsi import RSI
from app.indicators.volatility import ATR
from app.integrations.bybit.client import BybitMarketDataClient
from app.repositories.analytics import AnalyticsRepository
from app.repositories.trading import TradingRepository
from app.schemas.config import RiskStatusResponse
from app.schemas.dashboard import MarketSnapshotRead
from app.schemas.news import NewsEventRead
from app.schemas.position import PositionRead
from app.schemas.signal import SignalRead
from app.schemas.trade import TradeRead
from app.schemas.whale import WhaleEventRead

router = APIRouter()


@router.get("/signals", response_model=list[SignalRead])
async def active_signals(session: AsyncSession = Depends(get_session)) -> list[SignalRead]:
    repo = TradingRepository(session)
    return await repo.list_signals()


@router.get("/snapshots", response_model=list[MarketSnapshotRead])
async def snapshots(session: AsyncSession = Depends(get_session)) -> list[MarketSnapshotRead]:
    repo = TradingRepository(session)
    return await repo.list_latest_snapshots_by_symbol()


@router.get("/positions", response_model=list[PositionRead])
async def positions(session: AsyncSession = Depends(get_session)) -> list[PositionRead]:
    repo = TradingRepository(session)
    return await repo.list_open_positions()


@router.get("/trades", response_model=list[TradeRead])
async def trades(session: AsyncSession = Depends(get_session)) -> list[TradeRead]:
    repo = TradingRepository(session)
    return await repo.list_trades()


@router.get("/news", response_model=list[NewsEventRead])
async def news(session: AsyncSession = Depends(get_session)) -> list[NewsEventRead]:
    repo = AnalyticsRepository(session)
    return await repo.list_news()


@router.get("/whales", response_model=list[WhaleEventRead])
async def whales(session: AsyncSession = Depends(get_session)) -> list[WhaleEventRead]:
    repo = AnalyticsRepository(session)
    return await repo.list_whales()


@router.get("/risk", response_model=RiskStatusResponse)
async def risk_status(services=Depends(get_services)) -> RiskStatusResponse:
    runtime = services.runtime
    return RiskStatusResponse(
        trading_enabled=runtime.trading_enabled,
        paper_trading=runtime.settings.PAPER_TRADING,
        circuit_breaker_open=runtime.risk.circuit_breaker_open,
        daily_realized_pnl=runtime.risk.daily_realized_pnl,
        daily_loss_limit_pct=runtime.risk.max_daily_loss_pct,
        consecutive_losses=runtime.risk.consecutive_losses,
        open_positions=len(runtime.paper.positions),
        max_concurrent_positions=runtime.risk.max_concurrent_positions,
    )


@router.get("/model/status", response_model=dict)
async def model_status(services=Depends(get_services)) -> dict:
    return services.ml.status()


@router.get("/candles/{symbol}", response_model=dict)
async def candles(symbol: str, limit: int = 100) -> dict:
    client = BybitMarketDataClient()
    data = await client.get_recent_candles(symbol, limit=limit)
    closes = data["closes"]
    highs = data["highs"]
    lows = data["lows"]
    ema9_vals = list(EMA(9).compute(closes))
    ema21_vals = list(EMA(21).compute(closes))
    sma20_vals = list(SMA(20).compute(closes))
    sma50_vals = list(SMA(50).compute(closes))
    wma21_vals = list(WMA(21).compute(closes))
    rsi14_vals = list(RSI(14).compute(closes))
    atr14_vals = list(ATR(14).compute(highs, lows, closes))
    return {
        "symbol": symbol,
        "timestamps": [t.isoformat() for t in data["timestamps"]],
        "opens": data.get("opens", closes),
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "volumes": data["volumes"],
        "ema9": ema9_vals,
        "ema21": ema21_vals,
        "sma20": sma20_vals,
        "sma50": sma50_vals,
        "wma21": wma21_vals,
        "rsi14": rsi14_vals,
        "atr14": atr14_vals,
    }
