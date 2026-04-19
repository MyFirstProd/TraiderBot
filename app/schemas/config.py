from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class StrategyConfigRead(ORMModel):
    id: int
    symbol: str
    market_mode: str
    is_enabled: bool
    ma_type: str
    ema_fast: int
    ema_slow: int
    sma_fast: int
    sma_slow: int
    wma_period: int
    rsi_period: int
    risk_pct: float
    min_model_score: float
    max_spread_bps: float
    created_at: datetime
    updated_at: datetime


class StrategyConfigUpdate(BaseModel):
    is_enabled: bool | None = None
    ma_type: str | None = Field(default=None, pattern="^(EMA|SMA|WMA)$")
    ema_fast: int | None = Field(default=None, ge=1, le=200)
    ema_slow: int | None = Field(default=None, ge=2, le=400)
    sma_fast: int | None = Field(default=None, ge=1, le=200)
    sma_slow: int | None = Field(default=None, ge=2, le=400)
    wma_period: int | None = Field(default=None, ge=2, le=400)
    rsi_period: int | None = Field(default=None, ge=2, le=50)
    risk_pct: float | None = Field(default=None, ge=0.0001, le=0.02)
    min_model_score: float | None = Field(default=None, ge=0.0, le=1.0)
    max_spread_bps: float | None = Field(default=None, ge=1.0, le=50.0)


class RuntimeConfigResponse(BaseModel):
    symbols: list[str]
    paper_trading: bool
    trading_enabled: bool
    risk_per_trade_pct: float
    max_daily_loss_pct: float
    max_concurrent_positions: int


class RiskStatusResponse(BaseModel):
    trading_enabled: bool
    paper_trading: bool
    circuit_breaker_open: bool
    daily_realized_pnl: float
    daily_loss_limit_pct: float
    consecutive_losses: int
    open_positions: int
    max_concurrent_positions: int
