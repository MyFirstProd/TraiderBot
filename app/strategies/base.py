from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SignalDirection(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


@dataclass(slots=True)
class SignalResult:
    direction: SignalDirection
    score: float
    rationale: dict[str, Any]
    indicators_snapshot: dict[str, Any]
    confidence: float
    should_trade: bool


class BaseStrategy:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    async def generate_signal(self, market_data: dict, news_sentiment: float | None = None, whale_flow: float | None = None) -> SignalResult:
        raise NotImplementedError
