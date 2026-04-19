from __future__ import annotations

from collections.abc import Sequence

from app.indicators.base import Indicator


class RSI(Indicator):
    def compute(self, values: Sequence[float]) -> list[float | None]:
        if len(values) < 2:
            return [None] * len(values)
        result: list[float | None] = [None]
        gains: list[float] = []
        losses: list[float] = []
        for idx in range(1, len(values)):
            delta = values[idx] - values[idx - 1]
            gains.append(max(delta, 0.0))
            losses.append(abs(min(delta, 0.0)))
            if idx < self.period:
                result.append(None)
                continue
            avg_gain = sum(gains[-self.period :]) / self.period
            avg_loss = sum(losses[-self.period :]) / self.period
            if avg_loss == 0:
                result.append(100.0)
                continue
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))
        return result

    @staticmethod
    def is_exiting_oversold(values: Sequence[float | None], threshold: float) -> bool:
        if len(values) < 2 or values[-1] is None or values[-2] is None:
            return False
        return values[-2] <= threshold < values[-1]

    @staticmethod
    def is_exiting_overbought(values: Sequence[float | None], threshold: float) -> bool:
        if len(values) < 2 or values[-1] is None or values[-2] is None:
            return False
        return values[-2] >= threshold > values[-1]
