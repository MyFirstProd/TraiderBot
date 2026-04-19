from __future__ import annotations

from collections.abc import Sequence

from app.indicators.base import Indicator


class ATR(Indicator):
    def compute(self, highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> list[float | None]:
        result: list[float | None] = [None]
        ranges: list[float] = []
        for idx in range(1, len(closes)):
            true_range = max(
                highs[idx] - lows[idx],
                abs(highs[idx] - closes[idx - 1]),
                abs(lows[idx] - closes[idx - 1]),
            )
            ranges.append(true_range)
            if idx < self.period:
                result.append(None)
            else:
                result.append(sum(ranges[-self.period :]) / self.period)
        return result

    def current(self, highs: Sequence[float], lows: Sequence[float], closes: Sequence[float]) -> float | None:
        values = self.compute(highs, lows, closes)
        return values[-1] if values else None


class SpreadFilter:
    def __init__(self, max_spread_pct: float) -> None:
        self.max_spread_pct = max_spread_pct

    @staticmethod
    def spread_pct(bid: float, ask: float) -> float:
        midpoint = (bid + ask) / 2
        return (ask - bid) / midpoint if midpoint else 0.0

    def is_acceptable(self, bid: float, ask: float) -> bool:
        return self.spread_pct(bid, ask) <= self.max_spread_pct


class VolatilityFilter:
    def __init__(self, min_atr_pct: float = 0.001, max_atr_pct: float = 0.018) -> None:
        self.min_atr_pct = min_atr_pct
        self.max_atr_pct = max_atr_pct

    def is_tradeable(self, atr_value: float, price: float) -> bool:
        if price <= 0:
            return False
        atr_pct = atr_value / price
        return self.min_atr_pct <= atr_pct <= self.max_atr_pct
