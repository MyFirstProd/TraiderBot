from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin


class RiskEvent(TimestampMixin, Base):
    __tablename__ = "risk_events"

    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(20))
    details: Mapped[dict] = mapped_column(JSON, nullable=False)
