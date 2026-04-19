from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.common import ORMModel
from app.schemas.config import RiskStatusResponse, StrategyConfigRead
from app.schemas.news import NewsEventRead
from app.schemas.position import PositionRead
from app.schemas.signal import SignalRead
from app.schemas.trade import TradeRead
from app.schemas.whale import WhaleEventRead


class MarketSnapshotRead(ORMModel):
    symbol: str
    observed_at: datetime
    price: float
    bid: float
    ask: float
    high: float
    low: float
    volume: float
    volatility_bps: float
    orderbook_imbalance: float
    trade_imbalance: float
    is_synthetic: bool


class ModelStatusResponse(BaseModel):
    trained: bool
    path: str
    updated_at: datetime | None = None
    size_bytes: int = 0
    model_type: str


class TimeValuePoint(BaseModel):
    timestamp: datetime
    value: float
    label: str | None = None
    meta: dict[str, Any] | None = None


class DashboardChartsResponse(BaseModel):
    market_price: dict[str, list[TimeValuePoint]]
    signal_score: dict[str, list[TimeValuePoint]]
    whale_usd: dict[str, list[TimeValuePoint]]
    news_sentiment: list[TimeValuePoint]
    trade_pnl: list[TimeValuePoint]
    model_training: list[TimeValuePoint]


class MiniAppDashboardResponse(BaseModel):
    server_time: datetime
    app_name: str
    paper_trading: bool
    trading_enabled: bool
    equity: float
    risk: RiskStatusResponse
    model: ModelStatusResponse
    snapshots: list[MarketSnapshotRead]
    signals: list[SignalRead]
    positions: list[PositionRead]
    trades: list[TradeRead]
    news: list[NewsEventRead]
    whales: list[WhaleEventRead]
    strategies: list[StrategyConfigRead]
    charts: DashboardChartsResponse
