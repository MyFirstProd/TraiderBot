from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class MarketSnapshot(TimestampMixin, Base):
    __tablename__ = "market_snapshots"

    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    bid: Mapped[float] = mapped_column(Float, nullable=False)
    ask: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_bps: Mapped[float] = mapped_column(Float, nullable=False)
    orderbook_imbalance: Mapped[float] = mapped_column(Float, nullable=False)
    trade_imbalance: Mapped[float] = mapped_column(Float, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
