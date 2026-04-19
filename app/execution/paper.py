from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PaperPosition:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    stop_price: float
    take_price: float
    opened_at: datetime
    explanation: dict


@dataclass(slots=True)
class ClosedTrade:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    opened_at: datetime
    closed_at: datetime
    reason: str
    explanation: dict


class PaperExecutionEngine:
    def __init__(self) -> None:
        self.positions: dict[str, PaperPosition] = {}

    def open_position(self, position: PaperPosition) -> None:
        self.positions[position.symbol] = position

    def exposure(self) -> float:
        return sum(position.entry_price * position.quantity for position in self.positions.values())

    def check_exit(self, symbol: str, price: float, timestamp: datetime) -> ClosedTrade | None:
        position = self.positions.get(symbol)
        if position is None:
            return None
        if position.side == "long":
            if price <= position.stop_price:
                return self._close(position, position.stop_price, timestamp, "stop_loss")
            if price >= position.take_price:
                return self._close(position, position.take_price, timestamp, "take_profit")
        else:
            if price >= position.stop_price:
                return self._close(position, position.stop_price, timestamp, "stop_loss")
            if price <= position.take_price:
                return self._close(position, position.take_price, timestamp, "take_profit")
        return None

    def _close(self, position: PaperPosition, exit_price: float, timestamp: datetime, reason: str) -> ClosedTrade:
        self.positions.pop(position.symbol, None)
        multiplier = 1 if position.side == "long" else -1
        pnl = (exit_price - position.entry_price) * position.quantity * multiplier
        return ClosedTrade(
            symbol=position.symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=exit_price,
            pnl=pnl,
            opened_at=position.opened_at,
            closed_at=timestamp,
            reason=reason,
            explanation=position.explanation,
        )
