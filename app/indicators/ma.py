from __future__ import annotations

from collections.abc import Sequence

from app.indicators.base import Indicator


class SMA(Indicator):
    def compute(self, values: Sequence[float]) -> list[float | None]:
        result: list[float | None] = []
        for idx in range(len(values)):
            if idx + 1 < self.period:
                result.append(None)
            else:
                window = values[idx + 1 - self.period : idx + 1]
                result.append(sum(window) / self.period)
        return result


class EMA(Indicator):
    def compute(self, values: Sequence[float]) -> list[float | None]:
        result: list[float | None] = []
        multiplier = 2 / (self.period + 1)
        current = None
        for idx, value in enumerate(values):
            if idx + 1 < self.period:
                result.append(None)
                continue
            if current is None:
                current = sum(values[idx + 1 - self.period : idx + 1]) / self.period
            else:
                current = (value - current) * multiplier + current
            result.append(current)
        return result

    @staticmethod
    def crossover_up(fast_values: Sequence[float | None], slow_values: Sequence[float | None]) -> bool:
        if len(fast_values) < 2 or len(slow_values) < 2:
            return False
        prev_fast, current_fast = fast_values[-2], fast_values[-1]
        prev_slow, current_slow = slow_values[-2], slow_values[-1]
        return all(v is not None for v in [prev_fast, current_fast, prev_slow, current_slow]) and prev_fast <= prev_slow and current_fast > current_slow

    @staticmethod
    def crossover_down(fast_values: Sequence[float | None], slow_values: Sequence[float | None]) -> bool:
        if len(fast_values) < 2 or len(slow_values) < 2:
            return False
        prev_fast, current_fast = fast_values[-2], fast_values[-1]
        prev_slow, current_slow = slow_values[-2], slow_values[-1]
        return all(v is not None for v in [prev_fast, current_fast, prev_slow, current_slow]) and prev_fast >= prev_slow and current_fast < current_slow


class WMA(Indicator):
    def compute(self, values: Sequence[float]) -> list[float | None]:
        result: list[float | None] = []
        weights = list(range(1, self.period + 1))
        denominator = sum(weights)
        for idx in range(len(values)):
            if idx + 1 < self.period:
                result.append(None)
            else:
                window = values[idx + 1 - self.period : idx + 1]
                result.append(sum(weight * value for weight, value in zip(weights, window)) / denominator)
        return result
