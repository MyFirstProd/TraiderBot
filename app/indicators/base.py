from __future__ import annotations

from collections.abc import Sequence


class Indicator:
    def __init__(self, period: int) -> None:
        self.period = period

    def _guard(self, values: Sequence[float]) -> bool:
        return len(values) >= self.period
