from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class StrategyConfig(TimestampMixin, Base):
    __tablename__ = "strategy_configs"

    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    market_mode: Mapped[str] = mapped_column(String(20), default="linear", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ma_type: Mapped[str] = mapped_column(String(10), default="EMA", nullable=False)
    ema_fast: Mapped[int] = mapped_column(Integer, default=9, nullable=False)
    ema_slow: Mapped[int] = mapped_column(Integer, default=21, nullable=False)
    sma_fast: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    sma_slow: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    wma_period: Mapped[int] = mapped_column(Integer, default=21, nullable=False)
    rsi_period: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    risk_pct: Mapped[float] = mapped_column(Float, default=0.003, nullable=False)
    min_model_score: Mapped[float] = mapped_column(Float, default=0.55, nullable=False)
    max_spread_bps: Mapped[float] = mapped_column(Float, default=8.0, nullable=False)
