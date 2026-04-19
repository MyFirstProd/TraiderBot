from __future__ import annotations

from datetime import datetime
from typing import Any

from app.schemas.common import ORMModel


class SignalRead(ORMModel):
    id: int
    symbol: str
    observed_at: datetime
    direction: str
    score: float
    confidence: float
    should_trade: bool
    rationale: dict[str, Any]
    indicators_snapshot: dict[str, Any]
