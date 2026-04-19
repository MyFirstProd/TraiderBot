from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class Signal(TimestampMixin, Base):
    __tablename__ = "signals"

    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    should_trade: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rationale: Mapped[dict] = mapped_column(JSON, nullable=False)
    indicators_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
