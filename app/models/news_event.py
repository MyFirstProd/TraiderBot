from datetime import datetime

from sqlalchemy import DateTime, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class NewsEvent(TimestampMixin, Base):
    __tablename__ = "news_events"

    source: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    sentiment: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    relevance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    novelty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    entities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    symbol_relevance: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
