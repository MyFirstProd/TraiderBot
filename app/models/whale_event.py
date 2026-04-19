from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class WhaleEvent(TimestampMixin, Base):
    __tablename__ = "whale_events"

    asset: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    chain: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    usd_value: Mapped[float] = mapped_column(Float, nullable=False)
    from_type: Mapped[str] = mapped_column(String(50), nullable=False)
    to_type: Mapped[str] = mapped_column(String(50), nullable=False)
    exchange_related: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    significance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
