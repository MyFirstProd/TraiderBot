from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.common import ORMModel


class PositionRead(ORMModel):
    id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    stop_price: float
    take_price: float
    opened_at: datetime
    closed_at: datetime | None
    is_open: bool
    explanation: dict[str, Any]
