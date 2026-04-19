from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.common import ORMModel


class TradeRead(ORMModel):
    id: int
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    opened_at: datetime
    closed_at: datetime
    reason: str
    explanation: dict[str, Any]
